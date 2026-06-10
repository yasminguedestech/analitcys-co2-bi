"""
Gerador de dados simulados — Emissões CO₂ · 99 São Paulo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dados REAIS usados:
  • Fator de emissão: 155 g CO₂/km  (ICCT Brasil, 2023)
  • Fórmula de cálculo: CETESB
  • CO₂(g) = distância(km) × 155

Dados SIMULADOS:
  • As corridas em si — a 99 não disponibiliza esses dados publicamente.
    Esta simulação usa distribuição realista de demanda por bairro,
    horário e tipo de veículo.
"""

import pandas as pd
import numpy as np
import sqlite3
import os

np.random.seed(42)

# ── Constantes ────────────────────────────────────────────────────────────────
FATOR_EMISSAO_G_KM = 155
N_CORRIDAS         = 10_000
DATA_INICIO        = pd.Timestamp("2024-01-01")
DATA_FIM           = pd.Timestamp("2024-03-31")

# ── Distribuição horária realista (pico manhã 7-9h e tarde 17-20h) ────────────
PESOS_HORA = np.array([
    0.25, 0.20, 0.18, 0.18, 0.20, 0.50,  # 0-5h  (madrugada)
    0.85, 2.60, 2.90, 2.10, 1.20, 1.10,  # 6-11h (rush manhã)
    1.50, 1.40, 1.10, 1.10, 1.25, 2.40,  # 12-17h (almoço + tarde)
    2.90, 2.70, 1.90, 1.40, 1.00, 0.55,  # 18-23h (rush noite)
])
PESOS_HORA = PESOS_HORA / PESOS_HORA.sum()

# Modificador de distância por zona (Zona Sul mais distante do centro)
DIST_MOD_ZONA = {
    "Centro": 0.72,
    "Sul":    1.28,
    "Oeste":  1.05,
    "Leste":  0.88,
    "Norte":  0.82,
}

# ── Bairros de São Paulo ──────────────────────────────────────────────────────
BAIRROS_RAW = [
    (1,  "Pinheiros",      "Oeste",   -23.5636, -46.6770, 68000,  3.1,  1.5),
    (2,  "Itaim Bibi",     "Sul",     -23.5857, -46.6772, 89000,  3.7,  1.8),
    (3,  "Vila Mariana",   "Sul",     -23.5896, -46.6395, 110000, 6.8,  1.3),
    (4,  "Moema",          "Sul",     -23.6016, -46.6634, 73000,  4.4,  1.6),
    (5,  "Jardins",        "Oeste",   -23.5630, -46.6543, 42000,  2.8,  1.7),
    (6,  "Consolação",     "Centro",  -23.5505, -46.6561, 41000,  2.0,  1.2),
    (7,  "Santa Cecília",  "Centro",  -23.5440, -46.6523, 38000,  1.5,  1.1),
    (8,  "Bela Vista",     "Centro",  -23.5602, -46.6451, 61000,  2.9,  1.1),
    (9,  "Liberdade",      "Centro",  -23.5622, -46.6336, 80000,  2.7,  1.0),
    (10, "Morumbi",        "Sul",     -23.6178, -46.7194, 45000,  14.0, 1.9),
    (11, "Santo Amaro",    "Sul",     -23.6545, -46.7101, 82000,  5.6,  1.2),
    (12, "Campo Belo",     "Sul",     -23.6143, -46.6683, 55000,  3.4,  1.4),
    (13, "Brooklin",       "Sul",     -23.6165, -46.6942, 48000,  2.9,  1.6),
    (14, "Vila Olímpia",   "Sul",     -23.5975, -46.6862, 18000,  1.9,  2.1),
    (15, "Perdizes",       "Oeste",   -23.5374, -46.6722, 80000,  3.6,  1.1),
    (16, "Lapa",           "Oeste",   -23.5261, -46.7064, 70000,  3.1,  1.0),
    (17, "Barra Funda",    "Oeste",   -23.5252, -46.6601, 18000,  1.8,  1.3),
    (18, "Tatuapé",        "Leste",   -23.5396, -46.5730, 85000,  3.8,  1.0),
    (19, "Mooca",          "Leste",   -23.5572, -46.5969, 77000,  4.8,  0.9),
    (20, "Penha",          "Leste",   -23.5228, -46.5326, 112000, 5.4,  0.8),
    (21, "Santana",        "Norte",   -23.5017, -46.6270, 98000,  3.5,  1.1),
    (22, "Tucuruvi",       "Norte",   -23.4791, -46.6116, 78000,  5.9,  0.7),
    (23, "Pirituba",       "Norte",   -23.4754, -46.7280, 97000,  12.1, 0.7),
    (24, "Casa Verde",     "Norte",   -23.5074, -46.6621, 88000,  4.2,  0.8),
    (25, "Água Rasa",      "Leste",   -23.5576, -46.5619, 66000,  2.9,  0.8),
    (26, "Vila Prudente",  "Leste",   -23.5885, -46.5786, 95000,  7.1,  0.7),
    (27, "Jabaquara",      "Sul",     -23.6527, -46.6476, 90000,  7.6,  0.8),
    (28, "Ipiranga",       "Sul",     -23.5867, -46.6003, 104000, 6.7,  0.9),
    (29, "Sacomã",         "Sul",     -23.6102, -46.5984, 121000, 6.9,  0.7),
    (30, "Sé",             "Centro",  -23.5504, -46.6339, 23000,  1.3,  1.0),
]

