-- ============================================================================
-- Área a até 30 km de algum hospital (continuação da consulta 02: usa o CTE
-- cobertura; substituir o SELECT final por este). Camada de visualização.
-- ============================================================================
SELECT ST_Area(geom) / 1e6 AS area_km2, geom FROM cobertura;
