"""
MQM Dashboard v3 — 100% Streamlit nativo
Sem HTML customizado para interações críticas.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="MQM — Motor Quantitativo de Mercado",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo apenas para visual
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.block-container { padding-top: 1.2rem !important; }
header { visibility: hidden; }
[data-testid="stSidebar"] { min-width: 280px !important; max-width: 280px !important; }

.pill  { display:inline-block; padding:3px 12px; border-radius:20px;
         font-size:12px; font-weight:600; }
.pill-c { background:#14532d; color:#bbf7d0; }
.pill-v { background:#7f1d1d; color:#fecaca; }
.pill-n { background:#1e293b; color:#64748b; }
.sc { text-align:center; padding:10px 4px; border:1px solid #1e3a5f;
      border-radius:10px; background:rgba(30,37,53,0.5); }
.sc-tick { font-family:'IBM Plex Mono',monospace; font-size:13px;
           font-weight:600; color:#e2e8f0; margin-bottom:5px; }
.sc-prob { font-size:10px; color:#475569; font-family:'IBM Plex Mono',monospace; margin-top:5px; }
.status-bar { background:#0f172a; color:#22d3ee; padding:6px 16px;
  border-radius:8px; font-family:'IBM Plex Mono',monospace; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

TIPS = {
    "Ativo":        "O código da ação na B3. Ex: PETR4 = Petrobras, VALE3 = Vale, ITUB4 = Itaú.",
    "Horizonte":    "Dias úteis à frente previstos. D5 ≈ 1 semana · D14 ≈ 3 semanas · D28 ≈ 1 mês · D60 ≈ 3 meses. Horizontes mais longos tendem a ser mais confiáveis.",
    "Regime":       "Clima do mercado. LowVol = calmo, movimentos pequenos, típico de estabilidade. HighVol = agitado, grandes oscilações, típico de crises ou incertezas.",
    "Preço Atual":  "Última cotação em R$, atualizada a cada 15 min via Yahoo Finance. '—' indica que a cotação não foi obtida.",
    "Preço Alvo":   "Estimativa de preço no horizonte indicado, com base no retorno histórico do modelo. Use como referência, não como garantia.",
    "Recomendação": "Combina sinal do modelo com qualidade do backtest. COMPRA FORTE = PF≥2.5 + estável + acerto≥55%. NÃO COMPRAR = sem sinal claro.",
    "HR%":          "Taxa de Acerto: % de vezes que o modelo acertou a direção historicamente. Acima de 55% é bom. Lembre: acertar a direção não basta — o tamanho do ganho vs perda também importa.",
    "PF":           "Profit Factor = ganhos totais ÷ perdas totais. PF<1.0 = prejuízo. 1.0–1.5 = marginal. 1.5–2.5 = bom. >2.5 = excelente.",
    "Retorno%":     "Retorno acumulado simulado sobre R$100k com custos reais: corretagem 0,03%, slippage 0,05%, IR 15% sobre lucros.",
    "MaxDD%":       "Maior queda do pico ao fundo. Indica o pior cenário histórico — quanto você precisaria aguentar antes da recuperação.",
    "Sharpe":       "Retorno por unidade de risco (anualizado). <1.0 = não compensa. 1–2 = razoável. 2–4 = muito bom. >4 = excepcional.",
    "Ops":          "Número de operações no histórico. Quanto mais operações, mais estatisticamente confiável o resultado.",
    "Status":       "Estável = PF consistente entre períodos diferentes (mais confiável). Instável = alta variância entre períodos (maior risco de o modelo parar de funcionar).",
    "Score":        "Pontuação geral: PF × Sharpe × (HR/100). Quanto maior, melhor o conjunto de lucratividade + risco + precisão.",
}

def rec_label(sinal, pf, hr, instavel):
    pf = float(pf) if pf and not np.isnan(float(pf or 0)) and not np.isinf(float(pf or 0)) else 0
    hr = float(hr or 0)
    if sinal == "COMPRA":
        if pf >= 2.5 and not instavel and hr >= 55: return "🟢 COMPRA FORTE"
        elif pf >= 1.5 and hr >= 50:                return "🟩 COMPRA MODERADA"
        else:                                        return "🟡 COMPRA C/ RISCO"
    elif sinal == "VENDA":
        if pf >= 2.5 and not instavel and hr >= 55: return "🔴 VENDA URGENTE"
        else:                                        return "🟠 VENDA RISCO"
    return "⬜ NÃO COMPRAR"

def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
    return f"+{v:.1f}%" if float(v) >= 0 else f"{v:.1f}%"

def fmt_brl(v):
    return f"R${v:,.2f}" if v else "—"

# ─────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    csv = os.path.join(SCRIPT_DIR, "mqm_v64_operaveis.csv")
    if os.path.exists(csv):
        return pd.read_csv(csv, sep=";"), "real"
    rows = [
        ("PETR4","D5","LowVol",56.1,611,1.46,1.89,1.34,12,False,96.9,-15.1,2.36,196861,1.94),
        ("PETR4","D14","LowVol",61.0,700,1.74,4.14,4.94,13,True,1937.4,-32.1,3.02,2037430,3.21),
        ("PETR4","D28","LowVol",59.1,706,2.04,11.9,22.4,13,True,None,-41.8,3.44,None,4.15),
        ("PETR4","D60","LowVol",51.4,313,2.13,1.26,0.32,5,False,1632.0,-18.3,4.26,1732000,4.66),
        ("VALE3","D14","HighVol",73.9,130,11.83,109.8,152.4,3,True,121.8,-7.5,11.14,221808,82.29),
        ("VALE3","D28","LowVol",59.5,385,2.61,3.48,3.63,6,True,405.3,-18.2,5.52,505297,8.57),
        ("VALE3","D28","HighVol",84.5,58,2.61,None,None,1,True,7.1,-4.0,6.21,107119,13.70),
        ("ITUB4","D14","LowVol",60.4,766,2.21,21.9,66.7,15,True,324.5,-37.3,3.49,424500,4.65),
        ("ITUB4","D28","LowVol",46.3,287,2.99,2.45,2.35,5,False,163.5,-17.3,4.17,263521,5.78),
        ("BBAS3","D5","HighVol",62.5,64,2.20,None,None,1,True,2.2,-0.9,3.52,102156,4.85),
        ("BBAS3","D14","LowVol",58.4,615,2.01,45.5,134.7,11,True,252.8,-30.7,3.96,352775,4.65),
        ("BBAS3","D28","LowVol",49.0,488,2.05,5.32,6.79,9,True,718.3,-32.8,3.04,818297,3.06),
        ("BBAS3","D60","LowVol",46.1,232,4.90,9.70,15.6,4,True,223.7,-33.7,5.54,323738,12.53),
        ("MGLU3","D14","LowVol",57.6,469,1.54,10.1,24.6,9,True,325.3,-32.3,2.19,425336,1.93),
        ("MGLU3","D60","LowVol",45.6,228,1.88,0.21,0.10,3,False,620.7,-43.8,2.91,720677,2.50),
        ("SUZB3","D60","LowVol",59.4,384,2.76,20.0,33.4,7,True,1044.4,-48.5,5.79,1144351,9.49),
        ("ABEV3","D60","LowVol",53.3,214,30.56,51.2,68.6,4,True,180.8,-5.8,6.15,280767,32.76),
        ("VIVT3","D14","HighVol",84.0,81,31.98,None,None,1,True,31.8,-0.8,11.29,131768,94.75),
        ("GGBR4","D60","LowVol",51.3,515,1.72,3.42,3.39,10,False,1339.5,-56.4,3.09,1439542,2.73),
    ]
    cols = ["Ativo","Horizonte","Regime","HitRate","Operacoes","ProfitFactor",
            "PF_Folds_Mean","PF_Folds_Std","N_Folds","Instavel","Retorno_pct",
            "MaxDrawdown","Sharpe","Capital_Final","Score"]
    return pd.DataFrame(rows, columns=cols), "demo"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_prices(ativos):
    import yfinance as yf
    out = {}
    for a in ativos:
        try:
            fi = yf.Ticker(f"{a}.SA").fast_info
            p  = getattr(fi,"last_price",None) or getattr(fi,"regular_market_price",None)
            out[a] = round(float(p),2) if p else None
        except Exception:
            out[a] = None
    return out


@st.cache_data(ttl=600, show_spinner=False)
def fetch_candles(ativo, period, interval):
    import yfinance as yf
    try:
        ticker = f"{ativo}.SA"
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False, actions=False)
        if df is None or df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Garante colunas OHLCV presentes
        required = ["Open","High","Low","Close"]
        if not all(c in df.columns for c in required):
            return pd.DataFrame()
        df = df.dropna(subset=["Close"])
        return df
    except Exception:
        return pd.DataFrame()


# Setor de cada ativo → ticker do ETF/índice setorial B3
SETOR_MAP = {
    "PETR4": ("Petróleo & Gás",    "PETR3.SA"),       # próprio setor = PETR3 como proxy
    "VALE3": ("Mineração",         "VALE5.SA"),
    "ITUB4": ("Bancos",            "BPAC11.SA"),       # proxy setor bancário
    "BBAS3": ("Bancos",            "BPAC11.SA"),
    "BBDC4": ("Bancos",            "BPAC11.SA"),
    "MGLU3": ("Varejo",            "VVAR3.SA"),
    "SUZB3": ("Papel & Celulose",  "KLBN11.SA"),
    "ABEV3": ("Bebidas",           "ABEV3.SA"),        # sem proxy melhor
    "VIVT3": ("Telecom",           "TIMS3.SA"),
    "GGBR4": ("Siderurgia",        "CSNA3.SA"),
    "LREN3": ("Varejo Moda",       "AMAR3.SA"),
    "WEGE3": ("Máquinas",          "EGIE3.SA"),
}

IBOV_TICKER = "^BVSP"


@st.cache_data(ttl=600, show_spinner=False)
def fetch_benchmark(period, interval):
    """Busca IBOV para sobreposição no gráfico."""
    import yfinance as yf
    try:
        df = yf.download(IBOV_TICKER, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def fetch_setor(setor_ticker, period, interval):
    """Busca linha do setor para sobreposição."""
    import yfinance as yf
    try:
        df = yf.download(setor_ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


def normalizar(series):
    """Normaliza série para base 100 (para comparação visual)."""
    s = series.dropna()
    if len(s) == 0 or s.iloc[0] == 0:
        return series
    return (series / s.iloc[0]) * 100


@st.cache_data(ttl=1800, show_spinner=False)
def gerar_analise_ia(ativo, sinal, rec, pf, hr, regime, retorno, dd, horizonte):
    """
    Gera análise contextual do ativo via Claude API.
    Combina dados técnicos do modelo + busca de contexto de mercado.
    Cache de 30 min para não sobrecarregar a API.
    """
    try:
        import requests as req
        prompt = f"""Você é um analista de mercado financeiro brasileiro experiente.
