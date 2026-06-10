"""
Gera todos os gráficos em PNG — CO₂ por Bairro · 99 São Paulo
Fator de emissão: 155 g CO₂/km (ICCT Brasil) | Fórmula: CETESB
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

os.makedirs("graficos", exist_ok=True)

# ── Paleta 99 ──────────────────────────────────────────────────────────────────
C = {
    "bg":    "#0F1117",
    "card":  "#1A1C2C",
    "y99":   "#FFD600",
    "org":   "#FF6B2B",
    "grn":   "#00C896",
    "prp":   "#7B61FF",
    "cyn":   "#00D4FF",
    "txt":   "#FFFFFF",
    "muted": "#8892A4",
    "brd":   "#2A2D3E",
}

PALETA_ZONA = {
    "Centro": C["y99"],
    "Sul":    C["org"],
    "Oeste":  C["prp"],
    "Leste":  C["cyn"],
    "Norte":  C["grn"],
}

PALETA_VEICULO = {
    "Pop":       C["y99"],
    "Econômico": C["org"],
    "Comfort":   C["prp"],
    "Black":     C["cyn"],
}

BASE = dict(
    paper_bgcolor=C["card"],
    plot_bgcolor=C["card"],
    font=dict(color=C["txt"], family="Inter, Arial, sans-serif", size=13),
    margin=dict(l=24, r=24, t=56, b=24),
)

LEG = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=12))

W, H = 1200, 500

# ── Dados ──────────────────────────────────────────────────────────────────────
conn     = sqlite3.connect("data/co2_corridas.db")
corridas = pd.read_sql("SELECT * FROM corridas", conn)
conn.close()
corridas["data_hora"] = pd.to_datetime(corridas["data_hora"])
corridas["semana"]    = corridas["data_hora"].dt.to_period("W").apply(lambda x: x.start_time)

EV_ADOCAO  = 0.30
EV_REDUCAO = (155 - 20) / 155

bairro_agg = (
    corridas.groupby(
        ["bairro_origem", "zona_origem", "lat_origem", "lon_origem"], as_index=False
    ).agg(
        n_corridas   =("id_corrida",     "count"),
        co2_total_kg =("co2_emitido_kg", "sum"),
        dist_media_km=("distancia_km",   "mean"),
    ).sort_values("co2_total_kg", ascending=False)
)
bairro_agg["co2_proj_kg"] = bairro_agg["co2_total_kg"] * (1 - EV_ADOCAO * EV_REDUCAO)
bairro_agg["reducao_kg"]  = bairro_agg["co2_total_kg"] - bairro_agg["co2_proj_kg"]

zona_agg = (
    corridas.groupby("zona_origem", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg","sum"))
    .sort_values("co2_total_kg", ascending=False)
)

vei_agg = (
    corridas.groupby("tipo_veiculo", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg","sum"))
)

tempo_agg = (
    corridas.groupby("semana", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg","sum"))
    .sort_values("semana")
)

hora_agg = (
    corridas.groupby("hora", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg","sum"), n_corridas=("id_corrida","count"))
    .sort_values("hora")
)


def salvar(fig, nome, w=W, h=H):
    fig.update_layout(width=w, height=h)
    caminho = f"graficos/{nome}.png"
    fig.write_image(caminho, scale=2)
    print(f"  {caminho}")


# ── 01 · Mapa de bolhas ────────────────────────────────────────────────────────
fig = px.scatter_map(
    bairro_agg,
    lat="lat_origem", lon="lon_origem",
    size="co2_total_kg",
    color="co2_total_kg",
    color_continuous_scale=[
        [0,    "#1A1C2C"],
        [0.3,  C["grn"]],
        [0.65, C["org"]],
        [1,    C["y99"]],
    ],
    hover_name="bairro_origem",
    size_max=48,
    zoom=10.6,
    center={"lat": -23.575, "lon": -46.648},
    map_style="carto-darkmatter",
    title="CO₂ por Bairro · São Paulo",
)
fig.update_layout(
    title_font_size=15, title_x=0.02,
    coloraxis_showscale=False,
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["bg"],
    font=dict(color=C["txt"], family="Inter, Arial, sans-serif", size=13),
    margin=dict(l=24, r=24, t=56, b=24),
)
salvar(fig, "01_mapa_co2_bairro", w=1200, h=560)


# ── 02 · Top 10 bairros ────────────────────────────────────────────────────────
top10 = bairro_agg.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")
cores = [PALETA_ZONA.get(z, C["muted"]) for z in top10["zona_origem"]]

fig = go.Figure(go.Bar(
    y=top10["bairro_origem"],
    x=top10["co2_total_kg"],
    orientation="h",
    marker_color=cores,
    marker_line_width=0,
    text=top10["co2_total_kg"].apply(lambda v: f"{v:,.0f} kg"),
    textposition="outside",
    textfont=dict(color=C["txt"], size=11),
    hovertemplate="<b>%{y}</b><br>CO₂: %{x:,.0f} kg<extra></extra>",
))
fig.update_layout(
    **BASE,
    title="Top 10 Bairros por Emissão de CO₂",
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    yaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=12)),
)
salvar(fig, "02_top10_bairros")


# ── 03 · CO₂ por tipo de veículo ──────────────────────────────────────────────
ordem = ["Pop", "Econômico", "Comfort", "Black"]
df_v  = vei_agg.set_index("tipo_veiculo").reindex(ordem).reset_index().dropna()
cores = [PALETA_VEICULO[v] for v in df_v["tipo_veiculo"]]

fig = go.Figure(go.Pie(
    labels=df_v["tipo_veiculo"],
    values=df_v["co2_total_kg"],
    hole=0.58,
    marker=dict(colors=cores, line=dict(color=C["bg"], width=2)),
    textinfo="label+percent",
    textfont=dict(color=C["txt"], size=13),
    sort=False,
))
fig.add_annotation(text="CO₂<br>Veículo", x=0.5, y=0.5, showarrow=False,
                   font=dict(size=14, color=C["muted"]))
fig.update_layout(
    **BASE,
    title="CO₂ por Tipo de Veículo",
    title_font_size=15, title_x=0.02,
    showlegend=True,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=13)),
)
salvar(fig, "03_co2_por_veiculo", w=700, h=480)


# ── 04 · CO₂ por zona ─────────────────────────────────────────────────────────
cores = [PALETA_ZONA.get(z, C["muted"]) for z in zona_agg["zona_origem"]]

fig = go.Figure(go.Bar(
    x=zona_agg["zona_origem"],
    y=zona_agg["co2_total_kg"],
    marker_color=cores,
    marker_line_width=0,
    text=zona_agg["co2_total_kg"].apply(lambda v: f"{v/1000:.1f} t"),
    textposition="outside",
    textfont=dict(color=C["txt"], size=13),
    hovertemplate="<b>%{x}</b><br>CO₂: %{y:,.0f} kg<extra></extra>",
))
fig.update_layout(
    **BASE,
    title="CO₂ Total por Zona de São Paulo",
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=13)),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11),
               title=dict(text="CO₂ (kg)", font=dict(color=C["muted"]))),
)
salvar(fig, "04_co2_por_zona", w=800, h=480)


# ── 05 · Evolução semanal ─────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=tempo_agg["semana"],
    y=tempo_agg["co2_total_kg"],
    mode="lines+markers",
    line=dict(color=C["y99"], width=2.5),
    marker=dict(color=C["y99"], size=6, line=dict(color=C["bg"], width=1.5)),
    fill="tozeroy",
    fillcolor="rgba(255,214,0,0.08)",
    hovertemplate="%{x|%d/%m/%Y}<br>CO₂: %{y:,.0f} kg<extra></extra>",
))
fig.update_layout(
    **BASE,
    title="Evolução Semanal das Emissões de CO₂ — Q1 2024",
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11), tickformat="%d/%m"),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    showlegend=False,
)
salvar(fig, "05_evolucao_semanal")


# ── 06 · CO₂ por hora ─────────────────────────────────────────────────────────
pico  = {7, 8, 9, 17, 18, 19, 20}
cores = [C["y99"] if h in pico else C["prp"] for h in hora_agg["hora"]]

fig = go.Figure(go.Bar(
    x=hora_agg["hora"],
    y=hora_agg["co2_total_kg"],
    marker_color=cores,
    marker_line_width=0,
    customdata=hora_agg["n_corridas"],
    hovertemplate="<b>%{x}h</b><br>CO₂: %{y:,.0f} kg<br>Corridas: %{customdata:,}<extra></extra>",
))
fig.add_annotation(
    text="🟡 amarelo = horário de pico (7–9h e 17–20h)",
    xref="paper", yref="paper",
    x=0.98, y=0.97, showarrow=False,
    font=dict(size=11, color=C["muted"]), align="right",
)
fig.update_layout(
    **BASE,
    title="CO₂ por Hora do Dia",
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=False, tickmode="linear", dtick=2,
               tickfont=dict(color=C["muted"], size=11),
               title=dict(text="hora", font=dict(color=C["muted"]))),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
)
salvar(fig, "06_co2_por_hora")


# ── 07 · Distância × CO₂ ─────────────────────────────────────────────────────
fig = px.scatter(
    bairro_agg,
    x="dist_media_km",
    y="co2_total_kg",
    size="n_corridas",
    color="zona_origem",
    color_discrete_map=PALETA_ZONA,
    hover_name="bairro_origem",
    labels={
        "dist_media_km": "Distância Média (km)",
        "co2_total_kg":  "CO₂ Total (kg)",
        "zona_origem":   "Zona",
        "n_corridas":    "Corridas",
    },
    title="Distância Média × CO₂ Total por Bairro",
    size_max=40,
)
fig.update_traces(marker=dict(line=dict(color=C["bg"], width=1)))
fig.update_layout(
    **BASE,
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=12)),
)
salvar(fig, "07_scatter_distancia_co2")


# ── 08 · Potencial de redução EV ──────────────────────────────────────────────
top10 = bairro_agg.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Emissão Atual",
    y=top10["bairro_origem"],
    x=top10["co2_total_kg"],
    orientation="h",
    marker_color=C["org"],
    marker_line_width=0,
    opacity=0.9,
    hovertemplate="<b>%{y}</b><br>Atual: %{x:,.0f} kg<extra></extra>",
))
fig.add_trace(go.Bar(
    name="Com 30 % da Frota Elétrica",
    y=top10["bairro_origem"],
    x=top10["co2_proj_kg"],
    orientation="h",
    marker_color=C["grn"],
    marker_line_width=0,
    opacity=0.85,
    hovertemplate="<b>%{y}</b><br>Projetado: %{x:,.0f} kg<extra></extra>",
))
fig.update_layout(
    **BASE,
    title="Onde Reduzir? — Potencial com 30 % da Frota Elétrica",
    title_font_size=15, title_x=0.02,
    barmode="overlay",
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11),
               title=dict(text="CO₂ (kg)", font=dict(color=C["muted"]))),
    yaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=12)),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.06, x=0, font=dict(color=C["txt"], size=12)),
)
salvar(fig, "08_potencial_reducao_ev", h=520)


print(f"\n8 gráficos gerados em graficos/")
