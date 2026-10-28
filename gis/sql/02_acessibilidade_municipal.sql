-- ============================================================================
-- Consulta principal: acessibilidade hospitalar x vulnerabilidade social
-- por município do Paraná.
--
-- Tabelas correlacionadas:
--   public.bd2_2556553                           (CadÚnico/PBF, município x mês)  <- tabela do grupo
--   public.bd2_ricardo_divisa_municipio_parana   (polígonos municipais, SRID 4326)
--   saude."saude_parana_CRM"                     (estabelecimentos de saúde, SRID 4326)
--
-- Funções GIS: ST_Transform, ST_SetSRID, ST_PointOnSurface, ST_Within, ST_DWithin, ST_Distance,
--              operador KNN <->, ST_MakeLine, ST_Buffer, ST_Union, ST_Intersection, ST_Area.
-- Sistema de referência das medidas: SAD 69 / UTM 22S (EPSG:29192), em metros.
--   Obs.: a coluna geom de bd2_ricardo_divisa_municipio_parana declara SRID 4326, mas as
--   coordenadas estão em metros (x 136 mil a 800 mil). Por isso usamos ST_SetSRID (que só
--   corrige o rótulo) em vez de ST_Transform. Testado também com 31982: resultados idênticos.
-- Somente leitura (nenhum DDL).
-- ============================================================================
WITH
-- 1) Hospitais válidos: um registro por estabelecimento (a tabela traz cada
--    id_estab duplicado), nome de hospital, exclui hospital-dia/estética/odonto
--    e coordenadas fora do retângulo do Paraná.
--    O filtro de coordenadas é materializado ANTES da projeção: sem isso o
--    planejador pode executar ST_Transform sobre pontos inválidos (ex.: -51765)
--    e abortar a consulta.
hosp_filtrado AS MATERIALIZED (
    SELECT DISTINCT ON (c.id_estab)
           c.id_estab, c.crm, c.nome, c.cidade, c.geom
    FROM saude."saude_parana_CRM" c
    WHERE c.nome ~* '(hospital|santa casa|maternidade)'
      AND c.nome !~* '(hospital[ -]dia|dia e cl[ií]nica|est[eé]tica|odonto)'
      AND c.lng BETWEEN -55 AND -48
      AND c.lat BETWEEN -27 AND -22
    ORDER BY c.id_estab, c.crm
),
hosp AS MATERIALIZED (
    SELECT id_estab, nome, cidade,
           ST_Transform(geom, 29192) AS geom,
           (nome ~* '(infantil|pedi[aá]tric|pequeno pr[ií]ncipe)') AS infantil
    FROM hosp_filtrado
),

