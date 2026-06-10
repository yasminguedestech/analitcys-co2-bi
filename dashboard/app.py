"""
Dashboard CO₂ por Bairro — 99 São Paulo
Fator de emissão: 155 g CO₂/km (ICCT Brasil) | Fórmula: CETESB
Corridas: simuladas com distribuição realista
"""

import os
import sqlite3

import dash
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html, Input, Output

# ── Paleta 99 ─────────────────────────────────────────────────────────────────
C = {
    "bg":    "#0F1117",
    "card":  "#1A1C2C",
    "side":  "#13141F",
    "y99":   "#FFD600",
    "org":   "#FF6B2B",
    "grn":   "#00C896",
    "prp":   "#7B61FF",
    "cyn":   "#00D4FF",
    "red":   "#FF4560",
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

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=C["txt"], family="Inter, -apple-system, sans-serif", size=12),
    margin=dict(l=10, r=10, t=44, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["txt"], size=11)),
)

# ── Carregar dados ─────────────────────────────────────────────────────────────
DB = os.path.join(os.path.dirname(__file__), "..", "data", "co2_corridas.db")

conn = sqlite3.connect(DB)
CORRIDAS_FULL = pd.read_sql("SELECT * FROM corridas", conn)
conn.close()
CORRIDAS_FULL["data_hora"] = pd.to_datetime(CORRIDAS_FULL["data_hora"])
CORRIDAS_FULL["semana"] = (
    CORRIDAS_FULL["data_hora"].dt.to_period("W").apply(lambda x: x.start_time)
)

EV_FATOR   = 20.0
EV_ADOCAO  = 0.30
EV_REDUCAO = (155 - EV_FATOR) / 155
RED_EV_PCT = EV_ADOCAO * EV_REDUCAO * 100

