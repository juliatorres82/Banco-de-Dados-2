"""
Acessibilidade hospitalar x vulnerabilidade social, executada no PostGIS.

Executar a partir da raiz do projeto (precisa do túnel SSH e do .env, como os demais scripts):
    python gis/acessibilidade_postgis.py

1. Roda os SQLs de gis/sql/ no banco `postgiscwb` (conexão SOMENTE LEITURA).
2. Salva os resultados em gis/saida/ (CSV) e as camadas em
   gis/saida/acessibilidade_hospitalar_pr.gpkg (EPSG:29192) para o QGIS.
3. Cruza o resultado com o SIH (dados locais, fora do banco) e calcula as estatísticas.

As figuras são geradas depois, sem acesso ao banco, por gis/figuras_acessibilidade.py.
"""

import os
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from scipy.stats import spearmanr
from dotenv import load_dotenv
from shapely import wkb
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder

DIR_PROJETO = Path(__file__).resolve().parent.parent
DIR_SQL = Path(__file__).resolve().parent / 'sql'
DIR_SAIDA = Path(__file__).resolve().parent / 'saida'
ARQ_GPKG = DIR_SAIDA / 'acessibilidade_hospitalar_pr.gpkg'
CRS = 'EPSG:29192'  # SAD 69 / UTM 22S (ver cabeçalho de sql/02_acessibilidade_municipal.sql)
MARCADOR = '-- @@FINAL@@'

pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 30)


def conectar():
    load_dotenv(DIR_PROJETO / '.env')
    g = os.getenv
    tunel = SSHTunnelForwarder(
        (g('HOST_SSH'), 22), ssh_username=g('USER_SSH'), ssh_pkey=g('KEY_SSH'),
        ssh_password=g('PASSWORD_SSH'), ssh_private_key_password=g('PASSWORD_SSH'),
        remote_bind_address=(g('DB_HOST'), int(g('DB_PORT'))), allow_agent=False)
    tunel.start()
    engine = create_engine(
        f"postgresql://{g('DB_USER')}:{g('DB_PASSWORD')}@127.0.0.1:{tunel.local_bind_port}/{g('DB_NAME')}",
        connect_args={'options': '-c default_transaction_read_only=on'})
    return tunel, engine


def sql(arquivo, continuacao=False):
    """Lê um SQL. Continuações usam os CTEs da consulta 02 (tudo antes do marcador)."""
    corpo = (DIR_SQL / arquivo).read_text()
    if continuacao:
        prefixo = (DIR_SQL / '02_acessibilidade_municipal.sql').read_text().split(MARCADOR)[0]
        return prefixo + corpo
    return corpo


def consulta(con, texto, geometrias=()):
    t0 = time.time()
    df = pd.read_sql_query(text(texto), con)
    for col in geometrias:
        df[col] = df[col].map(lambda h: wkb.loads(h, hex=True))
    print(f'  {len(df):4d} linhas em {time.time() - t0:.1f}s')
    return df


