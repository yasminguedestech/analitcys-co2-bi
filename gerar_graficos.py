"""
Gera todos os gráficos em PNG — CO₂ por Bairro · 99 São Paulo
Fator de emissão: 155 g CO₂/km (ICCT Brasil) | Fórmula: CETESB
"""

import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

os.makedirs("graficos", exist_ok=True)

# ── Paleta 99 — amarelo + tons escuros sobre fundo branco ─────────────────────
C = {
    "bg":    "#FFFFFF",
    "y99":   "#FFD600",   # amarelo 99 (primário)
    "blk":   "#111827",   # preto 99
    "navy":  "#1E3A5F",   # azul marinho escuro
    "char":  "#374151",   # carvão
    "amb":   "#92400E",   # âmbar escuro (quente)
    "teal":  "#164E63",   # azul-verde escuro
    "txt":   "#111827",
    "muted": "#6B7280",
    "brd":   "#E5E7EB",
}

ZONA_COR = {
    "Sul":    C["navy"],
    "Oeste":  C["char"],
    "Leste":  C["amb"],
    "Norte":  C["teal"],
    "Centro": C["y99"],
}

VEI_COR = {
    "Pop":       C["y99"],
    "Econômico": C["blk"],
    "Comfort":   C["navy"],
    "Black":     C["char"],
}

BASE = dict(
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["bg"],
    font=dict(color=C["txt"], family="Inter, Arial, sans-serif", size=13),
    margin=dict(l=28, r=28, t=70, b=28),
)

W, H = 1200, 500


def add_logo(fig, x=0.995, y=1.06):
    """Badge amarelo 99 no canto superior direito."""
    fig.add_annotation(
        text="<b>99</b>",
        xref="paper", yref="paper",
        x=x, y=y,
        showarrow=False,
        font=dict(size=15, color=C["blk"], family="Inter, Arial, sans-serif"),
        bgcolor=C["y99"],
        borderpad=6,
        bordercolor=C["y99"],
        align="center",
        xanchor="right",
        yanchor="top",
    )
    return fig


def salvar(fig, nome, w=W, h=H):
    fig.update_layout(width=w, height=h)
    fig.write_image(f"graficos/{nome}.png", scale=2)
    print(f"  graficos/{nome}.png")


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
    .agg(co2_total_kg=("co2_emitido_kg", "sum"))
    .sort_values("co2_total_kg", ascending=False)
)

vei_agg = (
    corridas.groupby("tipo_veiculo", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg", "sum"))
)

tempo_agg = (
    corridas.groupby("semana", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg", "sum"))
    .sort_values("semana")
    .iloc[:-1]
)

hora_agg = (
    corridas.groupby("hora", as_index=False)
    .agg(co2_total_kg=("co2_emitido_kg", "sum"), n_corridas=("id_corrida", "count"))
    .sort_values("hora")
)

print("Gerando gráficos...")

# ── 01 · Mapa de bolhas ────────────────────────────────────────────────────────
fig = px.scatter_map(
    bairro_agg,
    lat="lat_origem", lon="lon_origem",
    size="co2_total_kg", color="co2_total_kg",
    color_continuous_scale=[
        [0,    "#F3F4F6"],
        [0.4,  C["y99"]],
        [0.75, C["navy"]],
        [1,    C["blk"]],
    ],
    hover_name="bairro_origem",
    size_max=48,
    zoom=10.6,
    center={"lat": -23.575, "lon": -46.648},
    map_style="carto-positron",
    title="CO₂ por Bairro · São Paulo",
)
fig.update_layout(
    paper_bgcolor=C["bg"],
    font=dict(color=C["txt"], family="Inter, Arial, sans-serif", size=13),
    title_font_size=15, title_x=0.02,
    coloraxis_showscale=False,
    margin=dict(l=0, r=0, t=52, b=0),
)
add_logo(fig, y=1.08)
salvar(fig, "01_mapa_co2_bairro", w=1200, h=580)


# ── 02 · Top 10 bairros ────────────────────────────────────────────────────────
top10 = bairro_agg.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")
fig = go.Figure(go.Bar(
    y=top10["bairro_origem"],
    x=top10["co2_total_kg"],
    orientation="h",
    marker_color=[ZONA_COR.get(z, C["char"]) for z in top10["zona_origem"]],
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
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
add_logo(fig)
salvar(fig, "02_top10_bairros")


# ── 03 · CO₂ por tipo de veículo ──────────────────────────────────────────────
ordem = ["Pop", "Econômico", "Comfort", "Black"]
df_v  = vei_agg.set_index("tipo_veiculo").reindex(ordem).reset_index().dropna()
fig = go.Figure(go.Pie(
    labels=df_v["tipo_veiculo"],
    values=df_v["co2_total_kg"],
    hole=0.58,
    marker=dict(
        colors=[VEI_COR[v] for v in df_v["tipo_veiculo"]],
        line=dict(color=C["bg"], width=3),
    ),
    textinfo="label+percent",
    textfont=dict(color=C["txt"], size=13),
    sort=False,
))
fig.add_annotation(
    text="CO₂<br>Veículo", x=0.5, y=0.5, showarrow=False,
    font=dict(size=14, color=C["muted"]),
)
fig.update_layout(
    **BASE,
    title="CO₂ por Tipo de Veículo",
    title_font_size=15, title_x=0.02,
    showlegend=True,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=13)),
)
add_logo(fig)
salvar(fig, "03_co2_por_veiculo", w=700, h=480)


# ── 04 · CO₂ por zona ─────────────────────────────────────────────────────────
fig = go.Figure(go.Bar(
    x=zona_agg["zona_origem"],
    y=zona_agg["co2_total_kg"],
    marker_color=[ZONA_COR.get(z, C["char"]) for z in zona_agg["zona_origem"]],
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
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
add_logo(fig)
salvar(fig, "04_co2_por_zona", w=800, h=480)


# ── 05 · Evolução semanal ─────────────────────────────────────────────────────
ymin = tempo_agg["co2_total_kg"].min() * 0.88
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=tempo_agg["semana"],
    y=tempo_agg["co2_total_kg"],
    mode="lines+markers",
    line=dict(color=C["blk"], width=2.5),
    marker=dict(color=C["y99"], size=9,
                line=dict(color=C["blk"], width=1.8)),
    hovertemplate="%{x|%d/%m/%Y}<br>CO₂: %{y:,.0f} kg<extra></extra>",
))
fig.update_layout(
    **BASE,
    title="Evolução Semanal das Emissões de CO₂ — Q1 2024",
    title_font_size=15, title_x=0.02,
    showlegend=False,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11), tickformat="%d/%m"),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               range=[ymin, None],
               tickfont=dict(color=C["muted"], size=11)),
)
add_logo(fig)
salvar(fig, "05_evolucao_semanal")


