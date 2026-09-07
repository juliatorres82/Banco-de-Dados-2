import pandas as pd
import os
from pathlib import Path

#EDITAR AQUI PARA O CAMINHO DAS BASES DE DADOS
DIR_PROJETO = Path(__file__).resolve().parent
CAMINHO_BASES = DIR_PROJETO/'Datasets'

def leitor_df():
    df_renda_1 = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_PBF_Renda_ateFev2023.csv', sep=',', encoding='latin1')
    df_renda_2 = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_PBF_Renda_dpsMar2023.csv', sep=',', encoding='latin1')
    dfFem_faixaEtaria = pd.read_csv(f'{CAMINHO_BASES}/PessoasFem_PBF_faixaEtaria.csv', sep=',', encoding='latin1')
    dfMasc_faixaEtaria = pd.read_csv(f'{CAMINHO_BASES}/PessoasMasc_PBF_faixaEtaria.csv', sep=',', encoding='latin1')
    df_CADUNICO_faixaEtaria = pd.read_csv(f'{CAMINHO_BASES}/Pessoas_CadUnico_RacaCor.csv', sep=',', encoding='latin1')
    df_TrabInfantil = pd.read_csv(f'{CAMINHO_BASES}/Familias_Pessoas_TrabInfantil.csv', sep=',', encoding='latin1')
    
    return df_renda_1, df_renda_2, dfFem_faixaEtaria, dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil

def trata_df(df_renda_1, df_renda_2, dfFem_faixaEtaria, dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil):
    
    df_renda_1 = df_renda_1.drop(columns=['Código', 'UF'])
    df_renda_1 = df_renda_1.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
                                        'Quantidade de pessoas em famílias  em situação de extrema pobreza beneficiárias do Programa Bolsa Família':'Pessoas beneficiarias BF em extrema pobreza',
                                        'Quantidade de pessoas em famílias  em situação de pobreza beneficiárias do Programa Bolsa Família':'Pessoas beneficiarias BF em pobreza',
                                        'Quantidade de pessoas em famílias de baixa renda** beneficiárias do Programa Bolsa Família':'Pessoas beneficiarias BF em baixa renda'})



    df_renda_2 = df_renda_2.drop(columns=['Código', 'UF'])
    df_renda_2 = df_renda_2.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
                                        'Quantidade de pessoas em famílias beneficiárias do Programa Bolsa Família em situação de pobreza, segundo a faixa do Programa*':'Pessoas beneficiarias BF em pobreza',
                                        'Quantidade de pessoas em famílias de baixa renda** beneficiárias do Programa Bolsa Família':'Pessoas beneficiarias BF em baixa renda',
                                        'Quantidade de pessoas em famílias com renda per capita mensal acima de meio salário-mínimo*** beneficiárias do Programa Bolsa Família':'Pessoas beneficiarias BF renda per capita maior meio salario minimo'})

    dfFem_faixaEtaria = dfFem_faixaEtaria.drop(columns=['Código', 'UF'])
    dfFem_faixaEtaria = dfFem_faixaEtaria.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
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
                                                        'Quantidade de pessoas do sexo feminino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único': 'Beneficiarias BF feminino acima de 64 anos'})

    dfMasc_faixaEtaria = dfMasc_faixaEtaria.drop(columns=['Código', 'UF'])
    dfMasc_faixaEtaria = dfMasc_faixaEtaria.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 0 e 3 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 0 a 3 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 4 e 6 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 4 a 6 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 7 e 15 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 7 a 15 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 16 e 17 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 16 a 17 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 18 e 24 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 18 a 24 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 25 e 34 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 25 a 34 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 35 e 39 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 35 a 39 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 40 e 44 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 40 a 44 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 45 e 49 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 45 a 49 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 50 e 54 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 50 a 54 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 55 e 59 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 55 a 59 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade entre 60 e 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino 60 a 64 anos',
                                                        'Quantidade de pessoas do sexo masculino com idade acima de 64 anos beneficiárias do Programa Bolsa Família inscritas no Cadastro Único':'Beneficiarias BF masculino acima de 64 anos'})

    df_CADUNICO_faixaEtaria = df_CADUNICO_faixaEtaria.drop(columns=['Código', 'UF'])
    df_CADUNICO_faixaEtaria = df_CADUNICO_faixaEtaria.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
                                                                    'Quantidade de pessoas brancas inscritas no Cadastro Único':'Beneficiarios CadUnico brancos',
                                                                    'Quantidade de pessoas pretas inscritas no Cadastro Único':'Beneficiarios CadUnico pretos',
                                                                    'Quantidade de pessoas amarelas inscritas no Cadastro Único':'Beneficiarios CadUnico amarelos',
                                                                    'Quantidade de pessoas pardas inscritas no Cadastro Único':'Beneficiarios CadUnico pardos',
                                                                    'Quantidade de pessoas indígenas inscritas no Cadastro Único':'Beneficiarios CadUnico indigenas',
                                                                    'Quantidade de pessoas sem informação sobre raça/cor inscritas no Cadastro Único':'Beneficiarios CadUnico sem informacao raca/cor'})

    df_TrabInfantil = df_TrabInfantil.drop(columns=['Código', 'UF'])
    df_TrabInfantil = df_TrabInfantil.rename(columns={'Referência':'Data', 'Unidade Territorial':'Municipio',
                                                    'Quantidade de famílias beneficiárias do Programa Bolsa Família em situação de trabalho infantil':'Familias BF em situação de trabalho infantil',
                                                    'Quantidade de pessoas beneficiárias do Programa Bolsa Família em situação de trabalho infantil':'Pessoas BF em situação de trabalho infantil'})

    return df_renda_1, df_renda_2, dfFem_faixaEtaria, dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil

def get_matches():
    
    df_renda_1, df_renda_2, dfFem_faixaEtaria, dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil = leitor_df()
    
    df_renda_1, df_renda_2, dfFem_faixaEtaria, dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil = trata_df(df_renda_1, df_renda_2, dfFem_faixaEtaria, 
                                                                                                                       dfMasc_faixaEtaria, df_CADUNICO_faixaEtaria, df_TrabInfantil)
    
    df_renda = pd.concat([df_renda_1, df_renda_2], ignore_index=True)
    df_merge_1 = pd.merge(df_renda, dfFem_faixaEtaria, on=['Data', 'Municipio'], how='outer')
    df_merge_2 = pd.merge(df_merge_1, dfMasc_faixaEtaria, on=['Data', 'Municipio'], how='outer')
    df_merge_3 = pd.merge(df_merge_2, df_CADUNICO_faixaEtaria, on=['Data', 'Municipio'], how='outer')
    df_final = pd.merge(df_merge_3, df_TrabInfantil, on=['Data', 'Municipio'], how='outer')
    
    #transformando para inteiro
    coluna_ignorada = ['Data', 'Municipio']
    colunas_para_converter = df_final.columns.difference(coluna_ignorada)
    df_final[colunas_para_converter] = df_final[colunas_para_converter].astype('Int64')
    
    print(f"Total de tuplas no dataset final: {len(df_final)}")
    
    duplicados = df_final[df_final.duplicated(subset=['Municipio', 'Data'], keep=False)]

    print(f"Encontradas {len(duplicados)} linhas duplicadas.")
    print(duplicados)

    df_final = df_final.drop_duplicates(subset=['Municipio', 'Data'])
    print(f"Total de tuplas no dataset final após remover duplicatas: {len(df_final)}")
    
    return df_final