"""

ACHADOS SOBRE DESLOCAMENTO PARA INTERNACAO PEDIATRICA E RAÇA/COR NO PR:

Imprime e salva em gis/saida/:
    00_registro_manipulacoes.csv  -> cada transformação aplicada aos dados, com contagem de linhas
    01_achados_gerais.csv         -> tabela-resumo do deslocamento
    02_polos_receptores.csv       -> municípios que mais recebem internações
    03_municipios_exportadores.csv-> municípios que mais enviam pacientes para fora
    04_raca_cor_deslocamento.csv  -> deslocamento por grupo de raça/cor
    05_raca_cor_representacao.csv -> % PPI no censo, no CadÚnico e nas internações
    05b_taxa_internacao_raca.csv  -> taxa de internação por 1.000 crianças, PPI x brancas
    06_correlacoes.csv            -> correlação (spearman) entre indicadores municipais
"""

import pandas as pd

from preparacao import DIR_SAIDA, preparar_tudo

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_colwidth', 120)


def mostrar(titulo, df, arquivo):
    print(f'\n{"=" * 100}\n{titulo}\n{"=" * 100}')
    print(df.to_string(index=False))
    df.to_csv(DIR_SAIDA / arquivo, index=False)


def main():
    DIR_SAIDA.mkdir(exist_ok=True)
    dados = preparar_tudo()
    s = dados['internacoes']
    m = dados['municipal']

    # ============================================================
    # 0. REGISTRO DAS MANIPULAÇÕES
    # ============================================================
    mostrar('0. Registro de manipulações (na ordem em que foram aplicadas)',
            dados['registro'], '00_registro_manipulacoes.csv')

    # ============================================================
    # 1. ACHADOS GERAIS DE DESLOCAMENTO
    # ============================================================
    # Cada linha diz qual cálculo gerou o número, para poder citá-lo no artigo.
    achados = pd.DataFrame([
        ('Internações analisadas (AIHs únicas, 2024–2025)', len(s),
         'contagem de linhas após as etapas de limpeza'),
        ('% internadas fora do município de residência', s['fora_municipio'].mean() * 100,
         'média de (id_municipio_paciente != id_municipio_estabelecimento)'),
        ('% internadas fora da própria Região de Saúde', s['fora_regiao_saude'].mean() * 100,
         'média de (id_regiao_saude do paciente != do hospital)'),
        ('% internadas fora do Paraná', s['fora_pr'].mean() * 100,
         'média de (UF do hospital != PR)'),
        ('% internadas a mais de 100 km (linha reta)', s['mais_100km'].mean() * 100,
         'média de (dist_km > 100)'),
        ('Distância média (km), todas as internações', s['dist_km'].mean(),
         'média de dist_km; inclui zeros de quem foi internado no próprio município'),
        ('Distância média (km), só quem saiu do município', s.loc[s['fora_municipio'], 'dist_km'].mean(),
         'média de dist_km onde fora_municipio = True'),
        ('Distância mediana (km), só quem saiu do município', s.loc[s['fora_municipio'], 'dist_km'].median(),
         'mediana de dist_km onde fora_municipio = True'),
        ('Municípios de residência com internação', s['id_municipio_paciente'].nunique(),
         'nunique(id_municipio_paciente)'),
        ('Municípios com hospital que recebeu criança do PR', s['id_municipio_estabelecimento'].nunique(),
         'nunique(id_municipio_estabelecimento)'),
        ('Municípios do PR com hospital que internou criança', s.loc[~s['fora_pr'], 'id_municipio_estabelecimento'].nunique(),
         'nunique(id_municipio_estabelecimento) onde UF = PR'),
    ], columns=['indicador', 'valor', 'como_foi_calculado'])
    achados['valor'] = achados['valor'].round(2)
    mostrar('1. Achados gerais de deslocamento', achados, '01_achados_gerais.csv')

    # ============================================================
    # 2. POLOS RECEPTORES
    # ============================================================
    polos = (s.groupby(['id_municipio_estabelecimento', 'nome_estab', 'sigla_uf_estab'])
               .agg(internacoes_recebidas=('id_aih', 'size'),
                    vindas_de_fora=('fora_municipio', 'sum'),
                    municipios_de_origem=('id_municipio_paciente', 'nunique'),
                    dist_media_origem_km=('dist_km', 'mean'))
               .reset_index()
               .sort_values('internacoes_recebidas', ascending=False))
    polos['pct_vindas_de_fora'] = polos['vindas_de_fora'] / polos['internacoes_recebidas'] * 100
    polos['pct_do_total_pr'] = polos['internacoes_recebidas'] / len(s) * 100
    mostrar('2. Polos receptores (groupby município do hospital; top 15)',
            polos.head(15).round(1), '02_polos_receptores.csv')

    # ============================================================
    # 3. MUNICÍPIOS EXPORTADORES
    # ============================================================
    export = m[m['internacoes'] > 0][
        ['nome', 'nome_regiao_saude', 'internacoes', 'pct_fora_municipio', 'dist_media_km',
         'taxa_int_1000_criancas_ano', 'pct_criancas_bf']].copy()
    export['enviadas_para_fora'] = (export['internacoes'] * export['pct_fora_municipio']).round()
    export = export.sort_values('enviadas_para_fora', ascending=False)
    for c in ['pct_fora_municipio', 'pct_criancas_bf']:
        export[c] = export[c] * 100
    mostrar('3. Municípios que mais enviam crianças para internação em outro município (top 15)',
            export.head(15).round(1), '03_municipios_exportadores.csv')

    # ============================================================
    # 4. RAÇA/COR x DESLOCAMENTO
    # ============================================================
    def resumo_por(coluna):
        r = (s.groupby(coluna)
               .agg(internacoes=('id_aih', 'size'),
                    pct_fora_municipio=('fora_municipio', 'mean'),
                    pct_fora_regiao=('fora_regiao_saude', 'mean'),
                    pct_mais_100km=('mais_100km', 'mean'),
                    dist_media_km=('dist_km', 'mean'),
                    idade_media=('idade_paciente', 'mean'))
               .reset_index())
        r['pct_das_internacoes'] = r['internacoes'] / len(s)
        for c in ['pct_fora_municipio', 'pct_fora_regiao', 'pct_mais_100km', 'pct_das_internacoes']:
            r[c] = r[c] * 100
        return r.round(2)

    raca = pd.concat([
        resumo_por('raca_cor_paciente').rename(columns={'raca_cor_paciente': 'categoria'}).assign(nivel='raça/cor (SIH)'),
        resumo_por('raca_grupo').rename(columns={'raca_grupo': 'categoria'}).assign(nivel='grupo'),
    ])
    mostrar('4. Deslocamento por raça/cor (groupby raca_cor_paciente e raca_grupo)',
            raca, '04_raca_cor_deslocamento.csv')

    # Controle: quem está em municípios-polo quase não se desloca. Se um grupo racial
    # se concentra em municípios-polo, a média dele cai sem que o acesso seja "melhor".
    # Por isso comparamos também dentro do mesmo município (diferença PPI − Branca).
    pares = m.dropna(subset=['dist_media_km_ppi', 'dist_media_km_branca'])
    pares = pares[(pares['int_ppi'] >= 20) & (pares['int_branca'] >= 20)]
    print(f'\nDentro do mesmo município (n = {len(pares)} municípios com ≥ 20 internações PPI e ≥ 20 brancas):')
    print(f'  diferença mediana de distância média (PPI − Branca): '
          f'{(pares["dist_media_km_ppi"] - pares["dist_media_km_branca"]).median():.2f} km')
    print(f'  diferença mediana de % fora do município (PPI − Branca): '
          f'{((pares["pct_fora_mun_ppi"] - pares["pct_fora_mun_branca"]) * 100).median():.2f} p.p.')

    # ============================================================
    # 5. RAÇA/COR: REPRESENTAÇÃO EM CADA BASE
    # ============================================================
    # Totais estaduais: soma dos numeradores / soma dos denominadores
    # (não é a média das proporções municipais, que daria o mesmo peso a todo município).
    int_com_raca = s[s['raca_grupo'] != 'Sem informação']
    rep = pd.DataFrame([
        ('Censo 2022, população total', m['censo_ppi'].sum() / m['pop_total'].sum(),
         'censo_ppi / pop_total'),
        ('Censo 2022, crianças de 0–16 anos', m['censo_ppi_0_16'].sum() / m['pop_0_16'].sum(),
         'censo_ppi_0_16 / pop_0_16'),
        ('CadÚnico, média mensal 2024–2025 (todas as idades)', m['cad_ppi'].sum() / m['cad_total'].sum(),
         'cad_ppi / cad_total (cad_total inclui "sem informação")'),
        ('Internações pediátricas SIH 2024–2025', (int_com_raca['raca_grupo'] == 'PPI').mean(),
         'internações PPI / internações com raça informada'),
    ], columns=['base', 'pct_ppi', 'como_foi_calculado'])
    rep['pct_ppi'] = (rep['pct_ppi'] * 100).round(2)
    print(f'\nInternações sem raça informada em 2024–2025: {(s["raca_grupo"] == "Sem informação").sum()}')
    mostrar('5a. % de pretos, pardos e indígenas (PPI) em cada base, Paraná', rep, '05_raca_cor_representacao.csv')

    n_anos = s['ano'].nunique()
    taxas = pd.DataFrame([
        ('PPI', (s['raca_grupo'] == 'PPI').sum(), m['censo_ppi_0_16'].sum()),
        ('Branca', (s['raca_grupo'] == 'Branca').sum(), m['censo_branca_0_16'].sum()),
    ], columns=['grupo', 'internacoes', 'pop_0_16_censo'])
    taxas['taxa_1000_criancas_ano'] = (taxas['internacoes'] / n_anos / taxas['pop_0_16_censo'] * 1000).round(2)
    mostrar(f'5b. Taxa de internação por raça = internações / {n_anos} anos / crianças 0–16 do grupo × 1000',
            taxas, '05b_taxa_internacao_raca.csv')

    razao = m[(m['int_ppi'] >= 20) & (m['int_branca'] >= 20)]['razao_taxa_ppi_branca']
    print(f'\nRazão de taxas PPI/Branca por município (n = {len(razao)} com ≥ 20 internações em cada grupo): '
          f'mediana = {razao.median():.2f}; municípios com razão < 1: {(razao < 1).mean() * 100:.1f}%')

    # ============================================================
    # 6. CORRELAÇÕES MUNICIPAIS (Spearman)
    # ============================================================
    # Spearman: robusto a outliers e a relações não lineares; apenas municípios
    # com ao menos 30 internações para evitar proporções instáveis.
    base = m[m['internacoes'] >= 30]
    variaveis = ['pct_criancas_bf', 'pct_pop_bf_pobreza', 'trab_inf_10mil_criancas',
                 'pct_ppi_censo_0_16', 'pct_ppi_cadunico', 'razao_ppi_cadunico_censo', 'razao_taxa_ppi_branca',
                 'taxa_int_1000_criancas_ano', 'pct_fora_municipio', 'dist_media_km']
    corr = base[variaveis].corr(method='spearman').round(2)
    corr.insert(0, 'variavel', corr.index)
    mostrar(f'6. Correlação de Spearman entre indicadores municipais (n = {len(base)} municípios com ≥ 30 internações)',
            corr, '06_correlacoes.csv')

    m.to_csv(DIR_SAIDA / 'indicadores_municipais.csv', index=False)
    print(f'\nArquivos salvos em {DIR_SAIDA}')


if __name__ == '__main__':
    main()