def gdf(df, geom):
    return gpd.GeoDataFrame(df.drop(columns=[c for c in ('geom', 'sede', 'linha') if c in df.columns and c != geom]),
                            geometry=geom, crs=CRS)


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    tunel, engine = conectar()
    try:
        with engine.connect() as con:
            print('01 diagnóstico de qualidade')
            funil = consulta(con, sql('01_qualidade.sql').split('-- @@')[0])
            srid = consulta(con, sql('01_qualidade.sql').split('-- @@')[1])
            nomes = consulta(con, sql('01_qualidade.sql').split('-- @@')[2])
            print('02 consulta principal (acessibilidade x CadÚnico)')
            principal = consulta(con, sql('02_acessibilidade_municipal.sql'), geometrias=('geom', 'sede', 'linha'))
            print('03 hospitais e junção espacial')
            hospitais = consulta(con, sql('03_hospitais.sql', True), geometrias=('geom',))
            print('04 resumo por grupo')
            grupos = consulta(con, sql('04_resumo_grupos.sql', True))
            print('05 correlações (Pearson)')
            pearson = consulta(con, sql('05_correlacoes.sql', True))
            print('06 cobertura de 30 km')
            cobertura = consulta(con, sql('06_cobertura.sql', True), geometrias=('geom',))
    finally:
        engine.dispose()
        tunel.stop()

    # --- camadas para o QGIS -------------------------------------------------
    municipios = gdf(principal, 'geom')
    ligacoes = gdf(principal[principal['n_hosp_municipio'] == 0].drop(columns=['geom']), 'linha')
    pontos = gdf(hospitais, 'geom')
    if ARQ_GPKG.exists():
        ARQ_GPKG.unlink()
    municipios.to_file(ARQ_GPKG, layer='municipios_acesso', driver='GPKG')
    ligacoes.to_file(ARQ_GPKG, layer='ligacao_hospital_proximo', driver='GPKG')
    pontos.to_file(ARQ_GPKG, layer='hospitais', driver='GPKG')
    gpd.GeoDataFrame(cobertura[['area_km2']], geometry=cobertura['geom'], crs=CRS).to_file(
        ARQ_GPKG, layer='cobertura_30km', driver='GPKG')

    # --- tabelas (sem geometria) ---------------------------------------------
    tabela = principal.drop(columns=['geom', 'sede', 'linha'])
    tabela.to_csv(DIR_SAIDA / 'acess_01_municipios.csv', index=False)
    funil.to_csv(DIR_SAIDA / 'acess_00_funil_hospitais.csv', index=False)
    grupos.to_csv(DIR_SAIDA / 'acess_02_grupos_sql.csv', index=False)
    pearson.to_csv(DIR_SAIDA / 'acess_03_pearson_sql.csv', index=False)
    hospitais.drop(columns=['geom']).to_csv(DIR_SAIDA / 'acess_04_hospitais.csv', index=False)

    # --- cruzamento com o SIH (dados locais) e estatísticas --------------------
    sih = pd.read_csv(DIR_SAIDA / 'indicadores_municipais.csv')
    sih['codibge'] = sih['id_municipio'].astype(int)
    cols = ['codibge', 'internacoes', 'pct_fora_municipio', 'pct_fora_regiao', 'pct_mais_100km',
            'dist_media_km', 'taxa_int_1000_criancas_ano', 'razao_taxa_ppi_branca', 'int_ppi', 'int_branca']
    juntos = tabela.merge(sih[cols], on='codibge', how='left')
    juntos['tem_hospital'] = juntos['n_hosp_municipio'] > 0
    juntos['fora_n'] = juntos['pct_fora_municipio'] * juntos['internacoes']
    juntos.to_csv(DIR_SAIDA / 'acess_05_municipios_sih.csv', index=False)

    # Saída do município no SIH, por presença de hospital (soma / soma, não média de proporções).
    sih_grupo = juntos.groupby('tem_hospital').agg(
        municipios=('codibge', 'size'), internacoes=('internacoes', 'sum'), fora=('fora_n', 'sum'),
        mediana_pct_fora_municipio=('pct_fora_municipio', 'median'),
        mun_100_por_cento=('pct_fora_municipio', lambda s: (s >= 0.999).sum())).reset_index()
    sih_grupo['pct_internacoes_fora'] = sih_grupo['fora'] / sih_grupo['internacoes']
    sih_grupo.to_csv(DIR_SAIDA / 'acess_06_sih_por_grupo.csv', index=False)

    # Spearman com p-valor. CadÚnico: todos os 399 municípios; SIH: só os com >= 30 internações.
    base = juntos[juntos['internacoes'] >= 30]
    x = ['dist_hosp_km', 'pct_area_ate_30km', 'n_hosp_30km', 'dist_hosp_infantil_km']
    y_cad = ['pct_bf_inscritos', 'pct_ppi_cadunico', 'pct_bf_pobreza']
    y_sih = ['pct_fora_municipio', 'taxa_int_1000_criancas_ano']
    linhas = []
    for fonte, ys in ((juntos, y_cad), (base, y_sih)):
        for u in x:
            for v in ys:
                r, p = spearmanr(fonte[u], fonte[v], nan_policy='omit')
                linhas.append({'x': u, 'y': v, 'n': int(fonte[[u, v]].dropna().shape[0]), 'rho': round(r, 3), 'p': p})
    sp = pd.DataFrame(linhas)
    sp.to_csv(DIR_SAIDA / 'acess_07_spearman.csv', index=False)

    print('\n=== Funil de hospitais'); print(funil.to_string(index=False))
    print('\n=== SRID declarado x coordenadas'); print(srid.to_string(index=False))
    print('\n=== Nomes (malha x CadÚnico)'); print(nomes.to_string(index=False))
    print('\n=== Resumo por grupo (SQL)'); print(grupos.to_string(index=False))
    print('\n=== Pearson (SQL)'); print(pearson.to_string(index=False))
    print('\n=== SIH por presença de hospital'); print(sih_grupo.round(3).to_string(index=False))
    print('\n=== Spearman (CadÚnico: 399 municípios; SIH: >= 30 internações)')
    print(sp.assign(p=sp['p'].map(lambda v: f'{v:.1e}')).to_string(index=False))
    print(f'\nCamadas em {ARQ_GPKG}')


if __name__ == '__main__':
    main()
