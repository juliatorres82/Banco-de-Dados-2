-- ============================================================================
-- Camada de hospitais com conferência espacial (continuação da consulta 02:
-- usa os CTEs hosp e mun; substituir o SELECT final por este).
-- Junção espacial: em que município (polígono) cai cada hospital?
-- ============================================================================
SELECT h.id_estab,
       h.nome,
       h.cidade,
       h.infantil,
       m.codibge                                                   AS codibge_poligono,
       m.nome                                                      AS municipio_poligono,
       (UPPER(unaccent(m.nome)) = UPPER(unaccent(h.cidade)))       AS nome_confere,
       h.geom
FROM hosp h
LEFT JOIN mun m ON ST_Within(h.geom, m.geom)
ORDER BY h.id_estab;
