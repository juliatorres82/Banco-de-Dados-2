import time
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder


################## DF 1: Beneficiários do Programa Bolsa Família por faixa de renda (PR) ##################
df_bf_renda = pd.read_csv('/home/julia/BD2/Datasets/beneficiarios_bs_por_renda_pr.csv', sep=',', encoding='utf-8')

df_bf_renda = df_bf_renda.rename(columns={'Referência':'Data', 'Quantidade de pessoas em famílias beneficiárias do Programa Bolsa Família em situação de pobreza, segundo a faixa do Programa*':'Familias Beneficiarias BS em pobreza',
'Quantidade de pessoas em famílias de baixa renda** beneficiárias do Programa Bolsa Família':'Familias Beneficiarias BS de baixa renda', 
'Quantidade de pessoas em famílias com renda per capita mensal acima de meio salário-mínimo*** beneficiárias do Programa Bolsa Família':'Familias Beneficiarias BS renda per capita maior meio salario minimo'})


################## DF 2: Beneficiários do Programa Bolsa Família por faixa etária (PR) - Feminino ##################


df_bf_faixa_etaria_feminino = pd.read_csv('/home/julia/BD2/Datasets/feminino_benef_bf_faixa_etaria_pr.csv', sep=',', encoding='utf-8')

df_bf_faixa_etaria_feminino = df_bf_faixa_etaria_feminino.rename(columns={'Referência':'Data', 
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 0 e 3 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF feminino 0 a 3 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 4 e 6 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF feminino 4 a 6 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 7 e 15 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF feminino 7 a 15 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 16 e 17 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 16 a 17 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 18 e 24 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 18 a 24 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 25 e 34 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 25 a 34 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 35 e 39 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 35 a 39 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 40 e 44 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 40 a 44 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 45 e 49 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 45 a 49 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 50 e 54 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 50 a 54 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 55 e 59 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 55 a 59 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade entre 60 e 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino 60 a 64 anos',
                                                                          'Quantidade de pessoas do sexo feminino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino acima de 64 anos'
})


################## DF 3: Beneficiários do Programa Bolsa Família por faixa etária (PR) - Masculino ##################


df_bf_faixa_etaria_masculino = pd.read_csv('/home/julia/BD2/Datasets/Tabela_PBFHomem_FaixaEtaria_2015a2026.csv', sep=',', encoding='utf-8')

df_bf_faixa_etaria_masculino = df_bf_faixa_etaria_masculino.rename(columns={'Referência':'Data', 
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 0 e 3 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 0 a 3 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 4 e 6 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 4 a 6 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 7 e 15 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 7 a 15 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 16 e 17 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 16 a 17 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 18 e 24 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 18 a 24 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 25 e 34 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 25 a 34 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 35 e 39 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 35 a 39 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 40 e 44 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 40 a 44 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 45 e 49 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 45 a 49 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 50 e 54 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 50 a 54 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 55 e 59 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 55 a 59 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade entre 60 e 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino 60 a 64 anos',
                                                                          'Quantidade de pessoas do sexo masculino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF masculino acima de 64 anos'
})


################## DF 4: Beneficiários do Programa Bolsa Família por tipo de benefício (PR) ##################

df_bf_qntde_beneficios_por_tipo = pd.read_csv('/home/julia/BD2/Datasets/Tabela_PBF_BeneficiosPorTipo_2023a2026.csv', sep=',', encoding='utf-8')
df_bf_qntde_beneficios_por_tipo = df_bf_qntde_beneficios_por_tipo.rename(columns={'Referência':'Data',})


################# CONCATENANDO OS DADOS: #################

#full outer join de todas as tabelas usando as DATAS:
df_merged = pd.merge(df_bf_renda, df_bf_faixa_etaria_feminino, on='Data', how='outer')
df_merged = pd.merge(df_merged, df_bf_faixa_etaria_masculino, on='Data', how='outer')
df_merged = pd.merge(df_merged, df_bf_qntde_beneficios_por_tipo, on='Data', how='outer')

df_merged.to_csv('/home/julia/BD2/Datasets/df_merged.csv', index=False, encoding='utf-8')


# ------------------------------------ Conexão ao BD: ------------------------------------
load_dotenv() # carrega as credenciais

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

print("Iniciando a criação do túnel...")

# Cria tunel SSH:
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

    # inserindo o novo dataframe (já merged) no banco de dados:
    df_merged.to_sql('bd2_2556553', engine, if_exists='replace', index=False)

    # visualizando:

    inicio = time.perf_counter()

    query = "SELECT * FROM bd2_2556553"
    df_ler = pd.read_sql_query(text(query), engine)

    fim = time.perf_counter()

    print(df_ler.head())
    print(f"tempo de execução da consulta: {fim - inicio:.4f} segundos")