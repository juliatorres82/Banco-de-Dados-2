# Esboço do artigo

**Título sugerido:** Geografia do acesso à internação pediátrica no Paraná: deslocamento, vulnerabilidade social e raça/cor (2024–2025)

**Pergunta central:** onde as crianças do Paraná são internadas, quem precisa sair do próprio município para isso, e esse deslocamento se associa à vulnerabilidade social e à raça/cor?

> Orçamento de páginas (modelo SBC, 8–12 pp.): Introdução 1 · Referencial 1 · Dados 1 · Metodologia 1,5 · Resultados 3–4 · Discussão 1,5 · Conclusão 0,5.
> Itens marcados com **[FAZER]** ainda não foram calculados ou escritos.

---

## Resumo / Abstract
Quatro frases: problema (deslocamento para internação pediátrica), dados (SIH/SUS, CadÚnico, Censo 2022, 399 municípios), método (integração, indicadores municipais, análise espacial em SIG), resultado principal e limitação. **Reescrever depois de fechar os resultados.**

## 1. Introdução
- Contexto: regionalização do SUS; internação pediátrica concentrada em poucos polos.
- Lacuna: pouco se sabe sobre **quem** sai do município e **quanto** se desloca, cruzando saúde, renda e raça/cor.
- Objetivo e perguntas (substituem as da seção 5 do rascunho):
  1. Qual a geografia dos fluxos de internação pediátrica no PR?
  2. O deslocamento se associa à vulnerabilidade social (Bolsa Família)?
  3. Crianças pretas, pardas e indígenas (PPI) são internadas e se deslocam de modo diferente das brancas?
- Contribuição: pipeline reprodutível + GeoPackage aberto.
- Roteiro das seções.

## 2. Referencial (curto)
Buscar e citar (não inventar referências; verificar cada uma):
- Acesso espacial à saúde e conceito de acesso (Penchansky & Thomas, 1981).
- Regionalização e Regiões de Saúde no SUS.
- Desigualdades raciais em saúde no Brasil e qualidade do registro de raça/cor no SIH.
- Análise de fluxos origem–destino (Nystuen–Dacey) e autocorrelação espacial (Moran, LISA/Anselin).
- Falácia ecológica.

## 3. Dados
Uma tabela com: fonte, unidade, período, linhas, variáveis usadas.

| Base | Fonte | Unidade | Período | Uso |
|---|---|---|---|---|
| Internações pediátricas | SIH/SUS (0–16 anos, PR) | AIH | 2022–2026 (usado: 2024–2025) | origem, destino, raça/cor, idade |
| CadÚnico / Bolsa Família | SAGICAD (VIS DATA 3) | município × mês | 2012–2026 | % crianças no PBF, % PPI |
| População | Censo 2022 (SIDRA 9606) | município | 2022 | denominadores por raça e idade |
| Municípios | IBGE / Base dos Dados | município | — | centroides, Regiões de Saúde |
| Malha municipal | IBGE via `geobr` | polígono | 2022 | camada `municipios` |

Pontos a registrar:
- 86.688 registros brutos de internação; **70.747** após limpeza.
- Cobertura do SIH desigual: 2022 tem 3 meses, 2023 tem 5, 2026 tem 1; só 2024 e 2025 têm 12 meses.
- **88%** das internações sem CID: diagnóstico fica fora da análise.
- Variáveis de renda do PBF mudam de série em março de 2023; trabalho infantil cai para ~20% de cobertura depois de 2023.
- Todos os 399 municípios presentes (README do projeto).

## 4. Metodologia
### 4.1 Integração e limpeza
Tabela com o registro de manipulações (`saida/00_registro_manipulacoes.csv`):
- remoção de 1.267 `id_aih` repetidos (linhas duplicadas e AIHs de continuação; mantido o mês mais antigo);
- recorte para 2024–2025 (−14.674 linhas);
- junção por código IBGE de 6 dígitos (`id_municipio_6`); no CadÚnico, nome em maiúsculas com `D'OESTE → DOESTE`;
- nulos preservados como nulos, não zeros (regra do projeto).
- Fecha a antiga seção "Problemas enfrentados" (cruzamento de códigos, busca por dados de saúde).

### 4.2 Variáveis derivadas
- `dist_km`: distância haversine entre centroides do município de residência e do hospital. **Quem é internado no próprio município tem 0 km.**
- `fora_municipio`, `fora_regiao_saude`, `fora_pr`, `mais_100km`.
- Grupo racial: PPI = preta + parda + indígena; Branca; Amarela; Sem informação.

### 4.3 Denominadores e taxas
- Taxa de internação = internações ÷ 2 anos ÷ população 0–16 anos × 1.000.
- Taxa por raça: mesma conta com a população 0–16 anos do grupo (Censo 2022).
- Razão de taxas PPI ÷ brancas, só em municípios com ≥ 20 internações em cada grupo (n = 169).
- Indicadores do CadÚnico = média mensal 2024–2025.

### 4.4 Análise espacial (SIG)
- Software: QGIS + Python (GeoPandas); GeoPackage em SIRGAS 2000 / UTM 22S (EPSG:31982).
- Camadas: `municipios`, `regioes_saude`, `polos_hospitalares`, `fluxos_od`, `fluxo_principal`.
- Mapas coropléticos; mapa de fluxos com destino principal por município; mapa bivariado 3×3.
- Regra de dados insuficientes: municípios com < 30 internações (ou < 20 por grupo racial) em cinza.

