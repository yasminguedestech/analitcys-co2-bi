"""
Exporta os dados para CSV prontos para importar no Power BI.
Gera os arquivos em powerbi/export/ — basta abrir cada um no Power BI.
"""

import os
import sqlite3
import pandas as pd

DB  = os.path.join("data", "co2_corridas.db")
OUT = os.path.join("powerbi", "export")
os.makedirs(OUT, exist_ok=True)

conn = sqlite3.connect(DB)

tabelas = {
    "corridas": """
        SELECT
            id_corrida,
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
    """,

    "bairros": """
        SELECT id_bairro, nome, zona, lat, lon, populacao, area_km2
        FROM bairros
    """,

    "emissoes_por_bairro": """
        SELECT
            v.bairro,
            v.zona,
            b.lat,
            b.lon,
            v.total_corridas,
            v.co2_total_kg,
            ROUND(v.co2_total_kg / 1000, 4) AS co2_total_ton,
            v.co2_medio_kg,
            v.distancia_media_km
        FROM vw_emissoes_bairro v
        JOIN bairros b ON v.bairro = b.nome
    """,

    "emissoes_por_zona": """
        SELECT * FROM vw_emissoes_zona
    """,

    "potencial_reducao_ev": """
        SELECT
            bairro,
            zona,
            total_corridas,
            co2_total_kg,
            co2_projetado_kg,
            reducao_potencial_kg,
            reducao_pct
        FROM vw_potencial_reducao
    """,

    "co2_por_veiculo": """
        SELECT
            tipo_veiculo,
            COUNT(*)                        AS total_corridas,
            ROUND(SUM(co2_emitido_kg), 2)  AS co2_total_kg,
            ROUND(AVG(co2_emitido_kg), 4)  AS co2_medio_kg,
            ROUND(AVG(distancia_km), 2)    AS distancia_media_km
        FROM corridas
        GROUP BY tipo_veiculo
        ORDER BY co2_total_kg DESC
    """,

    "evolucao_semanal": """
        SELECT
            strftime('%Y-%W', data_hora)    AS semana,
            MIN(date(data_hora))            AS data_inicio_semana,
            COUNT(*)                        AS total_corridas,
            ROUND(SUM(co2_emitido_kg), 2)  AS co2_total_kg
        FROM corridas
        GROUP BY strftime('%Y-%W', data_hora)
        ORDER BY semana
    """,

    "co2_por_hora": """
        SELECT
            hora,
            COUNT(*)                        AS total_corridas,
            ROUND(SUM(co2_emitido_kg), 2)  AS co2_total_kg
        FROM corridas
        GROUP BY hora
        ORDER BY hora
    """,
}

for nome, query in tabelas.items():
    df = pd.read_sql(query.strip(), conn)
    caminho = os.path.join(OUT, f"{nome}.csv")
    df.to_csv(caminho, index=False, encoding="utf-8-sig")  # utf-8-sig para Excel/Power BI reconhecer acentos
    print(f"  {nome}.csv  ({len(df)} linhas)")

conn.close()
print(f"\nArquivos exportados em: {os.path.abspath(OUT)}")
print("Importe cada CSV no Power BI via: Obter dados > Texto/CSV")
