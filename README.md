# 🚗 Emissões de CO₂ por Bairro — São Paulo · 99

![Python](https://img.shields.io/badge/Python-3.10+-6366f1?style=flat&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Visualizações-a78bfa?style=flat&logo=plotly&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-SQLite-38bdf8?style=flat&logo=sqlite&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Pronto-F2C811?style=flat&logo=powerbi&logoColor=black)
![Status](https://img.shields.io/badge/Status-Concluído-38bdf8?style=flat)

Análise exploratória de emissões de CO₂ por corridas de transporte por aplicativo em São Paulo, com foco em identificar **onde é possível reduzir**.

---

## Sobre o Projeto

O transporte por aplicativo é uma das principais fontes de emissão de CO₂ nas grandes cidades brasileiras. Este projeto mapeia as emissões por bairro em São Paulo, identifica os pontos críticos por hora do dia e zona, e estima o impacto de uma transição parcial para veículos elétricos.

**Fator de emissão:** 155 g CO₂/km — ICCT Brasil (2023) · dado real  
**Fórmula:** CO₂ (g) = distância (km) × 155 · metodologia CETESB  
**Corridas:** Simuladas com distribuição realista por bairro, horário de pico e tipo de veículo*  
**Stack:** Python · Plotly · SQLite · pandas · Power BI

> *A 99 não disponibiliza dados de corridas publicamente. Este projeto aplica fatores de emissão reais a corridas simuladas para fins de demonstração.*

---

## Visualizações

![Mapa CO₂](graficos/01_mapa_co2_bairro.png)
![Top 10 Bairros](graficos/02_top10_bairros.png)
![CO₂ por Hora](graficos/06_co2_por_hora.png)
![Evolução Semanal](graficos/05_evolucao_semanal.png)
![Distância × CO₂](graficos/07_scatter_distancia_co2.png)
![Potencial de Redução](graficos/08_potencial_reducao_ev.png)

---

## 8 Gráficos Gerados

| # | Gráfico | O que responde |
|---|---------|----------------|
| 1 | Mapa de bolhas | Onde a emissão está concentrada geograficamente? |
| 2 | Top 10 bairros | Quais bairros acumulam mais CO₂? |
| 3 | CO₂ por veículo | Qual categoria emite mais? |
| 4 | CO₂ por zona | Qual região da cidade é mais crítica? |
| 5 | Evolução semanal | Como as emissões variaram ao longo do Q1 2024? |
| 6 | CO₂ por hora | Em quais horários a emissão é maior? |
| 7 | Distância × CO₂ | Zona Sul emite mais por ter corridas mais longas? |
| 8 | Potencial de redução | Onde focar para reduzir com 30 % da frota elétrica? |

---

## Principais Resultados

- **15,4 ton** de CO₂ emitidas em 10.000 corridas simuladas no Q1 2024
- **Zona Sul** lidera com folga — corridas mais longas devido à distância do centro
- **Vila Olímpia** e **Morumbi** no topo do ranking por distâncias médias elevadas
- Picos de emissão claros às **7–9h** (rush manhã) e **17–20h** (rush noite)
- Converter **30 % da frota para elétrico** reduziria ~**26 % das emissões** totais
- Corridas com **menos de 5 km** representam alto potencial de substituição modal

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Gerar os dados simulados + banco SQLite
python generate_data.py

# Gerar todos os gráficos em PNG
python gerar_graficos.py
```

Os gráficos são salvos em `graficos/`.

### Power BI

```bash
python export_powerbi.py
```

Importar cada CSV de `powerbi/export/` via **Obter dados › Texto/CSV**.  
Medidas DAX prontas em `powerbi/medidas_dax.txt` · tema em `powerbi/tema_99.json`.

---

## Estrutura

```
analitcys-co2-bi/
├── graficos/               # 8 gráficos exportados em PNG
├── data/
│   └── bairros.csv         # 30 bairros de SP com coordenadas e peso de demanda
├── sql/
│   ├── schema.sql          # Tabelas + views analíticas
│   └── queries.sql         # Queries comentadas: ranking, hora de pico, potencial EV
├── powerbi/
│   ├── medidas_dax.txt     # Medidas DAX prontas para colar no Power BI
│   ├── tema_99.json        # Tema com paleta de cores da 99
│   └── export/             # CSVs prontos para importar no Power BI
├── generate_data.py        # Gerador de dados simulados + banco SQLite
├── gerar_graficos.py       # Gera os 8 gráficos em PNG (dark theme · paleta 99)
├── export_powerbi.py       # Exporta CSVs para o Power BI
└── requirements.txt
```

---

## 🛠️ Ferramentas Utilizadas

| Categoria | Ferramenta | Uso |
|-----------|------------|-----|
| Linguagem | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | Desenvolvimento completo |
| Visualização | ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white) | Gráficos e mapa · export PNG |
| Dados | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white) | Manipulação e análise |
| Numérico | ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white) | Simulação e cálculos |
| Banco de dados | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white) | Armazenamento + views analíticas |
| BI | ![Power BI](https://img.shields.io/badge/Power%20BI-F2C811?style=flat&logo=powerbi&logoColor=black) | Relatórios e medidas DAX |
| Versionamento | ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) | Controle de versão |
| Repositório | ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white) | Hospedagem do projeto |

---

*Projeto desenvolvido para portfólio de análise de dados — cenário de mobilidade urbana com fator de emissão real (ICCT Brasil, 2023).*
