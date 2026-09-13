import pandas as pd
import os
from pathlib import Path
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

DIR_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_BASES = DIR_PROJETO/'Datasets'

load_dotenv()

def gera_dict():
    df_renda_1 = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_PBF_Renda_ateFev2023.csv', sep=',', encoding='latin1')
    df_renda_2 = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_PBF_Renda_dpsMar2023.csv', sep=',', encoding='latin1')
    dfFem_faixaEtaria = pd.read_csv(f'{CAMINHO_BASES}/PessoasFem_PBF_faixaEtaria.csv', sep=',', encoding='latin1')
    dfMasc_faixaEtaria = pd.read_csv(f'{CAMINHO_BASES}/PessoasMasc_PBF_faixaEtaria.csv', sep=',', encoding='latin1')
    df_CADUNICO_racaCor = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_CadUnico_RacaCor.csv', sep=',', encoding='latin1')
    df_TrabInfantil = pd.read_csv(f'{CAMINHO_BASES}/Familias_Pessoas_TrabInfantil.csv', sep=',', encoding='latin1')
    
    df_renda_1 = df_renda_1.drop(columns=['Código', 'UF'])
    df_renda_1 = df_renda_1.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de pessoas em famílias  em situação de extrema pobreza beneficiárias do Programa Bolsa Família': 'qtd_bf_extrema_pobreza',
        'Quantidade de pessoas em famílias  em situação de pobreza beneficiárias do Programa Bolsa Família': 'qtd_bf_pobreza',
        'Quantidade de pessoas em famílias de baixa renda** beneficiárias do Programa Bolsa Família': 'qtd_bf_baixa_renda'
    })

    df_renda_2 = df_renda_2.drop(columns=['Código', 'UF'])
    df_renda_2 = df_renda_2.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de pessoas em famílias beneficiárias do Programa Bolsa Família em situação de pobreza, segundo a faixa do Programa*': 'qtd_bf_pobreza_new',
        'Quantidade de pessoas em famílias de baixa renda** beneficiárias do Programa Bolsa Família': 'qtd_bf_baixa_renda',
        'Quantidade de pessoas em famílias com renda per capita mensal acima de meio salário-mínimo*** beneficiárias do Programa Bolsa Família': 'qtd_bf_renda_maior_meio_sm'
    })

    dfFem_faixaEtaria = dfFem_faixaEtaria.drop(columns=['Código', 'UF'])
    dfFem_faixaEtaria = dfFem_faixaEtaria.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de pessoas do sexo feminino com idade entre 0 e 3 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_0_3_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 4 e 6 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_4_6_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 7 e 15 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_7_15_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 16 e 17 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_16_17_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 18 e 24 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_18_24_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 25 e 34 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_25_34_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 35 e 39 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_35_39_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 40 e 44 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_40_44_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 45 e 49 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_45_49_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 50 e 54 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_50_54_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 55 e 59 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_55_59_anos',
        'Quantidade de pessoas do sexo feminino com idade entre 60 e 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_60_64_anos',
        'Quantidade de pessoas do sexo feminino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_fem_acima_64_anos'
    })

    dfMasc_faixaEtaria = dfMasc_faixaEtaria.drop(columns=['Código', 'UF'])
    dfMasc_faixaEtaria = dfMasc_faixaEtaria.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de pessoas do sexo masculino com idade entre 0 e 3 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_0_3_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 4 e 6 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_4_6_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 7 e 15 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_7_15_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 16 e 17 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_16_17_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 18 e 24 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_18_24_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 25 e 34 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_25_34_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 35 e 39 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_35_39_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 40 e 44 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_40_44_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 45 e 49 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_45_49_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 50 e 54 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_50_54_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 55 e 59 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_55_59_anos',
        'Quantidade de pessoas do sexo masculino com idade entre 60 e 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_60_64_anos',
        'Quantidade de pessoas do sexo masculino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'qtd_bf_masc_acima_64_anos'
    })

    df_CADUNICO_racaCor = df_CADUNICO_racaCor.drop(columns=['Código', 'UF'])
    df_CADUNICO_racaCor = df_CADUNICO_racaCor.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de pessoas brancas inscritas no Cadastro Único': 'qtd_cadunico_brancas',
        'Quantidade de pessoas pretas inscritas no Cadastro Único': 'qtd_cadunico_pretas',
        'Quantidade de pessoas amarelas inscritas no Cadastro Único': 'qtd_cadunico_amarelas',
        'Quantidade de pessoas pardas inscritas no Cadastro Único': 'qtd_cadunico_pardas',
        'Quantidade de pessoas indígenas inscritas no Cadastro Único': 'qtd_cadunico_indigenas',
        'Quantidade de pessoas sem informação sobre raça/cor inscritas no Cadastro Único': 'qtd_cadunico_sem_info_cor'
    })

    df_TrabInfantil = df_TrabInfantil.drop(columns=['Código', 'UF'])
    df_TrabInfantil = df_TrabInfantil.rename(columns={
        'Referência': 'data', 
        'Unidade Territorial': 'municipio',
        'Quantidade de famílias beneficiárias do Programa Bolsa Família em situação de trabalho infantil': 'qtd_familias_bf_trab_infantil',
        'Quantidade de pessoas beneficiárias do Programa Bolsa Família em situação de trabalho infantil': 'qtd_pessoas_bf_trab_infantil'
    })
    
    meus_dfs = {
        'renda_ate_fev2023_pbf': df_renda_1,
        'renda_apos_mar2023_pbf': df_renda_2,
        'faixa_etaria_fem_pbf': dfFem_faixaEtaria,
        'faixa_etaria_masc_pbf': dfMasc_faixaEtaria,
        'raca_cor_cadunico': df_CADUNICO_racaCor, 
        'trab_infantil_pbf': df_TrabInfantil
    }

    return meus_dfs