ZONAS    = sorted(CORRIDAS_FULL["zona_origem"].unique())
VEICULOS = ["Pop", "Econômico", "Comfort", "Black"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def filtrar(zonas_sel, veic_sel):
    df = CORRIDAS_FULL
    if zonas_sel:
        df = df[df["zona_origem"].isin(zonas_sel)]
    if veic_sel:
        df = df[df["tipo_veiculo"].isin(veic_sel)]
    return df


def agg_bairro(df):
    if df.empty:
        return pd.DataFrame(columns=[
            "id_bairro_origem","bairro_origem","zona_origem","lat_origem","lon_origem",
            "n_corridas","co2_total_kg","co2_medio_kg","dist_media_km",
            "co2_projetado_kg","reducao_kg",
        ])
    agg = (
        df.groupby(
            ["id_bairro_origem","bairro_origem","zona_origem","lat_origem","lon_origem"],
            as_index=False,
        ).agg(
            n_corridas    =("id_corrida",     "count"),
            co2_total_kg  =("co2_emitido_kg", "sum"),
            co2_medio_kg  =("co2_emitido_kg", "mean"),
            dist_media_km =("distancia_km",   "mean"),
        )
        .sort_values("co2_total_kg", ascending=False)
    )
    agg["co2_projetado_kg"] = agg["co2_total_kg"] * (1 - EV_ADOCAO * EV_REDUCAO)
    agg["reducao_kg"]       = agg["co2_total_kg"] - agg["co2_projetado_kg"]
    return agg


def kpi_card(label, value, sub="", value_color=None):
    return html.Div([
        html.P(label, style={
            "color": C["muted"], "fontSize": "10px", "margin": "0 0 4px",
            "textTransform": "uppercase", "letterSpacing": "1.2px", "fontWeight": "600",
        }),
        html.H3(value, style={
            "color": value_color or C["txt"], "fontSize": "24px",
            "margin": "0 0 2px", "fontWeight": "800", "lineHeight": "1",
        }),
        html.P(sub, style={"color": C["muted"], "fontSize": "10px", "margin": "0"}),
    ], style={
        "backgroundColor": C["card"],
        "borderRadius": "12px",
        "padding": "16px 18px",
        "border": f"1px solid {C['brd']}",
        "flex": "1",
        "minWidth": "130px",
    })


def card_wrap(children, flex="1"):
    return html.Div(children, style={
        "backgroundColor": C["card"],
        "borderRadius": "12px",
        "padding": "4px 4px 0",
        "border": f"1px solid {C['brd']}",
        "flex": flex,
        "overflow": "hidden",
        "minWidth": "0",
    })


GC = {"displayModeBar": False, "responsive": True}


# ── Gráficos ──────────────────────────────────────────────────────────────────
def fig_mapa(ba):
    if ba.empty:
        fig = go.Figure()
        fig.update_layout(**LAYOUT_BASE, height=390,
                          title="CO₂ por Bairro · São Paulo",
                          title_font_size=13, title_x=0.02)
        return fig
    fig = px.scatter_map(
        ba,
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
        hover_data={
            "co2_total_kg":  ":.0f",
            "n_corridas":    True,
            "zona_origem":   True,
            "lat_origem":    False,
            "lon_origem":    False,
            "dist_media_km": ":.1f",
        },
        labels={
            "co2_total_kg":  "CO₂ (kg)",
            "n_corridas":    "Corridas",
            "zona_origem":   "Zona",
            "dist_media_km": "Dist. média (km)",
        },
        size_max=45,
        zoom=10.8,
        center={"lat": -23.575, "lon": -46.648},
        map_style="carto-darkmatter",
        title="CO₂ por Bairro · São Paulo",
    )
    fig.update_layout(
        **LAYOUT_BASE, height=390,
        title_font_size=13, title_x=0.02,
        coloraxis_showscale=False,
    )
    return fig


def fig_top_bairros(ba):
    top10 = ba.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")
    cores = [PALETA_ZONA.get(z, C["muted"]) for z in top10["zona_origem"]]
    fig = go.Figure(go.Bar(
        y=top10["bairro_origem"],
        x=top10["co2_total_kg"],
        orientation="h",
        marker_color=cores,
        marker_line_width=0,
        text=top10["co2_total_kg"].apply(lambda v: f"{v:,.0f} kg"),
        textposition="outside",
        textfont=dict(color=C["txt"], size=10),
        hovertemplate="<b>%{y}</b><br>CO₂: %{x:,.0f} kg<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title="Top 10 Bairros por CO₂",
        title_font_size=13, title_x=0.02,
        height=390,
        xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10)),
        yaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=11)),
    )
    return fig