Analise o ativo {ativo} com base nos seguintes dados do modelo quantitativo MQM:

- Sinal atual: {sinal}
- Recomendação: {rec}
- Horizonte: {horizonte}
- Regime de volatilidade: {regime}
- Profit Factor histórico: {pf:.2f}
- Taxa de acerto histórica: {hr:.1f}%
- Retorno simulado: {retorno}
- Máximo Drawdown: {dd}

Escreva uma análise curta e objetiva (máximo 4 linhas) explicando:
1. O que a tendência técnica indica
2. Qual o principal risco ou oportunidade no momento
3. Contexto macroeconômico/setorial relevante para esse ativo agora (Brasil 2025-2026: Selic em 13.25%, dólar alto, commodities, etc.)

Seja específico para {ativo}. Não repita os números — interprete-os.
Escreva em português, tom profissional mas acessível."""

        resp = req.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=20
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["content"][0]["text"].strip()
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────

df_all, fonte = load_data()
ativos_list   = sorted(df_all["Ativo"].unique().tolist())

with st.spinner("Buscando cotações..."):
    prices = fetch_prices(ativos_list)

SINAIS = {
    "PETR4":("VENDA",0.3021,"LowVol"),  "VALE3":("VENDA",0.2947,"LowVol"),
    "ITUB4":("COMPRA",0.9625,"LowVol"), "BBAS3":("VENDA",0.1620,"HighVol"),
    "MGLU3":("NEUTRO",0.4415,"LowVol"), "SUZB3":("VENDA",0.3028,"LowVol"),
    "ABEV3":("COMPRA",0.5800,"LowVol"), "VIVT3":("COMPRA",0.6200,"HighVol"),
    "GGBR4":("COMPRA",0.6047,"LowVol"), "LREN3":("NEUTRO",0.4814,"LowVol"),
}

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────

col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("### 📈 MQM — Painel de Sinais & Risco")
with col_h2:
    st.markdown(f"""<div class="status-bar" style="margin-top:6px">
        ● ATIVO &nbsp;|&nbsp; {datetime.now().strftime('%d/%m/%Y %H:%M')}
        &nbsp;|&nbsp; SELIC 13.25% &nbsp;|&nbsp; {fonte.upper()}
    </div>""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────