COLS_BAIRROS = ["id_bairro", "nome", "zona", "lat", "lon",
                "populacao", "area_km2", "peso_demanda"]

TIPOS_VEICULO = {
    "Pop":       {"peso": 0.45, "dist_media": 7.2,  "dist_std": 3.5},
    "Econômico": {"peso": 0.30, "dist_media": 9.5,  "dist_std": 4.8},
    "Comfort":   {"peso": 0.18, "dist_media": 12.3, "dist_std": 5.9},
    "Black":     {"peso": 0.07, "dist_media": 15.1, "dist_std": 7.2},
}


def gerar_corridas(df_bairros: pd.DataFrame) -> pd.DataFrame:
    pesos_bairro = df_bairros["peso_demanda"] / df_bairros["peso_demanda"].sum()
    tipos        = list(TIPOS_VEICULO.keys())
    pesos_tipo   = [TIPOS_VEICULO[t]["peso"] for t in tipos]

    # Timestamps com distribuição realista por hora do dia
    n_dias = (DATA_FIM - DATA_INICIO).days + 1
    dias   = np.random.randint(0, n_dias, N_CORRIDAS)
    horas  = np.random.choice(np.arange(24), size=N_CORRIDAS, p=PESOS_HORA)
    mins   = np.random.randint(0, 60, N_CORRIDAS)
    timestamps = (DATA_INICIO
                  + pd.to_timedelta(dias,  unit="D")
                  + pd.to_timedelta(horas, unit="h")
                  + pd.to_timedelta(mins,  unit="min"))

    # Bairros de origem
    ids_origem = np.random.choice(
        df_bairros["id_bairro"].values, size=N_CORRIDAS, p=pesos_bairro.values
    )

    # Tipos de veículo
    tipos_escolhidos = np.random.choice(tipos, size=N_CORRIDAS, p=pesos_tipo)

    # Mapa bairro → zona para modificador de distância
    bairro_zona = dict(zip(df_bairros["id_bairro"], df_bairros["zona"]))
    zona_mods   = np.array([DIST_MOD_ZONA[bairro_zona[i]] for i in ids_origem])

    # Distâncias por tipo de veículo × modificador de zona
    distancias = np.array([
        max(0.5, np.random.normal(TIPOS_VEICULO[t]["dist_media"], TIPOS_VEICULO[t]["dist_std"]))
        for t in tipos_escolhidos
    ]) * zona_mods

    co2_g  = distancias * FATOR_EMISSAO_G_KM
    co2_kg = co2_g / 1000
    duracao = distancias * np.random.uniform(2.0, 4.0, N_CORRIDAS)

    corridas = pd.DataFrame({
        "id_corrida":       range(1, N_CORRIDAS + 1),
        "id_bairro_origem": ids_origem,
        "data_hora":        timestamps,
        "tipo_veiculo":     tipos_escolhidos,
        "distancia_km":     distancias.round(2),
        "duracao_min":      duracao.round(1),
        "co2_emitido_g":    co2_g.round(1),
        "co2_emitido_kg":   co2_kg.round(4),
    })

    corridas["mes"]        = corridas["data_hora"].dt.month_name()
    corridas["mes_num"]    = corridas["data_hora"].dt.month
    corridas["dia_semana"] = corridas["data_hora"].dt.day_name()
    corridas["hora"]       = corridas["data_hora"].dt.hour

    corridas = corridas.merge(
        df_bairros[["id_bairro", "nome", "zona", "lat", "lon"]].rename(columns={
            "id_bairro": "id_bairro_origem",
            "nome":      "bairro_origem",
            "zona":      "zona_origem",
            "lat":       "lat_origem",
            "lon":       "lon_origem",
        }),
        on="id_bairro_origem", how="left",
    )
    return corridas


