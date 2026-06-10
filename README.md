# 99 · CO₂ Analytics — Emissões por Bairro em São Paulo

Dashboard interativo de análise de emissões de CO₂ por corridas de transporte por aplicativo em São Paulo, com foco em identificar **onde é possível reduzir**.

---

## Sobre o projeto

| | |
|---|---|
| **Fator de emissão** | 155 g CO₂/km — ICCT Brasil (2023) · dado real |
| **Fórmula** | CO₂ (g) = distância (km) × 155 · CETESB |
| **EV estimado** | 20 g CO₂/km (matriz elétrica brasileira ~80 % renovável) |
| **Corridas** | Simuladas com distribuição realista por bairro, horário e tipo de veículo* |
| **Período** | Q1 2024 · Janeiro a Março |
| **Volume** | 10.000 corridas · 30 bairros de SP |

> *A 99 não disponibiliza dados de corridas publicamente. Este projeto aplica fatores de emissão reais a corridas simuladas para fins de demonstração.*

---

## Dashboard

```
python dashboard/app.py
```

Acesse em `http://localhost:8050`

### Filtros interativos
- **Zona** (Centro, Sul, Norte, Leste, Oeste)
- **Tipo de veículo** (Pop, Econômico, Comfort, Black)
- Todos os KPIs e gráficos atualizam em tempo real

### Visões disponíveis

| Gráfico | Insight |
|---------|---------|
| Mapa de bolhas | Concentração geográfica das emissões |
| Top 10 bairros | Ranking por CO₂ total acumulado |
| Donut por veículo | Participação de cada categoria |
| Barras por zona | Sul lidera por distâncias maiores |
| Evolução semanal | Tendência ao longo do Q1 |
| CO₂ por hora | Picos de emissão às 7–9h e 17–20h |
| Distância × CO₂ | Identifica bairros com viagens longas |
| Potencial de redução | Impacto de 30 % da frota elétrica por bairro |

---

## Estrutura

```
analitcys-co2-bi/
├── dashboard/
│   ├── app.py              # Dashboard Dash/Plotly — filtros + callbacks
│   └── assets/style.css    # Dark theme · paleta 99
├── data/
│   └── bairros.csv         # 30 bairros de SP com coordenadas e pesos
├── sql/
│   ├── schema.sql          # Tabelas + views analíticas
│   └── queries.sql         # Queries comentadas: ranking, EV, hora de pico
├── powerbi/
│   ├── medidas_dax.txt     # Medidas DAX prontas para colar no Power BI
│   ├── tema_99.json        # Tema com paleta de cores da 99
│   └── export/             # CSVs prontos para importar no Power BI
├── generate_data.py        # Gerador de dados simulados + SQLite
├── export_powerbi.py       # Exporta CSVs para o Power BI
└── requirements.txt
```

---

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Gerar os dados simulados
python generate_data.py

# 3. Rodar o dashboard
python dashboard/app.py
```

### Power BI
```bash
python export_powerbi.py
```
Importar cada CSV de `powerbi/export/` via **Obter dados › Texto/CSV**.
As medidas DAX estão em `powerbi/medidas_dax.txt` e o tema em `powerbi/tema_99.json`.

---

## Stack

`Python` · `Pandas` · `SQLite` · `Plotly` · `Dash` · `Power BI`

---

## Metodologia

A emissão de CO₂ por corrida é calculada pela fórmula da CETESB:

```
CO₂ (g) = distância_km × 155
```

O potencial de redução com eletrificação parcial da frota considera:
- 30 % das corridas migradas para veículos elétricos
- Fator EV: 20 g CO₂/km (INEE · matriz elétrica brasileira)
- Redução por corrida EV: (155 − 20) / 155 ≈ **87 %**
- Redução total estimada: **~26 %** das emissões do período
