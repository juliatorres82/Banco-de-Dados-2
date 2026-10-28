
import os

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import geobr
import numpy as np

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder


# ============================================================
# 1. CONEXÃO AO BANCO DE DADOS
# ============================================================

load_dotenv()

ssh_host = os.getenv('HOST_SSH')
ssh_user = os.getenv('USER_SSH')
ssh_password = os.getenv('PASSWORD_SSH')
ssh_key = os.getenv('KEY_SSH')

db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

if not os.path.exists(ssh_key):
    raise FileNotFoundError(
        f"Chave SSH não encontrada: {ssh_key}"
    )


# ============================================================
# 2. CONSULTA SQL: AGRUPAMENTO POR DÉCADA
# ============================================================

query = """
    SELECT
        municipio,
        (EXTRACT(YEAR FROM data)::int / 10) * 10 AS decada,
        latitude,
        longitude,

        SUM(qtd_bf_fem_0_3_anos) AS bf_fem03,
        SUM(qtd_bf_fem_4_6_anos) AS bf_fem46,
        SUM(qtd_bf_fem_7_15_anos) AS bf_fem7_15,
        SUM(qtd_bf_fem_16_17_anos) AS bf_fem16_17,
        SUM(qtd_bf_fem_18_24_anos) AS bf_fem18_24,
        SUM(qtd_bf_fem_25_34_anos) AS bf_fem25_34,
        SUM(qtd_bf_fem_35_39_anos) AS bf_fem35_39,
        SUM(qtd_bf_fem_40_44_anos) AS bf_fem40_44,
        SUM(qtd_bf_fem_45_49_anos) AS bf_fem45_49,
        SUM(qtd_bf_fem_50_54_anos) AS bf_fem50_54,
        SUM(qtd_bf_fem_55_59_anos) AS bf_fem55_59,
        SUM(qtd_bf_fem_60_64_anos) AS bf_fem60_64,
        SUM(qtd_bf_fem_acima_64_anos) AS bf_fem_mais64

    FROM bd2_2556553_faixa_etaria_fem_pbf

    WHERE data >= DATE '2000-01-01'
      AND data < DATE '2030-01-01'

    GROUP BY
        municipio,
        decada,
        latitude,
        longitude

    ORDER BY decada, municipio
"""


# ============================================================
# 3. EXECUÇÃO DA CONSULTA
# ============================================================

with SSHTunnelForwarder(
    (ssh_host, 22),
    ssh_username=ssh_user,
    ssh_pkey=ssh_key,
    ssh_password=ssh_password,
    ssh_private_key_password=ssh_password,
    remote_bind_address=(db_host, db_port),
    allow_agent=False
) as tunnel:

    print(
        f"SSH Tunnel criado na porta local: "
        f"{tunnel.local_bind_port}"
    )

    print("Conectando ao banco de dados...")

    string_conexao = (
        f"postgresql://{db_user}:{db_password}"
        f"@127.0.0.1:{tunnel.local_bind_port}/{db_name}"
    )

    engine = create_engine(string_conexao)

    try:
        with engine.connect() as conexao:
            df_publicado = pd.read_sql_query(
                text(query),
                conexao
            )
    finally:
        engine.dispose()

print("Consulta concluída!")
print(df_publicado.head())


# ============================================================
# 4. CLASSIFICAÇÃO EM CICLOS DE VIDA
# ============================================================

# Ciclo 1: infância (0 a 15 anos)
df_publicado['infanciafem_0_15'] = (
    df_publicado['bf_fem03']
    + df_publicado['bf_fem46']
    + df_publicado['bf_fem7_15']
)

# Ciclo 2: juventude (16 a 24 anos)
df_publicado['juventfem_16_24'] = (
    df_publicado['bf_fem16_17']
    + df_publicado['bf_fem18_24']
)

# Ciclo 3: idade adulta (25 a 54 anos)
df_publicado['adultfem_25_54'] = (
    df_publicado['bf_fem25_34']
    + df_publicado['bf_fem35_39']
    + df_publicado['bf_fem40_44']
    + df_publicado['bf_fem45_49']
    + df_publicado['bf_fem50_54']
)

# Ciclo 4: 55 anos ou mais
df_publicado['adultfem_55mais'] = (
    df_publicado['bf_fem55_59']
    + df_publicado['bf_fem60_64']
    + df_publicado['bf_fem_mais64']
)

colunas_ciclos = [
    'infanciafem_0_15',
    'juventfem_16_24',
    'adultfem_25_54',
    'adultfem_55mais'
]

# Tratar valores nulos nas faixas etárias
df_publicado[colunas_ciclos] = (
    df_publicado[colunas_ciclos].fillna(0)
)


# ============================================================
# 5. AGRUPAMENTO POR DÉCADA
# ============================================================

df_agrupado = (
    df_publicado
    .groupby('decada')[colunas_ciclos]
    .sum()
    .reset_index()
    .sort_values('decada')
)

print("\nTotais por década:")
print(df_agrupado.to_string(index=False))


# ============================================================
# 6. CÁLCULO DOS PERCENTUAIS
# ============================================================

df_percentual = df_agrupado.copy()

df_percentual['total'] = (
    df_percentual[colunas_ciclos].sum(axis=1)
)

for ciclo in colunas_ciclos:
    df_percentual[ciclo] = (
        df_percentual[ciclo]
        / df_percentual['total'].replace(0, np.nan)
        * 100
    )

print("\nPercentuais por década:")
print(df_percentual.to_string(index=False))


# ============================================================
# 7. GRÁFICO COMPARATIVO ENTRE AS DÉCADAS
# ============================================================

decadas = df_percentual['decada'].astype(int).tolist()

x = np.arange(len(colunas_ciclos))

n_decadas = len(decadas)
width = 0.8 / max(n_decadas, 1)

cores = ['pink', 'coral', 'salmon']

fig, ax = plt.subplots(figsize=(11, 6))

for i, decada in enumerate(decadas):

    linha = df_percentual.loc[
        df_percentual['decada'] == decada
    ]

    valores = linha[colunas_ciclos].iloc[0].values

    deslocamento = (
        i - (n_decadas - 1) / 2
    ) * width

    ax.bar(
        x + deslocamento,
        valores,
        width,
        label=f'Década de {decada}',
        color=cores[i % len(cores)]
    )

ax.set_ylabel(
    'Proporção do total de beneficiárias (%)'
)

ax.set_title(
    'Evolução do perfil etário feminino no PBF - Paraná'
)

ax.set_xticks(x)

ax.set_xticklabels([
    'Infância\n(0-15 anos)',
    'Juventude\n(16-24 anos)',
    'Adultas\n(25-54 anos)',
    '55 anos ou mais'
])

ax.set_ylim(bottom=0)
ax.grid(axis='y', alpha=0.25)
ax.set_axisbelow(True)

ax.legend(title='Período')

plt.tight_layout()
plt.show()