def salvar_dados(corridas: pd.DataFrame, df_bairros: pd.DataFrame) -> None:
    os.makedirs("data", exist_ok=True)
    corridas.to_csv("data/corridas.csv", index=False)
    df_bairros.to_csv("data/bairros.csv", index=False)

    conn = sqlite3.connect("data/co2_corridas.db")
    df_bairros.to_sql("bairros",  conn, if_exists="replace", index=False)
    corridas.to_sql("corridas", conn, if_exists="replace", index=False)

    conn.executescript("""
        DROP VIEW IF EXISTS vw_emissoes_bairro;
        CREATE VIEW vw_emissoes_bairro AS
        SELECT
            b.nome                                   AS bairro,
            b.zona,
            COUNT(c.id_corrida)                      AS total_corridas,
            ROUND(SUM(c.co2_emitido_kg), 2)          AS co2_total_kg,
            ROUND(SUM(c.co2_emitido_kg) / 1000, 4)  AS co2_total_ton,
            ROUND(AVG(c.co2_emitido_kg), 4)          AS co2_medio_kg,
            ROUND(AVG(c.distancia_km),   2)          AS distancia_media_km
        FROM corridas c
        JOIN bairros b ON c.id_bairro_origem = b.id_bairro
        GROUP BY b.id_bairro, b.nome, b.zona
        ORDER BY co2_total_kg DESC;

        DROP VIEW IF EXISTS vw_emissoes_zona;
        CREATE VIEW vw_emissoes_zona AS
        SELECT
            b.zona,
            COUNT(c.id_corrida)                      AS total_corridas,
            ROUND(SUM(c.co2_emitido_kg), 2)          AS co2_total_kg,
            ROUND(AVG(c.co2_emitido_kg), 4)          AS co2_medio_kg,
            ROUND(AVG(c.distancia_km),   2)          AS distancia_media_km
        FROM corridas c
        JOIN bairros b ON c.id_bairro_origem = b.id_bairro
        GROUP BY b.zona
        ORDER BY co2_total_kg DESC;

        DROP VIEW IF EXISTS vw_potencial_reducao;
        CREATE VIEW vw_potencial_reducao AS
        SELECT
            bairro, zona, total_corridas, co2_total_kg,
            ROUND(co2_total_kg * (1 - 0.30 * (155.0 - 20.0) / 155.0), 2) AS co2_projetado_kg,
            ROUND(co2_total_kg * 0.30 * (155.0 - 20.0) / 155.0, 2)        AS reducao_potencial_kg,
            ROUND(0.30 * (155.0 - 20.0) / 155.0 * 100, 1)                  AS reducao_pct
        FROM vw_emissoes_bairro
        ORDER BY reducao_potencial_kg DESC;
    """)
    conn.commit()
    conn.close()

    co2_ton = corridas["co2_emitido_kg"].sum() / 1000
    print(f"OK  {len(corridas):,} corridas geradas  |  {co2_ton:.2f} ton CO2 total")
    print("    data/corridas.csv  |  data/bairros.csv  |  data/co2_corridas.db")


if __name__ == "__main__":
    df_bairros = pd.DataFrame(BAIRROS_RAW, columns=COLS_BAIRROS)
    corridas   = gerar_corridas(df_bairros)
    salvar_dados(corridas, df_bairros)
