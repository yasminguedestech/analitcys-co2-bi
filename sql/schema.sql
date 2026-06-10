-- ================================================================
-- Esquema: Emissões CO₂ · Corridas 99 por Bairro — São Paulo
-- ================================================================
-- Fator de emissão REAL:  155 g CO₂/km  (ICCT Brasil, 2023)
-- Fórmula de cálculo:     CETESB
-- CO₂ (g) = distância(km) × 155
--
-- ⚠  As corridas são SIMULADAS — a 99 não disponibiliza os dados.
--    Este projeto aplica fatores de emissão reais a corridas simuladas.
-- ================================================================

CREATE TABLE IF NOT EXISTS bairros (
    id_bairro    INTEGER PRIMARY KEY,
    nome         TEXT    NOT NULL,
    zona         TEXT    NOT NULL,  -- Centro, Sul, Norte, Leste, Oeste
    lat          REAL,
    lon          REAL,
    populacao    INTEGER,
    area_km2     REAL,
    peso_demanda REAL    -- fator de demanda relativa de corridas
);

CREATE TABLE IF NOT EXISTS corridas (
    id_corrida       INTEGER PRIMARY KEY,
    id_bairro_origem INTEGER NOT NULL REFERENCES bairros(id_bairro),
    data_hora        TEXT    NOT NULL,
    tipo_veiculo     TEXT    NOT NULL
                     CHECK(tipo_veiculo IN ('Pop','Econômico','Comfort','Black')),
    distancia_km     REAL    NOT NULL CHECK(distancia_km > 0),
    duracao_min      REAL    NOT NULL,
    co2_emitido_g    REAL    NOT NULL,  -- distancia_km × 155 g/km
    co2_emitido_kg   REAL    NOT NULL,
    mes              TEXT,
    mes_num          INTEGER,
    dia_semana       TEXT,
    hora             INTEGER,
    bairro_origem    TEXT,
    zona_origem      TEXT,
    lat_origem       REAL,
    lon_origem       REAL
);

-- ── Views de análise ────────────────────────────────────────────────────────

CREATE VIEW IF NOT EXISTS vw_emissoes_bairro AS
SELECT
    b.nome                                      AS bairro,
    b.zona,
    COUNT(c.id_corrida)                         AS total_corridas,
    ROUND(SUM(c.co2_emitido_kg),    2)          AS co2_total_kg,
    ROUND(SUM(c.co2_emitido_kg)/1000, 4)        AS co2_total_ton,
    ROUND(AVG(c.co2_emitido_kg),    4)          AS co2_medio_kg,
    ROUND(AVG(c.distancia_km),      2)          AS distancia_media_km
FROM corridas c
JOIN bairros b ON c.id_bairro_origem = b.id_bairro
GROUP BY b.id_bairro, b.nome, b.zona
ORDER BY co2_total_kg DESC;

CREATE VIEW IF NOT EXISTS vw_emissoes_zona AS
SELECT
    b.zona,
    COUNT(c.id_corrida)                         AS total_corridas,
    ROUND(SUM(c.co2_emitido_kg),    2)          AS co2_total_kg,
    ROUND(AVG(c.co2_emitido_kg),    4)          AS co2_medio_kg,
    ROUND(AVG(c.distancia_km),      2)          AS distancia_media_km
FROM corridas c
JOIN bairros b ON c.id_bairro_origem = b.id_bairro
GROUP BY b.zona
ORDER BY co2_total_kg DESC;

-- Potencial com 30 % da frota elétrica
-- EV Brasil: ~20 g CO₂/km (matriz elétrica majoritariamente renovável)
-- Redução por corrida EV: (155 - 20) / 155 ≈ 87 %
CREATE VIEW IF NOT EXISTS vw_potencial_reducao AS
SELECT
    bairro,
    zona,
    total_corridas,
    co2_total_kg,
    ROUND(co2_total_kg * (1 - 0.30 * (155.0 - 20.0) / 155.0), 2)  AS co2_projetado_kg,
    ROUND(co2_total_kg * 0.30 * (155.0 - 20.0) / 155.0, 2)         AS reducao_potencial_kg,
    ROUND(0.30 * (155.0 - 20.0) / 155.0 * 100, 1)                   AS reducao_pct
FROM vw_emissoes_bairro
ORDER BY reducao_potencial_kg DESC;