def fig_veiculo(df):
    vei = (
        df.groupby("tipo_veiculo", as_index=False)
        .agg(co2_total_kg=("co2_emitido_kg", "sum"))
    )
    df_v = (
        vei.set_index("tipo_veiculo")
        .reindex(VEICULOS)
        .reset_index()
        .dropna(subset=["co2_total_kg"])
    )
    cores = [PALETA_VEICULO.get(v, C["muted"]) for v in df_v["tipo_veiculo"]]
    fig = go.Figure(go.Pie(
        labels=df_v["tipo_veiculo"],
        values=df_v["co2_total_kg"],
        hole=0.58,
        marker=dict(colors=cores, line=dict(color=C["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(color=C["txt"], size=11),
        hovertemplate="<b>%{label}</b><br>CO₂: %{value:,.0f} kg (%{percent})<extra></extra>",
        sort=False,
    ))
    fig.add_annotation(text="CO₂<br>Veículo", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=12, color=C["muted"]))
    fig.update_layout(
        **LAYOUT_BASE,
        title="CO₂ por Tipo de Veículo",
        title_font_size=13, title_x=0.02,
        height=310, showlegend=False,
    )
    return fig


def fig_zona(df):
    zona = (
        df.groupby("zona_origem", as_index=False)
        .agg(co2_total_kg=("co2_emitido_kg", "sum"))
        .sort_values("co2_total_kg", ascending=False)
    )
    cores = [PALETA_ZONA.get(z, C["muted"]) for z in zona["zona_origem"]]
    fig = go.Figure(go.Bar(
        x=zona["zona_origem"],
        y=zona["co2_total_kg"],
        marker_color=cores,
        marker_line_width=0,
        text=zona["co2_total_kg"].apply(lambda v: f"{v/1000:.1f}t"),
        textposition="outside",
        textfont=dict(color=C["txt"], size=11),
        hovertemplate="<b>%{x}</b><br>CO₂: %{y:,.0f} kg<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title="CO₂ por Zona",
        title_font_size=13, title_x=0.02,
        height=310,
        xaxis=dict(showgrid=False, tickfont=dict(color=C["txt"])),
        yaxis=dict(
            showgrid=True, gridcolor=C["brd"], zeroline=False,
            tickfont=dict(color=C["muted"], size=10),
            title=dict(text="CO₂ (kg)", font=dict(color=C["muted"], size=10)),
        ),
    )
    return fig


def fig_timeline(df):
    tempo = (
        df.groupby("semana", as_index=False)
        .agg(co2_total_kg=("co2_emitido_kg", "sum"))
        .sort_values("semana")
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tempo["semana"],
        y=tempo["co2_total_kg"],
        mode="lines+markers",
        line=dict(color=C["y99"], width=2.5),
        marker=dict(color=C["y99"], size=5, line=dict(color=C["bg"], width=1)),
        fill="tozeroy",
        fillcolor="rgba(255,214,0,0.07)",
        hovertemplate="%{x|%d/%m/%Y}<br>CO₂: %{y:,.0f} kg<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title="Evolução Semanal do CO₂",
        title_font_size=13, title_x=0.02,
        height=310,
        xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10), tickformat="%d/%m"),
        yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10)),
        showlegend=False,
    )
    return fig


def fig_hora(df):
    hora = (
        df.groupby("hora", as_index=False)
        .agg(co2_total_kg=("co2_emitido_kg", "sum"), n_corridas=("id_corrida", "count"))
        .sort_values("hora")
    )
    pico = {7, 8, 9, 17, 18, 19, 20}
    cores = [C["y99"] if h in pico else C["prp"] for h in hora["hora"]]
    fig = go.Figure(go.Bar(
        x=hora["hora"],
        y=hora["co2_total_kg"],
        marker_color=cores,
        marker_line_width=0,
        customdata=hora["n_corridas"],
        hovertemplate="<b>%{x}h</b><br>CO₂: %{y:,.0f} kg<br>Corridas: %{customdata:,}<extra></extra>",
    ))
    fig.add_annotation(
        text="amarelo = horário de pico",
        xref="paper", yref="paper",
        x=0.98, y=0.98, showarrow=False,
        font=dict(size=9, color=C["muted"]),
        align="right",
    )
    fig.update_layout(
        **LAYOUT_BASE,
        title="CO₂ por Hora do Dia",
        title_font_size=13, title_x=0.02,
        height=310,
        xaxis=dict(showgrid=False, tickmode="linear", dtick=2,
                   tickfont=dict(color=C["muted"], size=10),
                   title=dict(text="hora", font=dict(color=C["muted"], size=10))),
        yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10)),
    )
    return fig


