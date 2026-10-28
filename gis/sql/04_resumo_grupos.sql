-- ============================================================================
-- Resumo por grupo (continuação da consulta 02: usa o CTE acesso).
-- Compara municípios com e sem hospital no próprio território.
-- ============================================================================
SELECT (n_hosp_municipio > 0)                                           AS tem_hospital_no_municipio,
       count(*)                                                         AS municipios,
       round(avg(dist_hosp_km)::numeric, 1)                             AS dist_media_km,
       round((percentile_cont(0.5) WITHIN GROUP (ORDER BY dist_hosp_km))::numeric, 1) AS dist_mediana_km,
       round(avg(pct_area_ate_30km)::numeric, 3)                        AS pct_area_ate_30km,
       round(avg(pct_bf_inscritos)::numeric, 3)                         AS pct_bf_inscritos,
       round(avg(pct_ppi_cadunico)::numeric, 3)                         AS pct_ppi_cadunico,
       round(avg(pct_bf_pobreza)::numeric, 3)                           AS pct_bf_pobreza,
       round(sum(bf_pessoas)::numeric)                                  AS bf_pessoas_total
FROM acesso
GROUP BY 1
ORDER BY 1;
