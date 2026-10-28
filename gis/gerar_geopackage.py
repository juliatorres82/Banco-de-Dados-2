"""
Gera o GeoPackage com as camadas para análise no QGIS.

Executar a partir da raiz do projeto:
    python gis/gerar_geopackage.py

Saída: gis/saida/internacoes_pediatricas_pr.gpkg, no SIRGAS 2000 / UTM 22S (EPSG:31982),
para que as medidas feitas no QGIS saiam em metros. Camadas:

    municipios          polígonos dos 399 municípios com todos os indicadores (deslocamento,
                        Bolsa Família, trabalho infantil, raça/cor)
    regioes_saude       polígonos das 22 Regiões de Saúde (dissolve dos municípios), com totais
    polos_hospitalares  pontos (sede municipal) dos municípios que internaram crianças do PR
    fluxos_od           linhas origem -> destino (residência -> hospital), só entre municípios diferentes
    fluxo_principal     para cada município, a linha até o destino que mais recebe suas crianças
                        fora dele (base para regionalização à Nystuen–Dacey)

As manipulações de dados estão em preparacao.py; aqui só há agregação e geometria.
"""

import geobr
import geopandas as gpd
from shapely.geometry import LineString

from preparacao import DIR_SAIDA, preparar_tudo

CRS_GEOGRAFICO = 'EPSG:4674'   # SIRGAS 2000 (lat/lon) — CRS dos centroides do IBGE
CRS_METRICO = 'EPSG:31982'     # SIRGAS 2000 / UTM 22S — cobre o Paraná
ARQ_GPKG = DIR_SAIDA / 'internacoes_pediatricas_pr.gpkg'


# ============================================================
# 1. CAMADA DE MUNICÍPIOS (polígonos)
# ============================================================

def camada_municipios(municipal):
    malha = geobr.read_municipality(code_muni='PR', year=2022)
    malha['id_municipio'] = malha['code_muni'].astype(int).astype(str)
    malha = malha[['id_municipio', 'geometry']].to_crs(CRS_METRICO)

    gdf = malha.merge(municipal.drop(columns=['lat', 'lon']), on='id_municipio', how='left')
    faltando = gdf['nome'].isna().sum()
    if faltando:
        print(f'Atenção: {faltando} polígonos sem indicadores (código IBGE não encontrado)')
    return gdf


def camada_regioes_saude(municipios_gdf, internacoes):
    somas = ['internacoes', 'pop_total', 'pop_0_16', 'bf_pessoas', 'bf_criancas_0_15', 'pop_0_15',
             'censo_ppi', 'censo_ppi_0_16', 'cad_ppi', 'cad_total', 'int_ppi', 'int_branca']
    reg = municipios_gdf.dissolve(by=['id_regiao_saude', 'nome_regiao_saude'], aggfunc={c: 'sum' for c in somas})
    reg = reg.reset_index()

    s = internacoes.groupby('id_regiao_saude_pac').agg(
        pct_fora_municipio=('fora_municipio', 'mean'),
        pct_fora_regiao=('fora_regiao_saude', 'mean'),
        dist_media_km=('dist_km', 'mean'),
    ).reset_index().rename(columns={'id_regiao_saude_pac': 'id_regiao_saude'})
    reg = reg.merge(s, on='id_regiao_saude', how='left')

    reg['taxa_int_1000_criancas_ano'] = reg['internacoes'] / internacoes['ano'].nunique() / reg['pop_0_16'] * 1000
    reg['pct_criancas_bf'] = reg['bf_criancas_0_15'] / reg['pop_0_15']
    reg['pct_ppi_censo_0_16'] = reg['censo_ppi_0_16'] / reg['pop_0_16']
    reg['pct_ppi_cadunico'] = reg['cad_ppi'] / reg['cad_total']
    reg['pct_ppi_internacoes'] = reg['int_ppi'] / (reg['int_ppi'] + reg['int_branca'])
    return reg


# ============================================================
# 2. PONTOS: POLOS HOSPITALARES
# ============================================================

