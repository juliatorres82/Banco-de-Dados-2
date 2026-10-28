# Análise espacial: deslocamento para internação pediátrica e raça/cor (PR, 2024–2025)

```
python gis/achados.py            # tabelas dos achados -> gis/saida/*.csv
python gis/gerar_geopackage.py   # camadas para o QGIS -> gis/saida/internacoes_pediatricas_pr.gpkg
```

Dependências: `pandas`, `geopandas`, `pyogrio`, `geobr`. Na primeira execução, a população
do Censo 2022 (SIDRA, tabela 9606) é baixada e salva em `Datasets/censo2022_pop_raca_idade_pr.csv`.

Todas as manipulações estão em `preparacao.py` e são listadas, com contagem de linhas,
em `saida/00_registro_manipulacoes.csv`.

## Camadas do GeoPackage (EPSG:31982, SIRGAS 2000 / UTM 22S)

| Camada | Geometria | Uso no QGIS |
|---|---|---|
| `municipios` | polígono | coropléticos (taxa de internação, % fora do município, % crianças no PBF, % PPI, razões raciais); LISA no GeoDa |
| `regioes_saude` | polígono | mesmo, agregado nas 22 Regiões de Saúde |
| `polos_hospitalares` | ponto | símbolos proporcionais a `internacoes_recebidas` |
| `fluxos_od` | linha | espessura por `internacoes` (estilo *graduado*); filtrar `internacoes >= 10` para legibilidade |
| `fluxo_principal` | linha | destino dominante de cada município: revela a regionalização "real" |

## Cuidados

- Proporções e razões de municípios pequenos são instáveis. Antes de mapear razões raciais,
  filtre `int_ppi >= 20 AND int_branca >= 20` (ou use suavização bayesiana empírica no GeoDa).
- `dist_km` é linha reta entre centroides municipais; quem é internado no próprio município tem 0 km.
- Análise ecológica (unidade = município): não permite conclusões sobre indivíduos.
- Raça/cor no SIH é registrada pelo hospital (heteroatribuição); no Censo e no CadÚnico, por autodeclaração.
