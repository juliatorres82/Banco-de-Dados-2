import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import geobr
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

print("Iniciando a criação do túnel...")

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
        SUM(qtd_familias_bf_trab_infantil) AS qtd_familias_bf_trab_infantil,
        SUM(qtd_pessoas_bf_trab_infantil) AS qtd_pessoas_bf_trab_infantil
    FROM bd2_2556553_trab_infantil_pbf 
    GROUP BY 
        municipio, decada, latitude, longitude
    """

    df_publicado = pd.read_sql_query(text(query), engine)
    print("Dados extraídos com sucesso!")

# ------------------------------------ Mapeamento: ------------------------------------


# converter o Df do pandas para GeoDataFrame
gdf_pontos = gpd.GeoDataFrame(
    df_publicado, 
    geometry=gpd.points_from_xy(df_publicado['longitude'], df_publicado['latitude']),
    crs="EPSG:4326"
)

# baixar o mapa de municípios do PR via geobr
print("Baixando malha municipal do PR...")
pr_mapa = geobr.read_municipality(code_muni="PR", year=2020)

# descobrir as décadas únicas para gerar os gráficos lado a lado
decadas_unicas = sorted(gdf_pontos['decada'].dropna().unique())
num_decadas = len(decadas_unicas)

# Configurar a figura (1 linha, 'num_decadas' colunas)
fig, axes = plt.subplots(1, num_decadas, figsize=(6 * num_decadas, 8))

# Se houver apenas uma década, transforma 'axes' em lista para o loop 'for' funcionar
if num_decadas == 1:
    axes = [axes]

# 6. Renderizar o mapa para cada década
for ax, decada in zip(axes, decadas_unicas):
    # Desenhar o mapa base do PR em cinza
    pr_mapa.plot(ax=ax, color='lightgrey', edgecolor='white', linewidth=0.5)
    
    # Filtrar apenas os pontos pertencentes à década atual do loop
    gdf_filtrado = gdf_pontos[gdf_pontos['decada'] == decada]
    
    # Calcular o tamanho das bolhas (ajuste o divisor se ficarem muito grandes ou pequenas)
    tamanho_fam = gdf_filtrado['qtd_familias_bf_trab_infantil'] / 20
    #tamanho_pess = gdf_filtrado['qtd_pessoas_bf_trab_infantil'] / 20
    
    # Desenhar as bolhas
    gdf_filtrado.plot(
        ax=ax,
        color='red',
        markersize=tamanho_fam,
        alpha=0.6,
        edgecolor='darkred',
        linewidth=0.5
    )
    # gdf_filtrado.plot(
    #         ax=ax,
    #         color='green',
    #         markersize=tamanho_pess,
    #         alpha=0.6,
    #         edgecolor='darkgreen',
    #         linewidth=0.5
    #     )
    
    # Configurações de título e remoção de eixos do mapa atual
    ax.set_title(f"Década de {int(decada)}", fontsize=14)
    ax.set_axis_off()

# Título geral e exibição
plt.suptitle("Trabalho infantil no PR ao longo das décadas ", fontsize=18)
fig.text(0.5, 0.92, "Análise sobre famílias beneficiárias do Bolsa Família", ha='center', fontsize=12, color='dimgrey')
plt.tight_layout()
plt.show()