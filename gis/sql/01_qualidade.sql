-- ============================================================================
-- Diagnóstico de qualidade das tabelas usadas (somente leitura).
-- Os comandos são separados por uma linha com o marcador de arroba duplo.
-- ============================================================================

-- (a) Funil de seleção dos hospitais em saude."saude_parana_CRM".
WITH base AS (
    SELECT DISTINCT ON (id_estab) id_estab, nome, lat, lng
    FROM saude."saude_parana_CRM"
    WHERE nome ~* '(hospital|santa casa|maternidade)'
    ORDER BY id_estab, crm
)
SELECT 1 AS ordem, 'Registros com nome de hospital' AS etapa,
       (SELECT count(*) FROM saude."saude_parana_CRM"
         WHERE nome ~* '(hospital|santa casa|maternidade)') AS n
UNION ALL SELECT 2, 'Estabelecimentos distintos (id_estab)', count(*) FROM base
UNION ALL SELECT 3, 'Excluídos: hospital-dia, estética, odontologia', count(*)
          FROM base WHERE nome ~* '(hospital[ -]dia|dia e cl[ií]nica|est[eé]tica|odonto)'
UNION ALL SELECT 4, 'Excluídos: coordenadas fora do Paraná', count(*)
          FROM base WHERE nome !~* '(hospital[ -]dia|dia e cl[ií]nica|est[eé]tica|odonto)'
                      AND NOT (lng BETWEEN -55 AND -48 AND lat BETWEEN -27 AND -22)
UNION ALL SELECT 5, 'Hospitais válidos', count(*)
          FROM base WHERE nome !~* '(hospital[ -]dia|dia e cl[ií]nica|est[eé]tica|odonto)'
                      AND lng BETWEEN -55 AND -48 AND lat BETWEEN -27 AND -22
ORDER BY 1;

-- @@

-- (b) SRID declarado x coordenadas reais da malha municipal.
SELECT ST_SRID(geom)                 AS srid_declarado,
       count(*)                      AS municipios,
       round(min(ST_XMin(geom))::numeric) AS x_min,
       round(max(ST_XMax(geom))::numeric) AS x_max,
       round(min(ST_YMin(geom))::numeric) AS y_min,
       round(max(ST_YMax(geom))::numeric) AS y_max
FROM public.bd2_ricardo_divisa_municipio_parana
GROUP BY 1;

-- @@

-- (c) Correspondência de nomes entre a malha e a tabela bd2_2556553.
SELECT count(*) FILTER (WHERE c."Municipio" IS NOT NULL) AS casam_sem_acento,
       count(*) FILTER (WHERE c."Municipio" IS NULL)     AS nao_casam
FROM public.bd2_ricardo_divisa_municipio_parana m
LEFT JOIN (SELECT DISTINCT "Municipio" FROM public.bd2_2556553) c
       ON UPPER(unaccent(REPLACE(m.nome, '''', ''))) = UPPER(unaccent(c."Municipio"));