def fig_reducao(ba):
    top10 = ba.nlargest(10, "co2_total_kg").sort_values("co2_total_kg")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Emissão atual",
        y=top10["bairro_origem"],
        x=top10["co2_total_kg"],
        orientation="h",
        marker_color=C["org"],
        marker_line_width=0,
        opacity=0.9,
        hovertemplate="<b>%{y}</b><br>Atual: %{x:,.0f} kg<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Com 30 % EV",
        y=top10["bairro_origem"],
        x=top10["co2_projetado_kg"],
        orientation="h",
        marker_color=C["grn"],
        marker_line_width=0,
        opacity=0.85,
        hovertemplate="<b>%{y}</b><br>Projetado: %{x:,.0f} kg<extra></extra>",
    ))
    fig.update_layout(
        **LAYOUT_BASE,
        title="Onde Reduzir? — Potencial com 30 % da Frota Elétrica",
        title_font_size=13, title_x=0.02,
        height=400, barmode="overlay",
        xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10),
                   title=dict(text="CO₂ (kg)", font=dict(color=C["muted"], size=10))),
        yaxis=dict(showgrid=False, tickfont=dict(color=C["txt"], size=11)),
        legend=dict(orientation="h", y=1.06, x=0),
    )
    return fig


def fig_scatter_dist(ba):
    fig = px.scatter(
        ba,
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
        title="Distância × CO₂ por Bairro",
        size_max=35,
    )
    fig.update_traces(
        marker=dict(line=dict(color=C["bg"], width=1)),
        hovertemplate="<b>%{hovertext}</b><br>Dist.: %{x:.1f} km<br>CO₂: %{y:,.0f} kg<extra></extra>",
    )
    fig.update_layout(
        **LAYOUT_BASE,
        height=400,
        title_font_size=13, title_x=0.02,
        xaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10)),
        yaxis=dict(showgrid=True, gridcolor=C["brd"], zeroline=False,
                   tickfont=dict(color=C["muted"], size=10)),
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
def nav_item(num, label, href):
    return html.A([
        html.Span(num, style={
            "color": C["y99"], "fontSize": "10px",
            "marginRight": "10px", "fontWeight": "700", "width": "16px",
        }),
        html.Span(label, style={"color": C["muted"], "fontSize": "12px"}),
    ], href=href, className="nav-item-link", style={
        "display": "flex", "alignItems": "center",
        "padding": "9px 14px", "borderRadius": "8px",
        "textDecoration": "none", "marginBottom": "2px",
        "transition": "background 0.15s",
    })


