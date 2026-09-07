# Documentação: Pipeline de ETL e Inserção no Banco de Dados

## 1. Fonte dos Dados
**Dados Escolhidos:** Secretaria de Avaliação, Gestão da Informação e Cadastro Único (SAGICAD) - VIS DATA 3. 
Foram utilizados 6 arquivos `.csv` referentes ao estado do Paraná, combinando recortes temporais distintos para obter a maior faixa histórica possível.

## 2. Processo de ETL (Extração, Transformação e Carga)
Todo o tratamento e manipulação dos dados foi construído em Python, utilizando a biblioteca **Pandas**. O processo de limpeza (localizado no módulo `gerador_matches`) seguiu as seguintes etapas:

* **Merge e Identificação:** Os arquivos CSV foram unificados, utilizando as colunas `Data` e `Municipio` como chaves primárias da análise.
* **Tratamento de Duplicatas:** Durante a união dos arquivos (especificamente com dados de 2023), foram geradas linhas repetidas. Para garantir a integridade do banco, aplicamos a função `.drop_duplicates(subset=['Municipio', 'Data'])`, que identificou e removeu 399 registros duplicados.
* **Tipagem Inteligente (Int64):** Como o banco de dados exige números inteiros para contagens, convertemos as colunas numéricas para o tipo especial `Int64` do Pandas. Isso evitou que a biblioteca transformasse as colunas em `float` (decimais) e permitiu **preservar os valores nulos (`NaN`)**. A preservação dos nulos é uma regra de negócio importante, pois a ausência do dado significa que o parâmetro não foi mensurado naquele período, o que difere do valor zero.

## 3. Infraestrutura e Conexão (PostgreSQL)
A inserção no banco de dados PostGIS foi feita de forma automatizada via script (`connection.py`):

* **Segurança:** As credenciais de acesso foram isoladas em um arquivo `.env` gerido pela biblioteca `python-dotenv`.
* **Túnel SSH:** Para contornar as restrições de rede do servidor universitário (C3SL/UFPR), a conexão foi roteada através de um túnel SSH local (porta `5435`), utilizando a chave de segurança `.pem`.
* **Carga de Dados (Load):** Utilizamos a biblioteca **SQLAlchemy** (`create_engine`) em conjunto com o método `.to_sql()` do Pandas para criar a tabela `bd2_2556553` e inserir as mais de 67 mil tuplas diretamente no banco de dados.

## 4. Desempenho
* **Tempo de Execução da Consulta:** Após a inserção, foi realizado um teste de leitura dos dados no banco. O tempo médio de execução da query de verificação foi de **0.7344 segundos**.

## 5. Sobre os dados:
* Quanto à padronização:

Todos as colunas do tipo string (como nome do município) aparecem em letra maiúscula e acentuadas. Para que pudéssemos cruzar os dados com outras tabelas (como a de municípios do Paraná, disponibilizada pelo IBGE), apenas tivemos que modificar o nome das cidades que continham "D'OESTE" para "DOESTE". 

Todas as outras colunas possuíam valores numéricos inteiros e valores sem dados disponíveis como nulos.


* Todas as tabelas possuem listados TODOS os municípios do Paraná (não há NENHUM município faltante dos 399).

* A quantidade de valores nulos de cada uma das 40 colunas da nossa tabela foi registrada no arquivo "quantidade_nulos_por_coluna.csv".

* O tempo de execução da query "select * from db2_2556553" levou 2.38 segundos.