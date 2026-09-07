from pathlib import Path
import time
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sshtunnel import SSHTunnelForwarder
from gerador_matches import get_matches

DIR_PROJETO = Path(__file__).resolve().parent

df = get_matches()

# ------------------------------------ Conexão ao BD: ------------------------------------
load_dotenv() # carrega as credenciais

ssh_host = os.getenv('HOST_SSH')
ssh_user = os.getenv('USER_SSH')
ssh_password = os.getenv('PASSWORD_SSH')
# ssh_key = str(DIR_PROJETO/'key.pem')
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
    df.to_sql('bd2_2556553', engine, if_exists='replace', index=False)

    # Para windows e conexao direta via terminal, descomentar as linhas abaixo e comentar as linhas acima (que usam o SSHTunnelForwarder)

    # string_conexao = f"postgresql+psycopg2://{db_user}:{db_password}@127.0.0.1:{db_port}/{db_name}"
    # engine = create_engine(string_conexao)

    # inicio = time.perf_counter()
    # df.to_sql('bd2_2556553', engine, if_exists='replace', index=False)
    # fim = time.perf_counter()
    
    query = "SELECT * FROM bd2_2556553"
    inicio = time.perf_counter()
    df_ler = pd.read_sql_query(text(query), engine)
    fim = time.perf_counter()

    print(df_ler.head())
    print(f"tempo de execução da consulta: {fim - inicio:.4f} segundos")

    