### 4.5 Estatística
- Correlação de Spearman (robusta a outliers), apenas municípios com ≥ 30 internações (n = 326).
- **[FAZER]** Moran global e LISA bivariado (GeoDa) para vulnerabilidade × saída do município.

### 4.6 Reprodutibilidade
- Repositório, scripts (`gis/preparacao.py`, `achados.py`, `gerar_geopackage.py`, `figuras*.py`), banco PostGIS `postgiscwb` (servidor BIGSEA/UTFPR) para as tabelas do CadÚnico.
- Dados do SIH mantidos localmente (base 3 do rascunho).

### 4.7 Limitações metodológicas
- Distância em linha reta entre sedes, não rota viária.
- Unidade ecológica (município): sem inferência individual.
- Raça/cor no SIH é registrada pelo hospital; no Censo e no CadÚnico é autodeclarada.
- Dados agregados e públicos; sem identificação de pacientes (CEP não usado).

## 5. Resultados
### 5.1 Panorama do deslocamento (Fig. 1, Fig. 7)
- 49,8% das internações ocorrem fora do município de residência; 15,1% fora da Região de Saúde; 10,6% a mais de 100 km; 0,56% fora do PR.
- Distância média 44 km (todas) e 88 km (só quem saiu; mediana 45 km).
- Metade dos municípios envia praticamente todas as crianças para fora.
- Polos: Curitiba 15.412 internações (21,8%), Campo Largo 5.968, Londrina 4.307, Maringá 3.656, Campina Grande do Sul 3.111.

### 5.2 Fluxos e regionalização (figura `fig_fluxo_principal`)
- Bacias de atendimento: Cascavel, Londrina/Maringá e Curitiba.
- Campo Largo: 91% das internações vêm de fora, de 284 municípios; **conferir no CNES antes de escrever**.
- Fluxos de longa distância convergem para Curitiba e Campo Largo.

### 5.3 Vulnerabilidade social e deslocamento (Fig. 4, Fig. 6)
- Mapa bivariado: 59 dos 109 municípios de maior proporção de crianças no PBF (54%) enviam 100% das crianças para fora, contra 37 dos 109 de menor proporção (34%).
- Spearman ρ = 0,29 (PBF × % fora) e 0,18 (PBF × taxa de internação): associação fraca.
- **[FAZER]** LISA bivariado para identificar clusters.

### 5.4 Raça/cor (Fig. 2, Fig. 3, Fig. 5)
- PPI = 34,6% das crianças (Censo) e 33,1% do CadÚnico, mas **27,1% das internações**.
- Taxa de internação: 11,1 por mil (PPI) contra 15,8 por mil (brancas).
- Razão PPI/branca < 1 em 75% dos 169 municípios comparáveis (mediana 0,68).
- Distância: crianças PPI percorrem menos (curva de distância acumulada à esquerda); dentro do mesmo município, 4,5 km a menos em mediana.
- Crianças indígenas: 84% internadas fora do município, mas só 6% fora da Região de Saúde (n = 220; cautela).

### 5.5 **[FAZER, opcional]** Sexo
- A base tem `sexo_paciente`; cobre a pergunta 5 do rascunho com pouco esforço.

## 6. Discussão
- Interpretação: a rede hospitalar pediátrica é muito concentrada; sair do município é regra para a maioria dos pequenos.
- **Duas leituras para a menor taxa PPI** (os dados não distinguem): barreira de acesso *ou* sub-registro de raça/cor no SIH. Propor teste futuro (comparar com mortalidade ou internações por causas sensíveis, se houver).
- Vulnerabilidade: associação fraca, não é regra; discutir exceções (ex.: RMC, onde há muitos hospitais próximos mesmo com saída alta).
- Campo Largo como hospital de referência.
- Implicações: regionalização, transporte sanitário, planejamento de leitos.
- Limitações (retomar 4.7) e ameaças à validade.

## 7. Conclusão e trabalhos futuros
- Respostas curtas às três perguntas.
- Futuro: tempo de viagem real (OpenStreetMap/ORS), LISA e Moran, diagnósticos (CID, hoje 88% ausente), geocodificação por CEP agregada, camada de Terras Indígenas (FUNAI), trabalho infantil.

## Referências
## Apêndice A — Tabela completa de manipulações
## Apêndice B — Dicionário das camadas do GeoPackage

---

## O que mudou em relação ao rascunho
| Pergunta do rascunho | Situação |
|---|---|
| 1. Distribuição do trabalho infantil | Não coberta nesta análise |
| 2. Trabalho infantil antes/depois do Bolsa Família | Não coberta |
| 3. Internações por renda | Coberta parcialmente (PBF, seção 5.3) |
| 4. Internações por cor | Coberta (seção 5.4) |
| 5. Internações por sexo | **[FAZER]** (seção 5.5) |
| 6. Perfil etário do PBF por década | Não coberta |

O rascunho apresenta três bases (PBF, trabalho infantil, internações). Se o foco passar a ser deslocamento e raça/cor, o resumo e o título precisam mudar, e o trabalho infantil vira variável secundária (ou trabalho futuro).
