"""
Preparação dos dados para a análise espacial de internações pediátricas no Paraná.

Todas as manipulações feitas sobre os dados brutos estão concentradas aqui, para que
os scripts `achados.py` (tabelas) e `gerar_geopackage.py` (camadas para o QGIS)
partam exatamente da mesma base.

Cada função recebe uma lista `registro` e acrescenta a ela uma linha por manipulação
(etapa, descrição, linhas antes, linhas depois). Ao final, essa lista vira um
DataFrame que documenta, passo a passo, como chegamos a cada número.
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


DIR_PROJETO = Path(__file__).resolve().parent.parent
DIR_DATASETS = DIR_PROJETO / 'Datasets'
DIR_SAIDA = Path(__file__).resolve().parent / 'saida'

ARQ_SAUDE = DIR_DATASETS / 'SAUDE_FINAL.csv'
ARQ_MUNICIPIOS = DIR_DATASETS / 'ids_municipios.csv'
ARQ_CADUNICO = DIR_PROJETO / 'bd2_2556553.csv'
ARQ_CENSO = DIR_DATASETS / 'censo2022_pop_raca_idade_pr.csv'

# Período de análise: só 2024 e 2025 têm os 12 meses completos no SIH extraído
# (2022 tem 3 meses, 2023 tem 5 e 2026 tem 1).
ANOS_ANALISE = [2024, 2025]

# Pretos, pardos e indígenas (PPI), agrupamento usual em estudos de desigualdade racial.
RACAS_PPI = ['Preta', 'Parda', 'Indígena']


def registrar(registro, etapa, descricao, antes, depois):
    registro.append({
        'etapa': etapa,
        'descricao': descricao,
        'linhas_antes': antes,
        'linhas_depois': depois,
        'removidas': antes - depois if antes is not None and depois is not None else None,
    })


def distancia_haversine_km(lat1, lon1, lat2, lon2):
    """Distância em linha reta (grande círculo) entre dois pontos, em km."""
    raio_terra = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * raio_terra * np.arcsin(np.sqrt(a))


# ============================================================
# 1. MUNICÍPIOS (IBGE / Base dos Dados)
# ============================================================

def carregar_municipios(registro):
    """
    Tabela de municípios do Brasil inteiro (alguns hospitais estão fora do PR),
    com o centroide em colunas numéricas de latitude e longitude.
    """
    mun = pd.read_csv(ARQ_MUNICIPIOS, dtype=str)
    n0 = len(mun)

    mun = mun[['id_municipio', 'id_municipio_6', 'nome', 'sigla_uf',
               'id_regiao_saude', 'nome_regiao_saude', 'centroide']].dropna(subset=['centroide'])
    registrar(registro, 'municipios', 'Remove municípios sem centroide em ids_municipios.csv', n0, len(mun))

    # 'POINT(-49.27 -25.43)' -> lon = -49.27, lat = -25.43
    coords = mun['centroide'].str.extract(r'POINT\(([-\d.]+) ([-\d.]+)\)').astype(float)
    mun['lon'] = coords[0]
    mun['lat'] = coords[1]
    registrar(registro, 'municipios',
              'Extrai lon/lat do texto WKT da coluna centroide (ponto central do município)',
              len(mun), len(mun))
    return mun.drop(columns='centroide')


# ============================================================
# 2. INTERNAÇÕES PEDIÁTRICAS (SIH/SUS)
# ============================================================

def carregar_internacoes(registro, municipios):
    s = pd.read_csv(ARQ_SAUDE, dtype=str)
    n = len(s)
    registrar(registro, 'internacoes', 'Leitura de SAUDE_FINAL.csv (SIH/SUS, pacientes do PR com até 16 anos)', n, n)

    s['ano'] = s['ano'].astype(int)
    s['mes'] = s['mes'].astype(int)
    s['idade_paciente'] = s['idade_paciente'].astype(int)

    # 2.1 Uma linha por AIH. O mesmo id_aih aparece mais de uma vez quando a linha
    # está duplicada no arquivo ou quando há AIH de continuação (internação longa,
    # cobrada em meses seguintes). Mantemos o registro mais antigo (mês de entrada).
    antes = len(s)
    s = s.sort_values(['ano', 'mes']).drop_duplicates(subset='id_aih', keep='first')
    registrar(registro, 'internacoes',
              'Remove id_aih repetido (linhas duplicadas e AIHs de continuação), mantendo o mês mais antigo',
              antes, len(s))

    # 2.2 Recorte temporal: apenas anos com 12 meses de dados.
    antes = len(s)
    s = s[s['ano'].isin(ANOS_ANALISE)]
    registrar(registro, 'internacoes',
              f'Mantém apenas os anos {ANOS_ANALISE} (únicos com os 12 meses no arquivo)', antes, len(s))

    # 2.3 Junta coordenadas e região de saúde do município de residência (origem)
    #     e do município do hospital (destino). Chave: código IBGE de 6 dígitos.
    cols = ['id_municipio_6', 'id_municipio', 'nome', 'sigla_uf', 'id_regiao_saude',
            'nome_regiao_saude', 'lat', 'lon']
    origem = municipios[cols].add_suffix('_pac')
    destino = municipios[cols].add_suffix('_estab')

    antes = len(s)
    s = (s.merge(origem, left_on='id_municipio_paciente', right_on='id_municipio_6_pac', how='inner')
          .merge(destino, left_on='id_municipio_estabelecimento', right_on='id_municipio_6_estab', how='inner'))
    registrar(registro, 'internacoes',
              'Junta (inner join) centroide e região de saúde dos municípios do paciente e do hospital '
              'via id_municipio_6 (remove códigos sem correspondência)', antes, len(s))

    # 2.4 Variáveis derivadas de deslocamento.
    s['dist_km'] = distancia_haversine_km(s['lat_pac'], s['lon_pac'], s['lat_estab'], s['lon_estab'])
    s['fora_municipio'] = s['id_municipio_paciente'] != s['id_municipio_estabelecimento']
    s['fora_regiao_saude'] = s['id_regiao_saude_pac'] != s['id_regiao_saude_estab']
    s['fora_pr'] = s['sigla_uf_estab'] != 'PR'
    s['mais_100km'] = s['dist_km'] > 100
    registrar(registro, 'internacoes',
              'Cria dist_km (haversine entre centroides), fora_municipio, fora_regiao_saude, fora_pr e mais_100km. '
              'Obs.: quem é internado no próprio município tem dist_km = 0 por construção',
              len(s), len(s))

    # 2.5 Grupos de raça/cor.
    s['raca_grupo'] = np.select(
        [s['raca_cor_paciente'].isin(RACAS_PPI),
         s['raca_cor_paciente'] == 'Branca',
         s['raca_cor_paciente'] == 'Amarela'],
        ['PPI', 'Branca', 'Amarela'],
        default='Sem informação',
    )
    registrar(registro, 'internacoes',
              'Cria raca_grupo: PPI (preta + parda + indígena), Branca, Amarela, Sem informação',
              len(s), len(s))
    return s


# ============================================================
# 3. CADÚNICO / BOLSA FAMÍLIA (tabela bd2_2556553)
# ============================================================

def carregar_cadunico(registro, municipios):
    """Média mensal de 2024–2025 por município."""
    b = pd.read_csv(ARQ_CADUNICO)
    n = len(b)
    registrar(registro, 'cadunico', 'Leitura de bd2_2556553.csv (CadÚnico/PBF, município × mês)', n, n)

    b = b[b['Data'].str[-4:].astype(int).isin(ANOS_ANALISE)]
    registrar(registro, 'cadunico', f'Mantém apenas meses de {ANOS_ANALISE}', n, len(b))

    col_fem = [c for c in b.columns if c.startswith('Beneficiarias BF feminino')]
    col_mas = [c for c in b.columns if c.startswith('Beneficiarias BF masculino')]
    col_criancas = [c for c in col_fem + col_mas
                    if any(f in c for f in ['0 a 3', '4 a 6', '7 a 15'])]

    # min_count=1: se todas as faixas estão nulas no mês, o total fica nulo (e não zero),
    # preservando a regra do README de que nulo ≠ 0.
    b['bf_pessoas'] = b[col_fem + col_mas].sum(axis=1, min_count=1)
    b['bf_criancas_0_15'] = b[col_criancas].sum(axis=1, min_count=1)
    b['cad_total_raca'] = b[[c for c in b.columns if c.startswith('Beneficiarios CadUnico')]].sum(axis=1, min_count=1)
    b['cad_ppi'] = b[['Beneficiarios CadUnico pretos', 'Beneficiarios CadUnico pardos',
                      'Beneficiarios CadUnico indigenas']].sum(axis=1, min_count=1)
    registrar(registro, 'cadunico',
              'Soma faixas etárias (fem + masc) -> bf_pessoas; faixas 0–3, 4–6, 7–15 -> bf_criancas_0_15; '
              'pretos + pardos + indígenas -> cad_ppi; todas as categorias de raça -> cad_total_raca',
              len(b), len(b))

    agregacoes = {
        'bf_pessoas': 'mean',
        'bf_criancas_0_15': 'mean',
        'Pessoas beneficiarias BF em pobreza': 'mean',
        'cad_total_raca': 'mean',
        'cad_ppi': 'mean',
        'Beneficiarios CadUnico brancos': 'mean',
        'Beneficiarios CadUnico pretos': 'mean',
        'Beneficiarios CadUnico pardos': 'mean',
        'Beneficiarios CadUnico indigenas': 'mean',
        'Pessoas BF em situação de trabalho infantil': ['mean', 'count'],
    }
    antes = len(b)
    g = b.groupby('Municipio').agg(agregacoes)
    g.columns = ['bf_pessoas', 'bf_criancas_0_15', 'bf_pobreza', 'cad_total', 'cad_ppi',
                 'cad_branca', 'cad_preta', 'cad_parda', 'cad_indigena',
                 'trab_inf_pessoas', 'trab_inf_meses_com_dado']
    g = g.reset_index()
    registrar(registro, 'cadunico',
              'Agrupa por município: média mensal de cada contagem (meses nulos são ignorados na média); '
              'conta quantos meses têm dado de trabalho infantil', antes, len(g))

    # Nomes do CadÚnico estão em maiúsculas e com "DOESTE" sem apóstrofo (ver README).
    pr = municipios[municipios['sigla_uf'] == 'PR'][['id_municipio_6', 'nome']].copy()
    pr['Municipio'] = pr['nome'].str.upper().str.replace("D'OESTE", 'DOESTE', regex=False)
    antes = len(g)
    g = g.merge(pr[['id_municipio_6', 'Municipio']], on='Municipio', how='inner')
    registrar(registro, 'cadunico',
              'Converte nome do município em código IBGE (nome em maiúsculas, D\'OESTE -> DOESTE)', antes, len(g))
    return g.drop(columns='Municipio')


# ============================================================
# 4. POPULAÇÃO (Censo 2022, SIDRA/IBGE) — denominadores
# ============================================================

def _baixar_sidra(url, destino):
    with urllib.request.urlopen(url, timeout=180) as r:
        dados = json.load(r)
    df = pd.DataFrame(dados[1:])  # a primeira linha do SIDRA é o cabeçalho descritivo
    df.to_csv(destino, index=False)
    return df


def carregar_populacao(registro):
    """
    Tabela 9606 do SIDRA: população residente por cor ou raça e idade, por município do PR.
    Baixamos o total de idades e as faixas 0–4, 5–9, 10–14, 15 e 16 anos (a base do SIH
    vai de 0 a 16 anos). O arquivo fica em Datasets/ depois do primeiro download.
    """
    if ARQ_CENSO.exists():
        censo = pd.read_csv(ARQ_CENSO, dtype=str)
    else:
        censo = _baixar_sidra(
            'https://apisidra.ibge.gov.br/values/t/9606/n6/in%20n3%2041/v/93/p/2022'
            '/c86/all/c2/6794/c287/100362,93070,93084,93085,6572,6573',
            ARQ_CENSO)

    # Valores suprimidos pelo IBGE ('-', 'X') viram nulo.
    censo['V'] = pd.to_numeric(censo['V'], errors='coerce')
    faixas_0_15 = ['0 a 4 anos', '5 a 9 anos', '10 a 14 anos', '15 anos']
    censo['faixa'] = np.select(
        [censo['D6N'] == 'Total', censo['D6N'].isin(faixas_0_15), censo['D6N'] == '16 anos'],
        ['total', '0_15', '16'],
        default='outra',
    )
    t = censo.pivot_table(index='D1C', columns=['D4N', 'faixa'], values='V', aggfunc='sum')

    def soma(raca, faixas):
        return sum(t[(r, f)] for r in raca for f in faixas)

    ppi = ['Preta', 'Parda', 'Indígena']
    pop = pd.DataFrame({
        'pop_total': soma(['Total'], ['total']),
        'pop_0_15': soma(['Total'], ['0_15']),
        'pop_0_16': soma(['Total'], ['0_15', '16']),
        'censo_ppi': soma(ppi, ['total']),
        'censo_branca': soma(['Branca'], ['total']),
        'censo_ppi_0_16': soma(ppi, ['0_15', '16']),
        'censo_branca_0_16': soma(['Branca'], ['0_15', '16']),
    })
    pop = pop.reset_index().rename(columns={'D1C': 'id_municipio'})
    registrar(registro, 'populacao',
              'Censo 2022 (SIDRA 9606, raça × idade): pop_total; pop_0_15 = 0–4 + 5–9 + 10–14 + 15 anos; '
              'pop_0_16 = pop_0_15 + 16 anos; PPI = preta + parda + indígena, para todas as idades e para 0–16 anos',
              None, len(pop))
    return pop


# ============================================================
# 5. TABELA MUNICIPAL CONSOLIDADA
# ============================================================

def indicadores_municipais(registro, internacoes, cadunico, populacao, municipios):
    """Uma linha por município do PR (residência do paciente) com todos os indicadores."""
    pr = municipios[municipios['sigla_uf'] == 'PR'][
        ['id_municipio', 'id_municipio_6', 'nome', 'id_regiao_saude', 'nome_regiao_saude', 'lat', 'lon']]

    s = internacoes
    s_ppi = s[s['raca_grupo'] == 'PPI']
    s_branca = s[s['raca_grupo'] == 'Branca']

    g = s.groupby('id_municipio_paciente').agg(
        internacoes=('id_aih', 'size'),
        pct_fora_municipio=('fora_municipio', 'mean'),
        pct_fora_regiao=('fora_regiao_saude', 'mean'),
        pct_mais_100km=('mais_100km', 'mean'),
        dist_media_km=('dist_km', 'mean'),
        dist_mediana_km=('dist_km', 'median'),
        int_ppi=('raca_grupo', lambda r: (r == 'PPI').sum()),
        int_branca=('raca_grupo', lambda r: (r == 'Branca').sum()),
        int_sem_info_raca=('raca_grupo', lambda r: (r == 'Sem informação').sum()),
    )
    g['dist_media_km_ppi'] = s_ppi.groupby('id_municipio_paciente')['dist_km'].mean()
    g['dist_media_km_branca'] = s_branca.groupby('id_municipio_paciente')['dist_km'].mean()
    g['pct_fora_mun_ppi'] = s_ppi.groupby('id_municipio_paciente')['fora_municipio'].mean()
    g['pct_fora_mun_branca'] = s_branca.groupby('id_municipio_paciente')['fora_municipio'].mean()
    g = g.reset_index().rename(columns={'id_municipio_paciente': 'id_municipio_6'})

    m = (pr.merge(g, on='id_municipio_6', how='left')
           .merge(cadunico, on='id_municipio_6', how='left')
           .merge(populacao, on='id_municipio', how='left'))
    m['internacoes'] = m['internacoes'].fillna(0)

    n_anos = len(ANOS_ANALISE)
    m['taxa_int_1000_criancas_ano'] = m['internacoes'] / n_anos / m['pop_0_16'] * 1000
    m['pct_pop_bf'] = m['bf_pessoas'] / m['pop_total']
    m['pct_criancas_bf'] = m['bf_criancas_0_15'] / m['pop_0_15']
    m['pct_pop_bf_pobreza'] = m['bf_pobreza'] / m['pop_total']
    m['trab_inf_10mil_criancas'] = m['trab_inf_pessoas'] / m['pop_0_15'] * 10000

    # Raça/cor: mesma proporção (PPI) medida em três populações diferentes.
    m['pct_ppi_censo'] = m['censo_ppi'] / m['pop_total']
    m['pct_ppi_censo_0_16'] = m['censo_ppi_0_16'] / m['pop_0_16']
    m['pct_ppi_cadunico'] = m['cad_ppi'] / m['cad_total']
    m['pct_ppi_internacoes'] = m['int_ppi'] / (m['internacoes'] - m['int_sem_info_raca'])
    m['pct_sem_info_raca_int'] = m['int_sem_info_raca'] / m['internacoes']
    # Razão > 1: PPI sobrerrepresentados em relação à população geral do município.
    m['razao_ppi_cadunico_censo'] = m['pct_ppi_cadunico'] / m['pct_ppi_censo']
    # Nas internações a comparação justa é com a população de 0–16 anos, não com a total.
    m['razao_ppi_internacoes_censo'] = m['pct_ppi_internacoes'] / m['pct_ppi_censo_0_16']
    # Taxa de internação específica por raça (por 1.000 crianças de 0–16 anos do mesmo grupo, por ano).
    m['taxa_int_ppi'] = m['int_ppi'] / n_anos / m['censo_ppi_0_16'] * 1000
    m['taxa_int_branca'] = m['int_branca'] / n_anos / m['censo_branca_0_16'] * 1000
    m['razao_taxa_ppi_branca'] = m['taxa_int_ppi'] / m['taxa_int_branca']

    registrar(registro, 'municipal',
              'Agrega internações por município de residência e junta CadÚnico (média 2024–2025) e Censo 2022. '
              f'Taxa de internação = internações / {n_anos} anos / pop_0_16 × 1000. '
              'pct_ppi_internacoes usa como denominador só internações com raça informada',
              len(s), len(m))
    return m


def preparar_tudo():
    registro = []
    municipios = carregar_municipios(registro)
    internacoes = carregar_internacoes(registro, municipios)
    cadunico = carregar_cadunico(registro, municipios)
    populacao = carregar_populacao(registro)
    municipal = indicadores_municipais(registro, internacoes, cadunico, populacao, municipios)
    return {
        'municipios': municipios,
        'internacoes': internacoes,
        'municipal': municipal,
        'registro': pd.DataFrame(registro),
    }
