-- ================================================================
-- Queries Analíticas: CO₂ por Bairro · 99 São Paulo
-- ================================================================

-- 1. Resumo executivo
SELECT
    COUNT(*)                                        AS total_corridas,
    ROUND(SUM(co2_emitido_kg), 1)                  AS co2_total_kg,
    ROUND(SUM(co2_emitido_kg) / 1000, 3)           AS co2_total_ton,
    ROUND(AVG(co2_emitido_kg), 3)                  AS co2_medio_kg_corrida,
    ROUND(AVG(distancia_km), 2)                    AS dist_media_km,
    COUNT(DISTINCT bairro_origem)                  AS bairros_atendidos,
    SUM(CASE WHEN distancia_km < 5 THEN 1 ELSE 0 END) AS corridas_curtas_lt5km
FROM corridas;

-- ─────────────────────────────────────────────────────────────────────────────

-- 2. Top 10 bairros por CO₂ total
SELECT
    bairro,
    zona,
    total_corridas,
    co2_total_kg,
    ROUND(co2_total_kg / 1000, 4) AS co2_total_ton,
    distancia_media_km
FROM vw_emissoes_bairro
LIMIT 10;

-- ─────────────────────────────────────────────────────────────────────────────

-- 3. CO₂ por zona
SELECT * FROM vw_emissoes_zona;

-- ─────────────────────────────────────────────────────────────────────────────

-- 4. CO₂ por tipo de veículo
SELECT
    tipo_veiculo,
    COUNT(*)                                AS total_corridas,
    ROUND(SUM(co2_emitido_kg), 2)          AS co2_total_kg,
    ROUND(AVG(co2_emitido_kg), 4)          AS co2_medio_kg,
    ROUND(AVG(distancia_km), 2)            AS distancia_media_km,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM corridas), 1) AS participacao_pct
FROM corridas
GROUP BY tipo_veiculo
ORDER BY co2_total_kg DESC;

-- ─────────────────────────────────────────────────────────────────────────────

-- 5. Evolução mensal do CO₂
SELECT
    mes_num,
    mes,
    COUNT(*)                               AS total_corridas,
    ROUND(SUM(co2_emitido_kg), 2)         AS co2_total_kg
FROM corridas
GROUP BY mes_num, mes
ORDER BY mes_num;

-- ─────────────────────────────────────────────────────────────────────────────

-- 6. Emissões por hora do dia (pico de demanda)
SELECT
    hora,
    COUNT(*)                               AS total_corridas,
    ROUND(SUM(co2_emitido_kg) / 1000, 3) AS co2_total_ton
FROM corridas
GROUP BY hora
ORDER BY hora;

-- ─────────────────────────────────────────────────────────────────────────────

-- 7. Corridas curtas por bairro (< 5 km) — alto potencial de substituição
SELECT
    bairro_origem                          AS bairro,
    zona_origem                            AS zona,
    COUNT(*)                               AS corridas_curtas,
    ROUND(SUM(co2_emitido_kg), 2)         AS co2_curtas_kg,
    ROUND(AVG(distancia_km), 2)           AS dist_media_km
FROM corridas
WHERE distancia_km < 5
GROUP BY bairro_origem, zona_origem
ORDER BY corridas_curtas DESC
LIMIT 15;

-- ─────────────────────────────────────────────────────────────────────────────

-- 8. Onde reduzir? — Potencial com 30 % de frota elétrica
--    Prioridade: bairros com maior CO₂ e maior volume de corridas
SELECT
    bairro,
    zona,
    total_corridas,
    co2_total_kg                           AS co2_atual_kg,
    co2_projetado_kg,
    reducao_potencial_kg,
    reducao_pct || ' %'                    AS reducao_estimada,
    -- Score de prioridade: quanto maior, mais urgente a intervenção
    ROUND(co2_total_kg * total_corridas / 1000, 0) AS score_prioridade
FROM vw_potencial_reducao
ORDER BY score_prioridade DESC
LIMIT 15;

-- ─────────────────────────────────────────────────────────────────────────────

-- 9. Ranking completo de bairros
SELECT
    ROW_NUMBER() OVER (ORDER BY co2_total_kg DESC) AS ranking,
    bairro,
    zona,
    total_corridas,
    co2_total_kg,
    distancia_media_km
FROM vw_emissoes_bairro;
