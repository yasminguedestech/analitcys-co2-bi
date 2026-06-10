import pandas as pd
import sqlite3

DB = r"C:\Users\Yasmin Guedes\OneDrive\Documentos\project\analitcys-co2-bi\data\co2_corridas.db"

conn = sqlite3.connect(DB)

# Tabela principal de corridas
corridas = pd.read_sql("""
    SELECT
        id_corrida,
        id_bairro_origem,
        data_hora,
        tipo_veiculo,
        distancia_km,
        duracao_min,
        co2_emitido_g,
        co2_emitido_kg,
        mes,
        mes_num,
        dia_semana,
        hora,
        bairro_origem,
        zona_origem,
        lat_origem,
        lon_origem
    FROM corridas
""", conn, parse_dates=["data_hora"])

# Tabela de bairros (dimensão geográfica)
bairros = pd.read_sql("""
    SELECT id_bairro, nome, zona, lat, lon, populacao, area_km2
    FROM bairros
""", conn)

# Agregado por bairro (pronto para visuais de mapa e ranking)
emissoes_bairro = pd.read_sql("""
    SELECT
        bairro,
        zona,
        total_corridas,
        co2_total_kg,
        ROUND(co2_total_kg / 1000, 4)                              AS co2_total_ton,
        co2_medio_kg,
        distancia_media_km
    FROM vw_emissoes_bairro
""", conn)

# Junta coordenadas ao agregado de bairros
emissoes_bairro = emissoes_bairro.merge(
    bairros[["nome", "lat", "lon"]].rename(columns={"nome": "bairro"}),
    on="bairro", how="left"
)

# Agregado por zona
emissoes_zona = pd.read_sql("SELECT * FROM vw_emissoes_zona", conn)

# Potencial de redução com 30 % de frota elétrica
potencial_ev = pd.read_sql("""
    SELECT
        bairro,
        zona,
        total_corridas,
        co2_total_kg,
        co2_projetado_kg,
        reducao_potencial_kg,
        reducao_pct
    FROM vw_potencial_reducao
""", conn)

# CO2 por tipo de veículo
co2_veiculo = pd.read_sql("""
    SELECT
        tipo_veiculo,
        COUNT(*)                          AS total_corridas,
        ROUND(SUM(co2_emitido_kg), 2)    AS co2_total_kg,
        ROUND(AVG(co2_emitido_kg), 4)    AS co2_medio_kg,
        ROUND(AVG(distancia_km), 2)      AS distancia_media_km
    FROM corridas
    GROUP BY tipo_veiculo
    ORDER BY co2_total_kg DESC
""", conn)

# Evolução semanal (para gráfico de linha)
evolucao_semanal = pd.read_sql("""
    SELECT
        strftime('%Y-%W', data_hora)     AS semana,
        MIN(data_hora)                   AS data_inicio_semana,
        COUNT(*)                         AS total_corridas,
        ROUND(SUM(co2_emitido_kg), 2)   AS co2_total_kg
    FROM corridas
    GROUP BY strftime('%Y-%W', data_hora)
    ORDER BY semana
""", conn, parse_dates=["data_inicio_semana"])

conn.close()