SIDEBAR = html.Div([
    # Logo
    html.Div([
        html.Div([
            html.Span("99", style={
                "backgroundColor": C["y99"], "color": "#000",
                "fontWeight": "900", "fontSize": "17px",
                "padding": "3px 9px", "borderRadius": "6px",
            }),
            html.Span(" CO₂", style={"color": C["txt"], "fontSize": "16px", "fontWeight": "700"}),
        ]),
        html.Div("Analytics · São Paulo", style={
            "color": C["muted"], "fontSize": "10px", "marginTop": "6px",
        }),
    ], style={"padding": "22px 16px 18px", "borderBottom": f"1px solid {C['brd']}"}),

    # Filtros
    html.Div([
        html.P("FILTROS", style={
            "color": C["y99"], "fontSize": "9px", "fontWeight": "700",
            "letterSpacing": "1.5px", "margin": "0 0 10px",
        }),
        html.P("Zona", style={"color": C["muted"], "fontSize": "9px", "margin": "0 0 5px"}),
        dcc.Dropdown(
            id="filtro-zona",
            options=[{"label": z, "value": z} for z in ZONAS],
            value=[],
            multi=True,
            placeholder="Todas as zonas",
            className="dropdown-99",
        ),
        html.P("Tipo de Veículo", style={
            "color": C["muted"], "fontSize": "9px", "margin": "12px 0 5px",
        }),
        dcc.Dropdown(
            id="filtro-veiculo",
            options=[{"label": v, "value": v} for v in VEICULOS],
            value=[],
            multi=True,
            placeholder="Todos os veículos",
            className="dropdown-99",
        ),
        html.Div(id="filtro-status", style={"marginTop": "8px"}),
    ], style={"padding": "14px 12px 12px", "borderBottom": f"1px solid {C['brd']}"}),

    # Navegação
    html.Div([
        nav_item("01", "Visão Executiva",     "#secao-kpis"),
        nav_item("02", "Mapa de Emissões",    "#secao-mapa"),
        nav_item("03", "Top Bairros",         "#secao-mapa"),
        nav_item("04", "Por Zona & Veículo",  "#secao-zona"),
        nav_item("05", "Potencial de Redução","#secao-ev"),
    ], style={"padding": "10px 6px", "flex": "1"}),

    # Rodapé com metodologia
    html.Div([
        html.Hr(style={"borderColor": C["brd"], "margin": "0 0 10px"}),
        html.P("Metodologia", style={
            "color": C["y99"], "fontSize": "10px", "fontWeight": "700", "margin": "0 0 6px",
        }),
        html.P("Fator de emissão (ICCT Brasil):", style={"color": C["muted"], "fontSize": "9px", "margin": "0"}),
        html.P("155 g CO₂/km", style={
            "color": C["txt"], "fontSize": "13px", "fontWeight": "700", "margin": "2px 0 4px",
        }),
        html.P("Fórmula: CETESB", style={"color": C["muted"], "fontSize": "9px", "margin": "0"}),
        html.P("EV: 20 g CO₂/km · matriz BR", style={"color": C["muted"], "fontSize": "9px", "margin": "0 0 8px"}),
        html.Hr(style={"borderColor": C["brd"], "margin": "0 0 8px"}),
        html.P("Q1 2024 · Jan–Mar", style={"color": C["muted"], "fontSize": "9px", "margin": "0"}),
        html.P("10.000 corridas simuladas*", style={"color": C["muted"], "fontSize": "9px", "margin": "0"}),
    ], style={
        "position": "absolute", "bottom": "16px", "left": "0", "right": "0",
        "padding": "0 16px",
    }),

], style={
    "backgroundColor": C["side"],
    "width": "210px",
    "minHeight": "100vh",
    "position": "fixed",
    "left": "0", "top": "0",
    "borderRight": f"1px solid {C['brd']}",
    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    "overflowY": "auto",
    "display": "flex",
    "flexDirection": "column",
})


# ── Layout principal ───────────────────────────────────────────────────────────
MAIN = html.Div([

    # Cabeçalho
    html.Div([
        html.H1("Emissões de CO₂ por Bairro", style={
            "color": C["txt"], "fontSize": "22px", "fontWeight": "800", "margin": "0",
        }),
        html.P(
            "Corridas simuladas · Fator real ICCT Brasil: 155 g CO₂/km · Fórmula: CETESB",
            style={"color": C["muted"], "fontSize": "12px", "margin": "4px 0 0"},
        ),
    ], style={"marginBottom": "20px"}),

    # KPIs dinâmicos
    html.Div(id="secao-kpis",
             style={"display": "flex", "gap": "10px", "marginBottom": "16px", "flexWrap": "wrap"}),

    # Linha 1 — Mapa + Top Bairros
    html.Div(id="secao-mapa", style={"display": "flex", "gap": "14px", "marginBottom": "14px"},
             children=[
                 card_wrap(dcc.Graph(id="grafico-mapa", config=GC), flex="1.3"),
                 card_wrap(dcc.Graph(id="grafico-top",  config=GC), flex="1"),
             ]),

    # Linha 2 — Donut + Zona + Timeline
    html.Div(id="secao-zona", style={"display": "flex", "gap": "14px", "marginBottom": "14px"},
             children=[
                 card_wrap(dcc.Graph(id="grafico-veiculo",  config=GC), flex="1"),
                 card_wrap(dcc.Graph(id="grafico-zona",     config=GC), flex="1"),
                 card_wrap(dcc.Graph(id="grafico-timeline", config=GC), flex="1.3"),
             ]),

    # Linha 3 — Hora + Scatter
    html.Div(style={"display": "flex", "gap": "14px", "marginBottom": "14px"},
             children=[
                 card_wrap(dcc.Graph(id="grafico-hora",    config=GC), flex="1"),
                 card_wrap(dcc.Graph(id="grafico-scatter", config=GC), flex="1"),
             ]),

    # Linha 4 — Potencial EV (largura total)
    html.Div(id="secao-ev", style={"display": "flex", "gap": "14px", "marginBottom": "14px"},
             children=[
                 card_wrap(dcc.Graph(id="grafico-ev", config=GC), flex="1"),
             ]),

    # Rodapé
    html.P(
        "* As corridas são simuladas para fins de demonstração — a 99 não disponibiliza dados de corridas publicamente. "
        "O fator de emissão de 155 g CO₂/km é real (ICCT Brasil, 2023). Fórmula de cálculo: CETESB. "
        "EV estimado: 20 g CO₂/km (matriz elétrica brasileira ~80 % renovável).",
        style={
            "color": C["muted"], "fontSize": "10px", "textAlign": "center",
            "padding": "8px 0 28px", "lineHeight": "1.6",
        },
    ),

], style={
    "marginLeft": "210px",
    "padding": "28px 24px",
    "minHeight": "100vh",
    "backgroundColor": C["bg"],
    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
    "boxSizing": "border-box",
})


# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    title="99 · CO₂ Analytics · São Paulo",
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    ],
)
app.layout = html.Div([SIDEBAR, MAIN], style={"backgroundColor": C["bg"]})


# ── Callback principal — todos os gráficos reagem aos filtros ─────────────────
@app.callback(
    Output("secao-kpis",       "children"),
    Output("grafico-mapa",     "figure"),
    Output("grafico-top",      "figure"),
    Output("grafico-veiculo",  "figure"),
    Output("grafico-zona",     "figure"),
    Output("grafico-timeline", "figure"),
    Output("grafico-hora",     "figure"),
    Output("grafico-scatter",  "figure"),
    Output("grafico-ev",       "figure"),
    Output("filtro-status",    "children"),
    Input("filtro-zona",    "value"),
    Input("filtro-veiculo", "value"),
)
def atualizar(zonas_sel, veic_sel):
    df = filtrar(zonas_sel, veic_sel)
    ba = agg_bairro(df)

    # KPIs
    n          = len(df)
    co2_ton    = df["co2_emitido_kg"].sum() / 1000 if n else 0
    co2_medio  = df["co2_emitido_kg"].mean() if n else 0
    bairro_top = ba.iloc[0]["bairro_origem"] if len(ba) > 0 else "—"
    curtas     = int((df["distancia_km"] < 5).sum())

    kpis = [
        kpi_card("Total de Corridas",  f"{n:,}".replace(",", "."),  "Q1 · Jan–Mar 2024"),
        kpi_card("CO₂ Total",          f"{co2_ton:.1f} ton",        "toneladas emitidas",      C["org"]),
        kpi_card("Média / Corrida",    f"{co2_medio:.2f} kg",       "CO₂ por corrida"),
        kpi_card("Bairro Crítico",     bairro_top,                  "maior emissão acumulada", C["y99"]),
        kpi_card("Corridas < 5 km",    f"{curtas:,}".replace(",","."),"alto pot. substituição"),
        kpi_card("Red. c/ 30 % EV",    f"-{RED_EV_PCT:.0f} %",     "adotando elétricos",      C["grn"]),
    ]

    # Chip de status do filtro
    partes = []
    if zonas_sel:
        partes.append(f"Zona: {', '.join(zonas_sel)}")
    if veic_sel:
        partes.append(f"Veíc: {', '.join(veic_sel)}")
    status = html.Span(" · ".join(partes), className="filtro-ativo") if partes else None

    return (
        kpis,
        fig_mapa(ba),
        fig_top_bairros(ba),
        fig_veiculo(df),
        fig_zona(df),
        fig_timeline(df),
        fig_hora(df),
        fig_scatter_dist(ba),
        fig_reducao(ba),
        status,
    )


if __name__ == "__main__":
    app.run(debug=False, port=8050)