def camada_polos(internacoes):
    s = internacoes
    polos = (s.groupby(['id_municipio_estabelecimento', 'nome_estab', 'sigla_uf_estab',
                        'nome_regiao_saude_estab', 'lat_estab', 'lon_estab'])
               .agg(internacoes_recebidas=('id_aih', 'size'),
                    vindas_de_fora=('fora_municipio', 'sum'),
                    vindas_outra_regiao=('fora_regiao_saude', 'sum'),
                    municipios_de_origem=('id_municipio_paciente', 'nunique'),
                    dist_media_origem_km=('dist_km', 'mean'),
                    recebidas_ppi=('raca_grupo', lambda r: (r == 'PPI').sum()),
                    recebidas_branca=('raca_grupo', lambda r: (r == 'Branca').sum()))
               .reset_index())
    polos['pct_vindas_de_fora'] = polos['vindas_de_fora'] / polos['internacoes_recebidas']
    gdf = gpd.GeoDataFrame(polos, geometry=gpd.points_from_xy(polos['lon_estab'], polos['lat_estab']),
                           crs=CRS_GEOGRAFICO)
    return gdf.drop(columns=['lat_estab', 'lon_estab']).to_crs(CRS_METRICO)


# ============================================================
# 3. LINHAS: FLUXOS ORIGEM -> DESTINO
# ============================================================

def camada_fluxos(internacoes):
    s = internacoes[internacoes['fora_municipio']]
    chaves = ['id_municipio_paciente', 'nome_pac', 'nome_regiao_saude_pac', 'lat_pac', 'lon_pac',
              'id_municipio_estabelecimento', 'nome_estab', 'sigla_uf_estab', 'nome_regiao_saude_estab',
              'lat_estab', 'lon_estab', 'dist_km', 'fora_regiao_saude']
    f = (s.groupby(chaves)
           .agg(internacoes=('id_aih', 'size'),
                internacoes_ppi=('raca_grupo', lambda r: (r == 'PPI').sum()),
                internacoes_branca=('raca_grupo', lambda r: (r == 'Branca').sum()),
                idade_media=('idade_paciente', 'mean'))
           .reset_index())

    # Peso do fluxo dentro da origem: que fração das crianças que saem do município vai para este destino.
    f['pct_saidas_da_origem'] = f['internacoes'] / f.groupby('id_municipio_paciente')['internacoes'].transform('sum')

    geometria = [LineString([(a, b), (c, d)])
                 for a, b, c, d in zip(f['lon_pac'], f['lat_pac'], f['lon_estab'], f['lat_estab'])]
    gdf = gpd.GeoDataFrame(f.drop(columns=['lat_pac', 'lon_pac', 'lat_estab', 'lon_estab']),
                           geometry=geometria, crs=CRS_GEOGRAFICO).to_crs(CRS_METRICO)

    # Fluxo dominante de cada origem: ordena por volume e fica com o primeiro.
    principal = (gdf.sort_values('internacoes', ascending=False)
                    .drop_duplicates(subset='id_municipio_paciente'))
    # Ordem crescente faz os fluxos maiores serem desenhados por cima no QGIS.
    return gdf.sort_values('internacoes'), principal.sort_values('internacoes')


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    dados = preparar_tudo()
    internacoes = dados['internacoes']

    municipios = camada_municipios(dados['municipal'])
    camadas = {
        'municipios': municipios,
        'regioes_saude': camada_regioes_saude(municipios, internacoes),
        'polos_hospitalares': camada_polos(internacoes),
    }
    camadas['fluxos_od'], camadas['fluxo_principal'] = camada_fluxos(internacoes)

    if ARQ_GPKG.exists():
        ARQ_GPKG.unlink()
    for nome, gdf in camadas.items():
        gdf.to_file(ARQ_GPKG, layer=nome, driver='GPKG')
        print(f'{nome:20s} {len(gdf):6d} feições')

    dados['registro'].to_csv(DIR_SAIDA / '00_registro_manipulacoes.csv', index=False)
    print(f'\nGeoPackage salvo em {ARQ_GPKG}')


if __name__ == '__main__':
    main()