-- 2) Municípios: polígono e ponto de referência (sempre dentro do polígono).
--    MATERIALIZED: projeta uma vez por geometria, não a cada par município x hospital.
mun AS MATERIALIZED (
    SELECT m.codibge,
           m.nome,
           UPPER(unaccent(REPLACE(m.nome, '''', ''))) AS chave,
           ST_SetSRID(m.geom, 29192)                      AS geom,
           ST_PointOnSurface(ST_SetSRID(m.geom, 29192))   AS sede
    FROM public.bd2_ricardo_divisa_municipio_parana m
),

-- 3) Grafias que divergem entre a malha e o CadÚnico, mesmo sem acentos.
grafia(chave_malha, chave_cadunico) AS (
    VALUES ('PINHAL DO SAO BENTO', 'PINHAL DE SAO BENTO'),
           ('MUNHOZ DE MELLO',     'MUNHOZ DE MELO')
),

-- 4) Área a até 30 km de algum hospital (união dos círculos de 30 km).
cobertura AS (
    SELECT ST_Union(ST_Buffer(geom, 30000)) AS geom FROM hosp
),

-- 5) CadÚnico/PBF 2024-2025: razões calculadas mês a mês e depois médias.
--    PBF = pobreza + baixa renda + acima de 1/2 salário mínimo (100% de cobertura);
--    só entram meses em que as colunas de raça/cor existem (abril/2025 não tem).
cad AS (
    SELECT UPPER(unaccent("Municipio")) AS chave,
           count(*)                                    AS meses,
           avg(bf)                                     AS bf_pessoas,
           avg(bf::numeric   / NULLIF(inscritos, 0))   AS pct_bf_inscritos,
           avg(ppi::numeric  / NULLIF(inscritos, 0))   AS pct_ppi_cadunico,
           avg(pobreza::numeric / NULLIF(bf, 0))       AS pct_bf_pobreza
    FROM (
        SELECT "Municipio",
               "Pessoas beneficiarias BF em pobreza"                                  AS pobreza,
               "Pessoas beneficiarias BF em pobreza"
                 + "Pessoas beneficiarias BF em baixa renda"
                 + "Pessoas beneficiarias BF renda per capita maior meio salario minimo" AS bf,
               "Beneficiarios CadUnico brancos" + "Beneficiarios CadUnico pretos"
                 + "Beneficiarios CadUnico amarelos" + "Beneficiarios CadUnico pardos"
                 + "Beneficiarios CadUnico indigenas"
                 + "Beneficiarios CadUnico sem informacao raca/cor"                   AS inscritos,
               "Beneficiarios CadUnico pretos" + "Beneficiarios CadUnico pardos"
                 + "Beneficiarios CadUnico indigenas"                                 AS ppi
        FROM public.bd2_2556553
        WHERE RIGHT("Data", 4) IN ('2024', '2025')
          AND "Beneficiarios CadUnico brancos" IS NOT NULL
          AND "Pessoas beneficiarias BF em pobreza" IS NOT NULL
    ) t
    GROUP BY 1
),

-- 6) Indicadores por município: acessibilidade (PostGIS) + vulnerabilidade (bd2_2556553).
acesso AS (
    SELECT m.codibge,
           m.nome,
           -- acessibilidade (PostGIS)
           (SELECT count(*) FROM hosp h WHERE ST_Within(h.geom, m.geom))        AS n_hosp_municipio,
           (SELECT count(*) FROM hosp h WHERE ST_DWithin(h.geom, m.sede, 30000)) AS n_hosp_30km,
           nn.id_estab                                                          AS id_hosp_proximo,
           nn.nome                                                              AS hosp_proximo,
           nn.cidade                                                            AS cidade_hosp_proximo,
           nn.dist_km                                                           AS dist_hosp_km,
           ni.nome                                                              AS hosp_infantil_proximo,
           ni.dist_km                                                           AS dist_hosp_infantil_km,
           ST_Area(ST_Intersection(m.geom, cob.geom)) / ST_Area(m.geom)         AS pct_area_ate_30km,
           -- vulnerabilidade (tabela bd2_2556553)
           cad.meses, cad.bf_pessoas, cad.pct_bf_inscritos, cad.pct_ppi_cadunico, cad.pct_bf_pobreza,
           -- geometrias para o QGIS (EPSG:29192)
           m.geom, m.sede, nn.linha
    FROM mun m
    CROSS JOIN cobertura cob
    CROSS JOIN LATERAL (                       -- hospital mais próximo (vizinho mais próximo, KNN)
        SELECT h.id_estab, h.nome, h.cidade,
               ST_Distance(m.sede, h.geom) / 1000 AS dist_km,
               ST_MakeLine(m.sede, h.geom)        AS linha
        FROM hosp h
        ORDER BY m.sede <-> h.geom
        LIMIT 1
    ) nn
    CROSS JOIN LATERAL (                       -- hospital infantil mais próximo
        SELECT h.nome, ST_Distance(m.sede, h.geom) / 1000 AS dist_km
        FROM hosp h
        WHERE h.infantil
        ORDER BY m.sede <-> h.geom
        LIMIT 1
    ) ni
    LEFT JOIN grafia g ON g.chave_malha = m.chave
    LEFT JOIN cad      ON cad.chave = COALESCE(g.chave_cadunico, m.chave)
)

-- @@FINAL@@
SELECT * FROM acesso ORDER BY nome;