# ── 06 · CO₂ por hora do dia ──────────────────────────────────────────────────
pico   = {7, 8, 9, 17, 18, 19, 20}
cores  = [C["y99"] if h in pico else C["brd"] for h in hora_agg["hora"]]
bordas = [C["blk"] if h in pico else C["muted"] for h in hora_agg["hora"]]

fig = go.Figure(go.Bar(
    x=hora_agg["hora"],
    y=hora_agg["co2_total_kg"],
    marker_color=cores,
    marker_line_color=bordas,
    marker_line_width=1.2,
    customdata=hora_agg["n_corridas"],
    hovertemplate="<b>%{x}h</b><br>CO₂: %{y:,.0f} kg<br>Corridas: %{customdata:,}<extra></extra>",
))
fig.add_annotation(
    text="amarelo = horário de pico (7–9h e 17–20h)",
    xref="paper", yref="paper",
    x=0.02, y=0.97, showarrow=False,
    font=dict(size=11, color=C["muted"]), align="left",
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
add_logo(fig)
salvar(fig, "06_co2_por_hora")


# ── 07 · Distância × CO₂ ─────────────────────────────────────────────────────
fig = px.scatter(
    bairro_agg,
    x="dist_media_km",
    y="co2_total_kg",
    size="n_corridas",
    color="zona_origem",
    color_discrete_map=ZONA_COR,
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
fig.update_traces(marker=dict(line=dict(color=C["bg"], width=1.5)))
fig.update_layout(
    **BASE,
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               tickfont=dict(color=C["muted"], size=11)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=12)),
)
add_logo(fig)
salvar(fig, "07_scatter_distancia_co2")


# ── 08 · Potencial de redução EV ──────────────────────────────────────────────
top10 = bairro_agg.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")
fig = go.Figure()
fig.add_trace(go.Bar(
    name="Emissão Atual",
    y=top10["bairro_origem"],
    x=top10["co2_total_kg"],
    orientation="h",
    marker_color=C["blk"],
    marker_line_width=0,
    opacity=0.85,
    hovertemplate="<b>%{y}</b><br>Atual: %{x:,.0f} kg<extra></extra>",
))
fig.add_trace(go.Bar(
    name="Com 30 % da Frota Elétrica",
    y=top10["bairro_origem"],
    x=top10["co2_proj_kg"],
    orientation="h",
    marker_color=C["y99"],
    marker_line_width=0,
    opacity=0.95,
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
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.06, x=0,
                font=dict(color=C["txt"], size=12)),
)
add_logo(fig)
salvar(fig, "08_potencial_reducao_ev", h=540)


# ── 09 · Score de prioridade ──────────────────────────────────────────────────
prior = bairro_agg.copy()
raw   = prior["co2_total_kg"] * prior["dist_media_km"]
prior["score"] = ((raw - raw.min()) / (raw.max() - raw.min()) * 100).round(1)
prior = prior.nlargest(10, "score").sort_values("score")

def cor_score(s):
    if s >= 80: return C["blk"]
    if s >= 60: return C["navy"]
    if s >= 40: return C["char"]
    return C["muted"]

fig = go.Figure(go.Bar(
    y=prior["bairro_origem"],
    x=prior["score"],
    orientation="h",
    marker_color=[cor_score(s) for s in prior["score"]],
    marker_line_color=[C["y99"] if s >= 80 else "rgba(0,0,0,0)" for s in prior["score"]],
    marker_line_width=2,
    text=[f"{s:.0f}" for s in prior["score"]],
    textposition="outside",
    textfont=dict(color=C["txt"], size=12),
    hovertemplate="<b>%{y}</b><br>Score: %{x:.0f}/100<extra></extra>",
))

top3_score = prior["score"].nlargest(3).min()
fig.add_vline(
    x=top3_score - 0.5,
    line_dash="dash", line_color=C["y99"], line_width=2,
    annotation_text="ação imediata",
    annotation_position="top right",
    annotation_font=dict(color=C["blk"], size=11,
                         family="Inter, Arial, sans-serif"),
)

fig.update_layout(
    **BASE,
    title="Onde Agir Primeiro? — Score de Prioridade para Eletrificação",
    title_font_size=15, title_x=0.02,
    xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
               range=[0, 115],
               tickfont=dict(color=C["muted"], size=11),
               title=dict(text="Score de Prioridade (0–100)", font=dict(color=C["muted"]))),
    yaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=12)),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
add_logo(fig)
salvar(fig, "09_score_prioridade", h=520)


print(f"\n9 gráficos gerados em graficos/")