def trata_dfs(meus_dfs):
    
    for nome, df in meus_dfs.items():
        print(70*"=")
        print(f"Processando o dataset: {nome}")
        print(70*"=")
        print(70*"-")
        print(f"Colunas do dataset: \n{df.columns}")
        print(70*"-")
        print(f"Tipos de dados do dataset: \n{df.dtypes}")
        print(70*"-")
        df['data'] = pd.to_datetime(df['data'], format='%m/%Y')

        coluna_ignorada = ['data', 'municipio']
        colunas_para_converter = df.columns.difference(coluna_ignorada)
        df[colunas_para_converter] = df[colunas_para_converter].astype('Int64')
        print(f"Tipos de dados do dataset após conversão: \n{df.dtypes}")
        print(70*"-")

        df_final = df.drop_duplicates(subset=['municipio', 'data'])
        if len(df_final) == len(df):
            print(f"Nenhuma tupla duplicada encontrada. Tamanho do dataset final: {len(df_final)}")
            print(70*"-", "\n\n")

        elif len(df_final) < len(df):
            print(f"Total de tuplas duplicadas removidas: {len(df) - len(df_final)}")
            print(70*"-", "\n\n")

def manda_banco(meus_dfs):
    
    for nome, df in meus_dfs.items():
        print(70*"=")
        print(f"Inserindo o dataset: {nome} no banco de dados")
        print(70*"=")
        print(70*"-")
        db_host = os.getenv('DB_HOST')
        db_port = int(os.getenv('DB_PORT'))
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')
    
        string_conexao = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(string_conexao)
        
        nome_tabela = f"bd2_2556553_{nome}"
        
        inicio = time.perf_counter()
        
        df.to_sql(
            name=nome_tabela, 
            con=engine,
            if_exists='fail',
            index=False
        )
        
        print(nome_tabela)
        fim = time.perf_counter()
        print(f"\nInserção da {nome_tabela} no banco: {fim - inicio:.2f} segundos")
        print(70*"-")

meus_dfs = gera_dict()
trata_dfs(meus_dfs)
manda_banco(meus_dfs)