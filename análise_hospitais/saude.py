import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import geobr
import numpy as np


caminho_file_saude = '/home/julia/BD2/Datasets/SAUDE_FINAL.csv'
caminho_file_mun = '/home/julia/BD2/Datasets/ids_municipios.csv'
caminho_file_cid = '/home/julia/BD2/Datasets/cid.csv'

df_saude = pd.read_csv(caminho_file_saude)
codigos_mun = pd.read_csv(caminho_file_mun)
cid = pd.read_csv(caminho_file_cid)

### substituindo os códigos do municipio do paciente pelo nome real
df_saude = df_saude.merge(
    codigos_mun[['id_municipio_6', 'nome']],
    left_on='id_municipio_paciente',
    right_on='id_municipio_6',
    how='left'
)

df_saude = df_saude.rename(columns={'nome': 'municipio_paciente'})
df_saude = df_saude.drop(columns=['id_municipio_paciente', 'id_municipio_6'])


### substituindo os códigos do id_muncipio_estabelecimento pelo nome real 

df_saude = df_saude.merge(
    codigos_mun[['id_municipio_6', 'nome']],
    left_on='id_municipio_estabelecimento',
    right_on='id_municipio_6',
    how='left'
)

df_saude = df_saude.rename(
    columns={'nome': 'municipio_estabelecimento'}
)

df_saude = df_saude.drop(
    columns=['id_municipio_estabelecimento', 'id_municipio_6']
)


### substituindo o código cid pelo diagnóstico real 
df_saude = df_saude.merge(
    cid[['subcategoria', 'descricao_subcategoria']],
    left_on='cid_principal_categoria',
    right_on='subcategoria',
    how= 'left'
)
df_saude = df_saude.rename(columns={'descricao_subcategoria': 'diagnostico'})
df_saude = df_saude.drop(columns=['cid_principal_categoria'])

df_saude.to_csv('saude_traduzido.csv', index=False)

print(df_saude['diagnostico'].head(10))