n_c = sum(1 for v in SINAIS.values() if v[0]=="COMPRA")
n_v = sum(1 for v in SINAIS.values() if v[0]=="VENDA")
best_pf = df_all["ProfitFactor"].replace([np.inf,-np.inf],np.nan).max()
best_sh = df_all["Sharpe"].replace([np.inf,-np.inf],np.nan).max()

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Combinações operáveis", len(df_all))
k2.metric("Melhor PF",    f"{best_pf:.2f}" if best_pf else "—")
k3.metric("Melhor Sharpe",f"{best_sh:.2f}" if best_sh else "—")
k4.metric("🟢 Compras hoje", n_c)
k5.metric("🔴 Vendas hoje",  n_v)

st.divider()

# ─────────────────────────────────────────────────────────────
# SINAIS DO DIA
# ─────────────────────────────────────────────────────────────

st.markdown("### Sinal do dia — D14")
cols_s = st.columns(len(SINAIS))
for i,(ativo,(sinal,prob,regime)) in enumerate(SINAIS.items()):
    with cols_s[i]:
        bar   = int(prob*100)
        bar_c = "#22c55e" if sinal=="COMPRA" else ("#f87171" if sinal=="VENDA" else "#334155")
        icon  = "▲" if sinal=="COMPRA" else ("▼" if sinal=="VENDA" else "─")
        cls   = "pill-c" if sinal=="COMPRA" else ("pill-v" if sinal=="VENDA" else "pill-n")
        st.markdown(f"""<div class="sc">
          <div class="sc-tick">{ativo}</div>
          <span class="pill {cls}">{icon} {sinal}</span>
          <div class="sc-prob">{prob:.4f}</div>
          <div style="margin-top:4px;background:#1e293b;border-radius:3px;height:3px">
            <div style="width:{bar}%;height:3px;border-radius:3px;background:{bar_c}"></div>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# SIDEBAR — FILTROS
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🎛️ Filtros")
    st.divider()

    f_ativo = st.multiselect(
        "Ativo", ativos_list, default=ativos_list,
        help="Selecione um ou mais ativos para filtrar"
    )
    f_hor = st.multiselect(
        "Horizonte", ["D5","D14","D28","D60"],
        default=["D5","D14","D28","D60"],
        help="D5=1 semana · D14=3 semanas · D28=1 mês · D60=3 meses"
    )
    f_reg = st.multiselect(
        "Regime", ["LowVol","HighVol"],
        default=["LowVol","HighVol"],
        help="LowVol = mercado calmo · HighVol = mercado agitado"
    )

    st.markdown("**Métricas mínimas**")
    pf_min = st.slider("Profit Factor mín.", 1.0, 10.0, 1.2, 0.1,
        help="Filtra apenas combinações com PF acima deste valor")
    sh_min = st.slider("Sharpe mín.", 0.0, 10.0, 0.0, 0.5,
        help="Filtra pelo índice de Sharpe mínimo")
    hr_min = st.slider("Hit Rate% mín.", 0.0, 100.0, 0.0, 5.0,
        help="Filtra pela taxa de acerto mínima")

    st.markdown("**Qualidade & Sinal**")
    f_est = st.selectbox(
        "Status do modelo",
        ["Todos","✓ Estável","⚠ Instável"],
        help="Estável = PF consistente entre períodos diferentes"
    )
    REC_OPTS = ["Todas","🟢 COMPRA FORTE","🟩 COMPRA MODERADA","🟡 COMPRA C/ RISCO",
                "⬜ NÃO COMPRAR","🟠 VENDA RISCO","🔴 VENDA URGENTE"]
    f_rec = st.selectbox(
        "Recomendação",
        REC_OPTS,
        help="Filtra pelo tipo de recomendação do modelo"
    )

    st.divider()
    st.caption("MQM v6.4 · Não constitui recomendação de investimento")


tab1, tab2, tab3 = st.tabs(["📊 Combinações & Gráfico", "❓ Guia das colunas", "🎯 Sizing"])

# ═══════════════════════════════════════
with tab1:

    # ── Filtros definidos na sidebar (ver bloco with st.sidebar acima)
    # As variáveis f_ativo, f_hor, f_reg, pf_min, sh_min, hr_min, f_est, f_rec
    # já foram definidas antes desta tab

    # ── APPLY
    df = df_all.copy()
    if f_ativo: df = df[df["Ativo"].isin(f_ativo)]
    if f_hor:   df = df[df["Horizonte"].isin(f_hor)]
    if f_reg:   df = df[df["Regime"].isin(f_reg)]
    df = df[df["ProfitFactor"].fillna(0).replace([np.inf,-np.inf],0) >= pf_min]
    df = df[df["Sharpe"].fillna(0) >= sh_min]
    df = df[df["HitRate"].fillna(0) >= hr_min]
    if f_est == "✓ Estável":  df = df[df["Instavel"]==False]
    if f_est == "⚠ Instável": df = df[df["Instavel"]==True]
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)

    # Aplica filtro de recomendação (precisa calcular rec antecipado)
    if f_rec != "Todas":
        rec_filter = []
        for _, r in df.iterrows():
            sd  = SINAIS.get(r["Ativo"], ("NEUTRO",0.5,"LowVol"))
            rec = rec_label(sd[0], r.get("ProfitFactor"), float(r.get("HitRate") or 0), bool(r.get("Instavel",True)))
            rec_filter.append(rec == f_rec)
        df = df[rec_filter].reset_index(drop=True)

    st.caption(f"{len(df)} combinações encontradas")

    if df.empty:
        st.info("Nenhuma combinação com os filtros selecionados.")
    else:
        # ── BUILD DISPLAY DATAFRAME
        rows = []
        for _, r in df.iterrows():
            ativo = r["Ativo"]
            hor   = r["Horizonte"]
            pf_v  = r.get("ProfitFactor")
            hr_v  = float(r.get("HitRate") or 0)
            ret_v = r.get("Retorno_pct")
            dd_v  = r.get("MaxDrawdown")
            sh_v  = float(r.get("Sharpe") or 0)
            sc_v  = float(r.get("Score") or 0)
            inst  = bool(r.get("Instavel", True))

            preco = prices.get(ativo)
            alvo  = None
            if preco and ret_v and not np.isnan(float(ret_v)):
                h_d   = int(hor.replace("D",""))
                radj  = float(ret_v)/100/5*(h_d/252)
                radj  = max(min(radj,1.5),-0.45)
                alvo  = round(preco*(1+radj), 2)

            sinal_data = SINAIS.get(ativo, ("NEUTRO",0.5,"LowVol"))
            rec = rec_label(sinal_data[0], pf_v, hr_v, inst)

            rows.append({
                "Ativo":          ativo,
                "Horizonte":      hor,
                "Regime":         r.get("Regime",""),
                "Preço Atual":    fmt_brl(preco),
                "Preço Alvo":     fmt_brl(alvo),
                "Recomendação":   rec,
                "HR%":            f"{hr_v:.1f}",
                "PF":             f"{pf_v:.2f}" if pf_v and not np.isnan(float(pf_v or 0)) and not np.isinf(float(pf_v or 0)) else "—",
                "Retorno%":       fmt_pct(float(ret_v) if ret_v else None),
                "MaxDD%":         fmt_pct(float(dd_v) if dd_v else None),
                "Sharpe":         f"{sh_v:.2f}",
                "Ops":            int(r.get("Operacoes") or 0),
                "Status":         "✓ estável" if not inst else "⚠ instável",
                "Score":          f"{sc_v:.2f}",
            })

        df_display = pd.DataFrame(rows)
        st.dataframe(
            df_display,
            use_container_width=True,
            height=420,
            column_config={
                "Ativo":        st.column_config.TextColumn("Ativo", help=TIPS["Ativo"], width="small"),
                "Horizonte":    st.column_config.TextColumn("Horizonte", help=TIPS["Horizonte"], width="small"),
                "Regime":       st.column_config.TextColumn("Regime", help=TIPS["Regime"], width="small"),
                "Preço Atual":  st.column_config.TextColumn("Preço Atual", help=TIPS["Preço Atual"]),
                "Preço Alvo":   st.column_config.TextColumn("Preço Alvo", help=TIPS["Preço Alvo"]),
                "Recomendação": st.column_config.TextColumn("Recomendação", help=TIPS["Recomendação"], width="medium"),
                "HR%":          st.column_config.TextColumn("HR%", help=TIPS["HR%"], width="small"),
                "PF":           st.column_config.TextColumn("PF", help=TIPS["PF"], width="small"),
                "Retorno%":     st.column_config.TextColumn("Retorno%", help=TIPS["Retorno%"]),
                "MaxDD%":       st.column_config.TextColumn("MaxDD%", help=TIPS["MaxDD%"]),
                "Sharpe":       st.column_config.TextColumn("Sharpe", help=TIPS["Sharpe"], width="small"),
                "Ops":          st.column_config.NumberColumn("Ops", help=TIPS["Ops"], width="small"),
                "Status":       st.column_config.TextColumn("Status", help=TIPS["Status"]),
                "Score":        st.column_config.TextColumn("Score", help=TIPS["Score"], width="small"),
            },
            hide_index=True,
        )

        st.caption("💡 Passe o mouse sobre o nome de cada coluna para ver a explicação.")

        # ── ANÁLISE IA POR ATIVO
        st.markdown("#### 🤖 Análise contextual por ativo")
        st.caption("Selecione um ativo para ver a análise gerada por IA combinando dados técnicos e contexto de mercado.")

        opcoes_ia = sorted(list(set(r["Ativo"] for r in rows)))
        col_ia1, col_ia2 = st.columns([1, 3])
        with col_ia1:
            ativo_ia = st.selectbox("Ativo para análise:", opcoes_ia, key="sel_ia")
        with col_ia2:
            gerar = st.button("🔍 Gerar análise", key="btn_ia", use_container_width=True)

        if gerar and ativo_ia:
            row_ia = next((r for r in rows if r["Ativo"] == ativo_ia), None)
            if row_ia:
                sinal_ia   = SINAIS.get(ativo_ia, ("NEUTRO",0.5,"LowVol"))[0]
                rec_ia     = row_ia["Recomendação"]
                pf_ia      = float(row_ia["PF"]) if row_ia["PF"] != "—" else 1.0
                hr_ia      = float(row_ia["HR%"])
                regime_ia  = row_ia["Regime"]
                retorno_ia = row_ia["Retorno%"]
                dd_ia      = row_ia["MaxDD%"]
                hor_ia     = row_ia["Horizonte"]

                with st.spinner(f"Analisando {ativo_ia}..."):
                    analise = gerar_analise_ia(
                        ativo_ia, sinal_ia, rec_ia, pf_ia, hr_ia,
                        regime_ia, retorno_ia, dd_ia, hor_ia
                    )

                if analise:
                    sinal_color = "#22c55e" if sinal_ia=="COMPRA" else ("#f87171" if sinal_ia=="VENDA" else "#94a3b8")
                    st.markdown(f"""
                    <div style="background:rgba(15,23,42,0.8);border:1px solid #1e3a5f;
                        border-left:4px solid {sinal_color};border-radius:10px;
                        padding:16px 20px;margin:8px 0">
                      <div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:8px">
                        📋 {ativo_ia} · {hor_ia} · {rec_ia}
                      </div>
                      <div style="font-size:13px;color:#cbd5e1;line-height:1.7">{analise}</div>
                      <div style="font-size:10px;color:#334155;margin-top:8px">
                        Gerado por IA · Não constitui recomendação de investimento · {datetime.now().strftime("%d/%m/%Y %H:%M")}
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.info("Análise não disponível no momento. Verifique a conexão com a API.")

        st.divider()

        # ── SELEÇÃO DE LINHA → GRÁFICO
        st.markdown("#### 📈 Gráfico de preço")
        opcoes = [f"{r['Ativo']} · {r['Horizonte']} · {r['Regime']}" for r in rows]
        sel = st.selectbox("Selecione um ativo para ver o gráfico:", opcoes)

        if sel:
            ativo_sel = sel.split(" · ")[0]
            row_sel   = next(r for r in rows if r["Ativo"] == ativo_sel)

            # Métricas rápidas
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            m1.metric("Preço atual",  row_sel["Preço Atual"])
            m2.metric("Preço alvo",   row_sel["Preço Alvo"])
            m3.metric("PF",           row_sel["PF"])
            m4.metric("Hit Rate",     row_sel["HR%"]+"%")
            m5.metric("Max DD",       row_sel["MaxDD%"])
            m6.metric("Score",        row_sel["Score"])

            # Seletor de período
            period_map = {
                "⏱ Hora (hoje)":  ("1d",  "5m"),
                "📅 Diário (6m)":  ("6mo", "1d"),
                "📅 Semanal (2a)": ("2y",  "1wk"),
                "📅 Mensal (5a)":  ("5y",  "1mo"),
            }
            view = st.radio("Período:", list(period_map.keys()), horizontal=True)
            period, interval = period_map[view]

            gc1, gc2, gc3 = st.columns([1,1,3])
            with gc1:
                show_ibov  = st.checkbox("📊 IBOV", value=True)
            with gc2:
                setor_info = SETOR_MAP.get(ativo_sel)
                show_setor = st.checkbox(f"🏭 {setor_info[0] if setor_info else 'Setor'}", value=bool(setor_info))
            with gc3:
                normalizar_chart = st.checkbox("Base 100 (comparar em %)", value=False,
                    help="Normaliza todas as linhas para base 100 no início do período — facilita comparar desempenho relativo")

            with st.spinner(f"Carregando dados de {ativo_sel}..."):
                candles  = fetch_candles(ativo_sel, period, interval)
                ibov_df  = fetch_benchmark(period, interval) if show_ibov else pd.DataFrame()
                setor_df = fetch_setor(setor_info[1], period, interval) if (show_setor and setor_info) else pd.DataFrame()

            if candles.empty:
                st.warning(f"Dados de {ativo_sel} não disponíveis para este período. Tente outro horizonte.")
            else:
                fig = go.Figure()

                close = candles["Close"]

                if normalizar_chart:
                    # Modo normalizado: linhas simples base 100
                    y_ativo = normalizar(close)
                    fig.add_trace(go.Scatter(
                        x=candles.index, y=y_ativo,
                        mode="lines", name=ativo_sel,
                        line=dict(color="#3b82f6", width=2),
                    ))
                    y_label = "Base 100"
                else:
                    # Modo preço: candlestick
                    fig.add_trace(go.Candlestick(
                        x=candles.index,
                        open=candles["Open"], high=candles["High"],
                        low=candles["Low"],   close=close,
                        name=ativo_sel,
                        increasing_line_color="#22c55e", decreasing_line_color="#f87171",
                        increasing_fillcolor="#166534",  decreasing_fillcolor="#7f1d1d",
                    ))
                    # Volume
                    if "Volume" in candles.columns:
                        fig.add_trace(go.Bar(
                            x=candles.index, y=candles["Volume"],
                            name="Volume", yaxis="y2",
                            marker_color="rgba(99,102,241,0.18)", showlegend=False,
                        ))
                    # MA20
                    if len(candles) >= 20:
                        fig.add_trace(go.Scatter(
                            x=candles.index, y=close.rolling(20).mean(),
                            mode="lines", name="MA20",
                            line=dict(color="#f59e0b", width=1.5, dash="dot"),
                        ))
                    y_label = "Preço (R$)"

                # ── IBOV overlay
                if not ibov_df.empty and "Close" in ibov_df.columns:
                    ibov_close = ibov_df["Close"].reindex(candles.index, method="ffill").dropna()
                    if not ibov_close.empty:
                        y_ibov = normalizar(ibov_close) if normalizar_chart else ibov_close
                        ax = "y" if normalizar_chart else "y3"
                        fig.add_trace(go.Scatter(
                            x=ibov_close.index, y=y_ibov,
                            mode="lines", name="IBOV",
                            line=dict(color="#a855f7", width=1.5, dash="dash"),
                            yaxis=ax,
                        ))

                # ── Setor overlay
                if not setor_df.empty and "Close" in setor_df.columns:
                    setor_close = setor_df["Close"].reindex(candles.index, method="ffill").dropna()
                    if not setor_close.empty:
                        y_setor = normalizar(setor_close) if normalizar_chart else setor_close
                        ax = "y" if normalizar_chart else "y4"
                        fig.add_trace(go.Scatter(
                            x=setor_close.index, y=y_setor,
                            mode="lines", name=setor_info[0] if setor_info else "Setor",
                            line=dict(color="#06b6d4", width=1.5, dash="dashdot"),
                            yaxis=ax,
                        ))

                # Layout
                yaxis_cfg = dict(gridcolor="#1e2d4a", tickprefix="R$" if not normalizar_chart else "",
                                 ticksuffix="%" if normalizar_chart else "", side="right", title=y_label)

                layout_extra = {}
                if not normalizar_chart:
                    layout_extra["yaxis2"] = dict(overlaying="y", side="left", showgrid=False, showticklabels=False)
                    layout_extra["yaxis3"] = dict(overlaying="y", side="left", showgrid=False, showticklabels=False)
                    layout_extra["yaxis4"] = dict(overlaying="y", side="left", showgrid=False, showticklabels=False)

                fig.update_layout(
                    height=460,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15,23,42,0.9)",
                    font=dict(family="IBM Plex Sans", color="#94a3b8", size=12),
                    xaxis=dict(gridcolor="#1e2d4a", rangeslider=dict(visible=False)),
                    yaxis=yaxis_cfg,
                    legend=dict(orientation="h", y=1.03, bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                    margin=dict(l=0, r=0, t=10, b=0),
                    hovermode="x unified",
                    **layout_extra,
                )
                st.plotly_chart(fig, use_container_width=True)

                if normalizar_chart:
                    st.caption("Base 100: todas as linhas começam em 100 no início do período. Linhas acima = melhor desempenho relativo ao IBOV / setor.")

# ═══════════════════════════════════════
with tab2:
    st.markdown("### ❓ Guia completo das colunas")
    st.caption("Passe o mouse sobre qualquer coluna na tabela para ver a dica rápida. Aqui está a explicação completa de cada uma.")
    for col, tip in TIPS.items():
        with st.expander(f"**{col}**"):
            st.write(tip)

# ═══════════════════════════════════════
with tab3:
    st.markdown("### 🎯 Sizing — Posição recomendada por capital")
    st.caption("Kelly fracionado (25%) com teto de 20% do capital. Posição menor quando histórico instável.")

    cap = st.number_input("Seu capital (R$)", 10_000, 10_000_000, 100_000, 10_000, format="%d")

    df_sz = df_all[
        df_all["ProfitFactor"].fillna(0).replace([np.inf,-np.inf],0) >= 1.5
    ].sort_values("Score", ascending=False).head(8)

    CAPS = [50_000,100_000,250_000,500_000,1_000_000]

    for _, r in df_sz.iterrows():
        pf   = float(r.get("ProfitFactor") or 1.5)
        hr   = float(r.get("HitRate") or 50)/100
        ops  = int(r.get("Operacoes") or 100)
        inst = bool(r.get("Instavel", True))

        b = max(pf*(1-hr)/hr, 0.01)
        k = (hr*b-(1-hr))/b * 0.25
        if ops < 50: k = 0.02
        if inst:     k *= 0.7
        k = float(np.clip(k, 0.01, 0.20))

        sinal_d = SINAIS.get(r["Ativo"], ("NEUTRO",0.5,"LowVol"))
        rec = rec_label(sinal_d[0], pf, hr*100, inst)
        est = "✓ estável" if not inst else "⚠ instável"

        with st.expander(f"**{r['Ativo']}** · {r['Horizonte']} · {r['Regime']}  —  Kelly {k*100:.1f}%  ·  {est}  ·  {rec}"):
            cc = st.columns(len(CAPS))
            for j,(cap_ref,lbl) in enumerate(zip(CAPS,["R$50k","R$100k","R$250k","R$500k","R$1M"])):
                pos  = cap_ref * k
                stop = pos * 0.04
                cc[j].metric(lbl, f"R${pos:,.0f}", f"stop R${stop:,.0f}")

            pos_user = cap * k
            st.success(f"Com seu capital de R${cap:,.0f}: posição recomendada **R${pos_user:,.0f}** · stop **R${pos_user*0.04:,.0f}**")

# ── footer
st.divider()
st.caption(f"MQM v6.4 · Fonte: {fonte.upper()} · Não constitui recomendação de investimento · {datetime.now().strftime('%d/%m/%Y %H:%M')}")
