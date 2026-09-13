import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

db_host = os.getenv('DB_HOST')
db_port = int(os.getenv('DB_PORT'))
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

string_conexao = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(string_conexao)

queries = {
    'renda_ate_fev2023_pbf': """
        SELECT * FROM public.bd2_2556553_renda_ate_fev2023_pbf
    """,
    'renda_apos_mar2023_pbf': """
        SELECT * FROM public.bd2_2556553_renda_apos_mar2023_pbf
    """,
    'faixa_etaria_fem_pbf': """
        SELECT * FROM public.bd2_2556553_faixa_etaria_fem_pbf
    """,
    'faixa_etaria_masc_pbf': """
        SELECT * FROM public.bd2_2556553_faixa_etaria_masc_pbf
    """,
    'raca_cor_cadunico': """
        SELECT * FROM public.bd2_2556553_raca_cor_cadunico
    """,
    'trab_infantil_pbf': """
        SELECT * FROM public.bd2_2556553_trab_infantil_pbf
    """
}

for nome, query in queries.items():
    df = pd.read_sql_query(text(query), engine)

    print(70 * "=")
    print(f"DATASET: {nome}")
    print(70 * "=")

    print("DADOS NULOS")
    total_nulos = df.isnull().sum().sum()
    print(f"-> Total de dados nulos no dataset: {total_nulos}")

    total_celulas = df.size
    porcentagem_geral = (total_nulos / total_celulas) * 100
    print(f"-> Porcentagem geral de dados nulos: {porcentagem_geral:.2f}%")

    print("\n-> Detalhamento por coluna:")
    nulos_por_coluna = df.isnull().sum()
    porcentagem_por_coluna = df.isnull().mean() * 100

    for coluna in df.columns:
        if nulos_por_coluna[coluna] > 0:
            print(
                f"Coluna '{coluna}': {nulos_por_coluna[coluna]} valores "
                f"nulos ({porcentagem_por_coluna[coluna]:.2f}%)"
            )
            print("   -> Detalhamento dos nulos:")
            linhas_vazias = df[df[coluna].isnull()]
            meses_vazios = linhas_vazias['data'].unique()
            print(f"   -> Esses nulos ocorreram nos seguintes meses: {meses_vazios}\n")
            
        else:
            print(f"Coluna '{coluna}': Nenhum valor nulo encontrado.")

    print("\n" + 70 * "-")
    print("MUNICÍPIOS FALTANTES")
    print(70 * "-")

    qtd_municipios = df['municipio'].nunique()
    print(f"-> Quantidade de municípios únicos encontrados: {qtd_municipios}")
    if qtd_municipios == 399:
        print("Sucesso! Nenhum município faltando.")
    else:
        print(f"Atenção! Estão faltando {399 - qtd_municipios} municípios.")