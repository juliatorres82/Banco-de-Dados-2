-- ============================================================================
-- Correlação de Pearson entre acessibilidade e vulnerabilidade
-- (continuação da consulta 02: usa o CTE acesso). Spearman é calculado em Python.
-- ============================================================================
SELECT count(*)                                              AS municipios,
       round(corr(dist_hosp_km, pct_bf_inscritos)::numeric, 3)   AS dist_x_pbf,
       round(corr(dist_hosp_km, pct_ppi_cadunico)::numeric, 3)   AS dist_x_ppi,
       round(corr(dist_hosp_km, pct_bf_pobreza)::numeric, 3)     AS dist_x_pobreza,
       round(corr(pct_area_ate_30km, pct_bf_inscritos)::numeric, 3) AS cobertura_x_pbf,
       round(corr(pct_area_ate_30km, pct_ppi_cadunico)::numeric, 3) AS cobertura_x_ppi,
       round(corr(dist_hosp_infantil_km, pct_ppi_cadunico)::numeric, 3) AS dist_infantil_x_ppi
FROM acesso;
