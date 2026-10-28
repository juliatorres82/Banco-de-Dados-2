import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import geobr
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder
 
# ------------------------------------ Conexão ao BD: ------------------------------------
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
    raise FileNotFoundError(f"Chave SSH não encontrada: {ssh_key}")

# CRIA TUNEL
with SSHTunnelForwarder(
    (ssh_host, 22), 
    ssh_username=ssh_user,
    ssh_pkey=ssh_key,
    ssh_password=ssh_password,
    ssh_private_key_password=ssh_password,
    remote_bind_address=(db_host, db_port),
    allow_agent=False
) as tunnel:
    
    print(f"SSH Tunnel criado na porta local: {tunnel.local_bind_port}")
    print("Conectando ao banco de dados...")
    
    string_conexao = f"postgresql://{db_user}:{db_password}@127.0.0.1:{tunnel.local_bind_port}/{db_name}"
    engine = create_engine(string_conexao)

    query = """

        SELECT 
            municipio,
            (EXTRACT(YEAR FROM data)::int / 10) * 10 AS decada,
            latitude,
            longitude,
            SUM(qtd_bf_masc_0_3_anos) AS bf_masc03,
			SUM(qtd_bf_masc_4_6_anos) AS bf_masc46,
			SUM(qtd_bf_masc_7_15_anos) AS bf_masc7_15,
			SUM(qtd_bf_masc_16_17_anos) AS bf_masc16_17,
			SUM(qtd_bf_masc_18_24_anos) AS bf_masc18_24,
			SUM(qtd_bf_masc_25_34_anos) AS bf_masc25_34,
			SUM(qtd_bf_masc_35_39_anos) AS bf_masc35_39,
            SUM(qtd_bf_masc_40_44_anos) AS bf_masc40_44,
			SUM(qtd_bf_masc_45_49_anos) AS bf_masc45_49,
			SUM(qtd_bf_masc_50_54_anos) AS bf_masc50_54,
			SUM(qtd_bf_masc_55_59_anos) AS bf_masc55_59,
			SUM(qtd_bf_masc_60_64_anos) AS bf_masc60_64,
			SUM(qtd_bf_masc_acima_64_anos) AS bf_masc_mais64
        FROM bd2_2556553_faixa_etaria_masc_pbf 
        GROUP BY 
            municipio, decada, latitude, longitude
    """

    df_publicado = pd.read_sql_query(text(query), engine)

# ------------------------------------ Mapeamento: ------------------------------------

####################### 1) CLASSIFICACAO EM "CICLOS DE VIDA":

# ciclo 1: 0 - 15 anos = infância, dependentes;
df_publicado['infanciamasc_0_15'] = df_publicado['bf_masc03'] + df_publicado['bf_masc46'] + df_publicado['bf_masc7_15']

#ciclo 2: período de maior evasão escolar, transição para o mercado de trabalho;
df_publicado['juventmasc_16_24'] = df_publicado['bf_masc16_17'] + df_publicado['bf_masc18_24']

#ciclo 3: maior inserção no mercado de trabalho, maior chance de dependentes
df_publicado['adultmasc_25_54'] = df_publicado['bf_masc25_34'] + df_publicado['bf_masc35_39'] + df_publicado['bf_masc40_44'] + df_publicado['bf_masc45_49'] + df_publicado['bf_masc50_54']

#ciclo 4: período de transição para aposentadoria + aposentadas
df_publicado['adultmasc_55mais'] = df_publicado['bf_masc55_59'] + df_publicado['bf_masc60_64']

############################################
# FAZENDO AGRUPAMENTO POR DÉCADA:

colunas_ciclos = ['infanciamasc_0_15', 'juventmasc_16_24', 'adultmasc_25_54', 'adultmasc_55mais']
df_agrupado = df_publicado.groupby('decada')[colunas_ciclos].sum().reset_index()

print(df_agrupado)

# transformando em percentuais para vermos a proporção
df_percentual = df_agrupado.copy()
df_percentual['total'] = df_percentual[colunas_ciclos].sum(axis=1)
for ciclo in colunas_ciclos:
    df_percentual[ciclo] = (df_percentual[ciclo] / df_percentual['total']) * 100


#plotando um grafico comparativo:
decadas = df_agrupado['decada'].astype(int).astype(str).tolist()
x = np.arange(len(colunas_ciclos))  
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

if len(decadas) == 2:
    valores_decada1 = df_percentual.loc[0, colunas_ciclos].values
    valores_decada2 = df_percentual.loc[1, colunas_ciclos].values
    
    rects1 = ax.bar(x - width/2, valores_decada1, width, label=f'Década {decadas[0]}', color='green')
    rects2 = ax.bar(x + width/2, valores_decada2, width, label=f'Década {decadas[1]}', color='lightgreen')

ax.set_ylabel('Proporção do total de beneficiárias (%)')
ax.set_title('Evolução do perfil etário masculino no PBF - PR')
ax.set_xticks(x)
ax.set_xticklabels(['\n(0-15 anos)', '\n(16-24 anos)', '\n(25-54 anos)', '\n(55+ anos)'])
ax.legend()

plt.tight_layout()
plt.show()