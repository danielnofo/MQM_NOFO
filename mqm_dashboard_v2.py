"""
MQM Dashboard v2 — Streamlit
Motor Quantitativo de Mercado v6.4
"""
import warnings; warnings.filterwarnings("ignore")
import os, json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="MQM — Motor Quantitativo de Mercado",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
*, body { font-family: 'IBM Plex Sans', sans-serif; }

/* ── status bar */
.status-bar { background:#0f172a; color:#22d3ee; padding:6px 16px;
  border-radius:8px; font-family:'IBM Plex Mono',monospace;
  font-size:12px; letter-spacing:.05em; margin-bottom:16px; }

/* ── kpi card */
.kpi { background:rgba(30,37,53,0.6); border:1px solid #1e3a5f;
  border-radius:10px; padding:14px 18px; }
.kpi-label { font-size:10px; letter-spacing:.12em; text-transform:uppercase;
  color:#64748b; margin-bottom:4px; font-family:'IBM Plex Mono',monospace; }
.kpi-val { font-size:24px; font-weight:600; color:#e2e8f0; }
.kpi-val.g { color:#22c55e; } .kpi-val.r { color:#f87171; }

/* ── sinal pill */
.pill { display:inline-block; padding:3px 11px; border-radius:20px;
  font-size:12px; font-weight:600; }
.pill-c { background:#14532d; color:#bbf7d0; }
.pill-v { background:#7f1d1d; color:#fecaca; }
.pill-n { background:#1e293b; color:#64748b; }

/* ── sinal card */
.sc { text-align:center; padding:10px 4px; border:1px solid #1e3a5f;
  border-radius:10px; background:rgba(30,37,53,0.5); cursor:default; }
.sc-tick { font-family:'IBM Plex Mono',monospace; font-size:13px;
  font-weight:600; color:#e2e8f0; margin-bottom:5px; }
.sc-prob { font-size:10px; color:#475569; font-family:'IBM Plex Mono',monospace; margin-top:5px; }

/* ── main table */
.gt { border-collapse:collapse; width:100%; font-size:13px; }
.gt thead th {
  background:#0f172a; color:#64748b; padding:9px 10px;
  font-size:10px; letter-spacing:.1em; text-transform:uppercase;
  font-family:'IBM Plex Mono',monospace; border-bottom:1px solid #1e3a5f;
  position:relative; white-space:nowrap; cursor:pointer; user-select:none;
}
.gt thead th:hover { color:#94a3b8; }
.gt thead th .sort-arrow { margin-left:4px; color:#334155; font-size:9px; }
.gt tbody tr { cursor:pointer; transition:background .15s; }
.gt tbody tr:hover td { background:rgba(37,99,235,0.08); }
.gt tbody tr.selected td { background:rgba(37,99,235,0.15);
  border-left:3px solid #3b82f6; }
.gt td { padding:9px 10px; border-bottom:1px solid #0f1929; color:#cbd5e1; }
.gt td:first-child { font-weight:600; color:#e2e8f0; font-family:'IBM Plex Mono',monospace; }

/* ── pf badge */
.pf { display:inline-block; padding:2px 8px; border-radius:10px;
  font-family:'IBM Plex Mono',monospace; font-size:12px; }
.pf-h { background:#14532d; color:#86efac; }
.pf-m { background:#713f12; color:#fde68a; }
.pf-l { background:#7f1d1d; color:#fca5a5; }

/* ── stability badge */
.stab-ok  { background:#14532d; color:#86efac; padding:2px 7px;
  border-radius:10px; font-size:11px; }
.stab-no  { background:#78350f; color:#fde68a; padding:2px 7px;
  border-radius:10px; font-size:11px; }

/* ── rec badge */
.rec { display:inline-block; padding:3px 9px; border-radius:10px;
  font-size:11px; font-weight:600; white-space:nowrap; }

/* ── tooltip */
.hdr-tip { display:inline-flex; align-items:center; gap:3px; }
.tip-i {
  font-size:9px; color:#64748b; background:rgba(100,116,139,0.2);
  border-radius:50%; width:15px; height:15px; display:inline-flex;
  align-items:center; justify-content:center; cursor:help; flex-shrink:0;
  font-weight:700;
}
#mqm-tip {
  display:none; position:fixed; z-index:2147483647;
  background:#0f172a; color:#e2e8f0;
  font-size:12px; font-family:'IBM Plex Sans',sans-serif;
  font-weight:400; text-transform:none; letter-spacing:0;
  padding:10px 14px; border-radius:8px; width:270px; line-height:1.6;
  border:1px solid #1e3a5f; box-shadow:0 8px 28px rgba(0,0,0,.7);
  white-space:normal; pointer-events:none;
}

/* ── filter chips */
.filter-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:12px; }
.f-chip { background:rgba(30,37,53,0.8); border:1px solid #1e3a5f;
  color:#94a3b8; padding:4px 12px; border-radius:20px;
  font-size:12px; cursor:pointer; }
.f-chip.active { background:#1d4ed8; border-color:#3b82f6; color:#fff; }

/* ── detail panel */
.det-panel { background:rgba(15,23,42,0.8); border:1px solid #1e3a5f;
  border-radius:12px; padding:16px; margin-top:12px; }

/* hide streamlit chrome */
[data-testid="stSidebar"] { display:none !important; width:0 !important; }
[data-testid="stSidebarNav"] { display:none !important; }
header { visibility:hidden; }
.block-container { padding-top:1rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def pf_badge(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return '<span style="color:#334155">—</span>'
    cls = "pf-h" if v >= 2.5 else ("pf-m" if v >= 1.5 else "pf-l")
    return f'<span class="pf {cls}">{v:.2f}</span>'

def rec_badge(label):
    cfg = {
        "COMPRA FORTE":    ("#052e16","#bbf7d0"),
        "COMPRA MODERADA": ("#14532d","#86efac"),
        "COMPRA C/ RISCO": ("#451a03","#fde68a"),
        "NÃO COMPRAR":     ("#1e293b","#475569"),
        "VENDA RISCO":     ("#431407","#fdba74"),
        "VENDA URGENTE":   ("#450a0a","#fca5a5"),
    }
    bg, fg = cfg.get(label, ("#1e293b","#475569"))
    return f'<span class="rec" style="background:{bg};color:{fg}">{label}</span>'

def pill(sinal):
    cls = "pill-c" if sinal=="COMPRA" else ("pill-v" if sinal=="VENDA" else "pill-n")
    icon = "▲" if sinal=="COMPRA" else ("▼" if sinal=="VENDA" else "─")
    return f'<span class="pill {cls}">{icon} {sinal}</span>'

def th(label, tip):
    safe = tip.replace('"','&quot;').replace("'","&#39;")
    return (f'<th><span class="hdr-tip">{label}'
            f'<span class="tip-i"'
            f' onmouseenter="showTip(event,\'{safe}\')"'
            f' onmouseleave="hideTip()">?</span>'
            f'</span></th>')

def fmt_pct(v, decimals=1):
    if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
    return f'+{v:.{decimals}f}%' if v >= 0 else f'{v:.{decimals}f}%'

def fmt_brl(v):
    if v is None: return "—"
    return f"R${v:,.2f}"

def classificar_rec(sinal, pf, hr, instavel):
    pf = pf if pf and not np.isnan(pf) and not np.isinf(pf) else 0
    if sinal == "COMPRA":
        if pf >= 2.5 and not instavel and hr >= 55: return "COMPRA FORTE"
        elif pf >= 1.5 and hr >= 50:                return "COMPRA MODERADA"
        else:                                        return "COMPRA C/ RISCO"
    elif sinal == "VENDA":
        if pf >= 2.5 and not instavel and hr >= 55: return "VENDA URGENTE"
        else:                                        return "VENDA RISCO"
    return "NÃO COMPRAR"


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    csv = os.path.join(SCRIPT_DIR, "mqm_v64_operaveis.csv")
    if os.path.exists(csv):
        return pd.read_csv(csv, sep=";"), "real"
    # Demo data
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
            p  = getattr(fi, "last_price", None) or getattr(fi, "regular_market_price", None)
            out[a] = round(float(p), 2) if p else None
        except Exception:
            out[a] = None
    return out


@st.cache_data(ttl=900, show_spinner=False)
def fetch_candles(ativo, period, interval):
    """Busca OHLCV para o gráfico de preço."""
    import yfinance as yf
    ticker = f"{ativo}.SA"
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────
df_all, fonte = load_data()
ativos_list   = sorted(df_all["Ativo"].unique().tolist())
prices        = fetch_prices(ativos_list)

SINAIS_DEMO = {
    "PETR4":("VENDA",0.3021,"LowVol"),  "VALE3":("VENDA",0.2947,"LowVol"),
    "ITUB4":("COMPRA",0.9625,"LowVol"), "BBAS3":("VENDA",0.1620,"HighVol"),
    "MGLU3":("NEUTRO",0.4415,"LowVol"), "SUZB3":("VENDA",0.3028,"LowVol"),
    "ABEV3":("NEUTRO",0.5276,"LowVol"), "VIVT3":("NEUTRO",0.4254,"LowVol"),
    "GGBR4":("COMPRA",0.6047,"LowVol"), "LREN3":("NEUTRO",0.4814,"LowVol"),
}

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;
    border-bottom:1px solid #1e3a5f;padding-bottom:10px;margin-bottom:16px">
  <div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
        letter-spacing:.15em;color:#334155;text-transform:uppercase">Motor Quantitativo de Mercado</div>
    <div style="font-size:26px;font-weight:600;color:#e2e8f0;letter-spacing:-.5px">
        Painel de Sinais & Risco</div>
  </div>
  <div class="status-bar">● ATIVO &nbsp;|&nbsp; {datetime.now().strftime('%d/%m/%Y %H:%M')}
    &nbsp;|&nbsp; SELIC 13.25% &nbsp;|&nbsp; FONTE: {fonte.upper()}</div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────────────────────
n_op  = len(df_all)
best_pf = df_all["ProfitFactor"].replace([np.inf,-np.inf],np.nan).max()
best_sh = df_all["Sharpe"].replace([np.inf,-np.inf],np.nan).max()
n_c = sum(1 for v in SINAIS_DEMO.values() if v[0]=="COMPRA")
n_v = sum(1 for v in SINAIS_DEMO.values() if v[0]=="VENDA")

c1,c2,c3,c4,c5 = st.columns(5)
for col, lbl, val, cls in [
    (c1,"Combinações operáveis", str(n_op), ""),
    (c2,"Melhor PF", f"{best_pf:.2f}" if best_pf else "—", "g"),
    (c3,"Melhor Sharpe", f"{best_sh:.2f}" if best_sh else "—", "g"),
    (c4,"Compras hoje", str(n_c), "g"),
    (c5,"Vendas hoje",  str(n_v), "r"),
]:
    col.markdown(f'<div class="kpi"><div class="kpi-label">{lbl}</div>'
                 f'<div class="kpi-val {cls}">{val}</div></div>',
                 unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SINAIS DO DIA
# ─────────────────────────────────────────────────────────────
st.markdown("### Sinal do dia — D14")
cols_s = st.columns(len(SINAIS_DEMO))
for i, (ativo, (sinal, prob, regime)) in enumerate(SINAIS_DEMO.items()):
    with cols_s[i]:
        bar = int(prob*100)
        bar_c = "#22c55e" if sinal=="COMPRA" else ("#f87171" if sinal=="VENDA" else "#334155")
        icon  = "▲" if sinal=="COMPRA" else ("▼" if sinal=="VENDA" else "─")
        pill_cls = "pill-c" if sinal=="COMPRA" else ("pill-v" if sinal=="VENDA" else "pill-n")
        st.markdown(f"""
        <div class="sc">
          <div class="sc-tick">{ativo}</div>
          <span class="pill {pill_cls}">{icon} {sinal}</span>
          <div class="sc-prob">{prob:.4f}</div>
          <div style="margin-top:4px;background:#1e293b;border-radius:3px;height:3px">
            <div style="width:{bar}%;height:3px;border-radius:3px;background:{bar_c}"></div>
          </div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊 Combinações operáveis", "🎯 Sizing por ativo"])

with tab1:

    # ── FILTROS INLINE
    st.markdown("**Filtros**")
    fc1,fc2,fc3,fc4,fc5,fc6 = st.columns([1.5,1.5,1,1,1,1])
    with fc1:
        f_ativo = st.multiselect("Ativo", ativos_list, default=ativos_list, key="f_ativo")
    with fc2:
        f_hor = st.multiselect("Horizonte", ["D5","D14","D28","D60"],
                                default=["D5","D14","D28","D60"], key="f_hor")
    with fc3:
        f_reg = st.multiselect("Regime", ["LowVol","HighVol"],
                                default=["LowVol","HighVol"], key="f_reg")
    with fc4:
        pf_min = st.number_input("PF mínimo", 1.0, 10.0, 1.2, 0.1, key="pf_min")
    with fc5:
        sh_min = st.number_input("Sharpe mín.", 0.0, 10.0, 0.0, 0.5, key="sh_min")
    with fc6:
        f_est = st.selectbox("Status", ["Todos","✓ Estável","⚠ Instável"], key="f_est")

    # ── APPLY FILTERS
    df = df_all.copy()
    if f_ativo: df = df[df["Ativo"].isin(f_ativo)]
    if f_hor:   df = df[df["Horizonte"].isin(f_hor)]
    if f_reg:   df = df[df["Regime"].isin(f_reg)]
    df = df[df["ProfitFactor"].fillna(0) >= pf_min]
    df = df[df["Sharpe"].fillna(0) >= sh_min]
    if f_est == "✓ Estável":   df = df[df["Instavel"]==False]
    if f_est == "⚠ Instável":  df = df[df["Instavel"]==True]
    df = df.sort_values("Score", ascending=False).reset_index(drop=True)

    st.markdown(f"<span style='font-size:12px;color:#475569'>{len(df)} combinações encontradas</span>",
                unsafe_allow_html=True)

    if df.empty:
        st.info("Nenhuma combinação com os filtros aplicados.")
    else:
        # ── selected row state
        if "selected_idx" not in st.session_state:
            st.session_state.selected_idx = None

        # ── COLUMN DEFS with tooltips
        TIPS = {
            "Ativo":       "O código da ação na B3. Ex: PETR4 = Petrobras, VALE3 = Vale.",
            "Horizonte":   "Dias úteis à frente previstos. D5 ≈ 1 sem · D14 ≈ 3 sem · D28 ≈ 1 mês · D60 ≈ 3 meses.",
            "Regime":      "Clima do mercado. LowVol = calmo, movimentos pequenos. HighVol = agitado, grandes oscilações.",
            "Preço":       "Última cotação em R$, atualizada a cada 15 min via Yahoo Finance.",
            "Alvo":        "Estimativa de preço no horizonte. Calculada pelo retorno histórico médio do modelo.",
            "Rec.":        "Recomendação combinando sinal do modelo com qualidade do backtest histórico.",
            "HR%":         "Taxa de Acerto: % de vezes que o modelo acertou a direção. >55% é bom.",
            "PF":          "Profit Factor = ganhos totais ÷ perdas totais. >2.5 excelente. <1.0 = prejuízo.",
            "Retorno":     "Retorno simulado sobre R$100k com corretagem, slippage e IR descontados.",
            "MaxDD":       "Maior queda do pico ao fundo. Indica o pior cenário histórico.",
            "Sharpe":      "Retorno por unidade de risco. >2 = bom. >4 = excepcional.",
            "Ops":         "Número de operações no histórico. Mais ops = resultado mais confiável.",
            "Status":      "✓ Estável = PF consistente entre períodos. ⚠ Instável = alta variância entre períodos.",
            "Score":       "Pontuação geral: PF × Sharpe × HR. Quanto maior, melhor o conjunto.",
        }

        hdr = "".join(th(k, TIPS[k]) for k in TIPS)

        rows_html = ""
        for i, r in df.iterrows():
            ativo  = r["Ativo"]
            hor    = r["Horizonte"]
            regime = r["Regime"]
            pf_v   = r.get("ProfitFactor")
            hr_v   = float(r.get("HitRate", 0) or 0)
            ret_v  = r.get("Retorno_pct")
            dd_v   = r.get("MaxDrawdown")
            sh_v   = r.get("Sharpe", 0) or 0
            sc_v   = r.get("Score", 0) or 0
            ops_v  = int(r.get("Operacoes", 0) or 0)
            inst   = bool(r.get("Instavel", True))

            preco  = prices.get(ativo)
            preco_s= fmt_brl(preco)

            # Alvo: projeto retorno histórico no horizonte
            alvo_s = "—"
            if preco and ret_v and not np.isnan(float(ret_v or 0)):
                h_d     = int(hor.replace("D",""))
                ret_adj = float(ret_v)/100 / 5 * (h_d/252)
                ret_adj = max(min(ret_adj, 1.5), -0.45)
                alvo    = preco * (1 + ret_adj)
                var     = ret_adj * 100
                vc      = "#22c55e" if var >= 0 else "#f87171"
                alvo_s  = f"R${alvo:.2f} <span style='color:{vc};font-size:10px'>{var:+.1f}%</span>"

            # Sinal
            sinal_data = SINAIS_DEMO.get(ativo, ("NEUTRO",0.5,"LowVol"))
            rec = classificar_rec(sinal_data[0], pf_v, hr_v, inst)

            ret_s  = fmt_pct(float(ret_v) if ret_v else None)
            ret_c  = "#22c55e" if ret_v and float(ret_v) >= 0 else "#f87171"
            dd_s   = fmt_pct(float(dd_v) if dd_v else None)
            st_badge = '<span class="stab-ok">✓ estável</span>' if not inst else '<span class="stab-no">⚠ instável</span>'
            sel_cls  = "selected" if st.session_state.selected_idx == i else ""
            reg_c    = "#f87171" if regime=="HighVol" else "#94a3b8"

            rows_html += f"""<tr class="{sel_cls}" onclick="selectRow({i})">
              <td>{ativo}</td>
              <td style='font-family:monospace;color:#818cf8'>{hor}</td>
              <td style='font-size:11px;color:{reg_c}'>{regime}</td>
              <td style='font-family:monospace'>{preco_s}</td>
              <td style='font-family:monospace'>{alvo_s}</td>
              <td>{rec_badge(rec)}</td>
              <td>{hr_v:.1f}%</td>
              <td>{pf_badge(pf_v)}</td>
              <td style='color:{ret_c};font-weight:500'>{ret_s}</td>
              <td style='color:#f87171'>{dd_s}</td>
              <td style='font-family:monospace'>{sh_v:.2f}</td>
              <td style='color:#475569'>{ops_v}</td>
              <td>{st_badge}</td>
              <td style='color:#818cf8;font-weight:500'>{sc_v:.2f}</td>
            </tr>"""

        # JS for row selection
        js_select = """
        <script>
        function selectRow(idx) {
            const rows = document.querySelectorAll('.gt tbody tr');
            rows.forEach((r,i) => {
                if(i===idx) r.classList.toggle('selected');
                else r.classList.remove('selected');
            });
            // Streamlit component communication via query param trick
            const url = new URL(window.location);
            url.searchParams.set('sel', idx);
            window.history.replaceState({}, '', url);
            // Try streamlit setComponentValue if available
            try {
                window.parent.postMessage({type:'streamlit:setComponentValue', value:idx}, '*');
            } catch(e){}
        }
        </script>"""

        st.markdown("""
        <div id="mqm-tip"></div>
        <script>
        (function(){
          var tip = document.getElementById('mqm-tip');
          if(!tip){ tip=document.createElement('div'); tip.id='mqm-tip';
            document.body.appendChild(tip); }
          function showTip(e,txt){
            tip.innerHTML = txt;
            tip.style.display = 'block';
            moveTip(e);
          }
          function moveTip(e){
            var x=e.clientX+14, y=e.clientY+16;
            if(x+280>window.innerWidth) x=window.innerWidth-285;
            if(y+200>window.innerHeight) y=e.clientY-205;
            tip.style.left=x+'px'; tip.style.top=y+'px';
          }
          function hideTip(){ tip.style.display='none'; }
          window.showTip=showTip; window.hideTip=hideTip;
          document.addEventListener('scroll', hideTip, true);
        })();
        </script>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <table class="gt">
          <thead><tr>{hdr}</tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        {js_select}""", unsafe_allow_html=True)

        # ── ROW CLICK via Streamlit selectbox (reliable fallback)
        st.markdown("<br>", unsafe_allow_html=True)
        sel_options = [f"{r['Ativo']} · {r['Horizonte']} · {r['Regime']}"
                       for _, r in df.iterrows()]
        sel_label = st.selectbox(
            "🔍 Ver detalhe + gráfico de preço:",
            ["— selecione uma linha —"] + sel_options,
            key="row_select"
        )

        if sel_label != "— selecione uma linha —":
            idx = sel_options.index(sel_label)
            row = df.iloc[idx]
            ativo_sel = row["Ativo"]

            st.markdown('<div class="det-panel">', unsafe_allow_html=True)

            # ── metrics strip
            m1,m2,m3,m4,m5,m6 = st.columns(6)
            for col, lbl, val in [
                (m1, "PF",          f"{row['ProfitFactor']:.2f}" if row['ProfitFactor'] else "—"),
                (m2, "Hit Rate",    f"{row['HitRate']:.1f}%"),
                (m3, "Sharpe",      f"{row['Sharpe']:.2f}"),
                (m4, "Max DD",      f"{row['MaxDrawdown']:.1f}%" if row['MaxDrawdown'] else "—"),
                (m5, "Retorno sim.",f"{row['Retorno_pct']:.0f}%" if row['Retorno_pct'] else "—"),
                (m6, "Score",       f"{row['Score']:.2f}"),
            ]:
                col.metric(lbl, val)

            # ── price chart
            st.markdown(f"#### Gráfico de preço — {ativo_sel}")
            period_map = {
                "Hora (só hoje)": ("1d",  "1m"),
                "Diário":         ("6mo", "1d"),
                "Semanal":        ("2y",  "1wk"),
                "Mensal":         ("5y",  "1mo"),
            }
            view = st.radio("Período:", list(period_map.keys()),
                            horizontal=True, key="chart_view")
            period, interval = period_map[view]

            with st.spinner(f"Carregando {ativo_sel}..."):
                candles = fetch_candles(ativo_sel, period, interval)

            if candles.empty:
                st.warning("Dados não disponíveis para este ativo no período selecionado.")
            else:
                fig = go.Figure()

                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=candles.index,
                    open=candles["Open"], high=candles["High"],
                    low=candles["Low"],   close=candles["Close"],
                    name=ativo_sel,
                    increasing_line_color="#22c55e",
                    decreasing_line_color="#f87171",
                    increasing_fillcolor="#166534",
                    decreasing_fillcolor="#7f1d1d",
                ))

                # Volume bars
                if "Volume" in candles.columns:
                    fig.add_trace(go.Bar(
                        x=candles.index, y=candles["Volume"],
                        name="Volume", yaxis="y2",
                        marker_color="rgba(99,102,241,0.25)",
                        showlegend=False,
                    ))

                # MA20
                if len(candles) >= 20:
                    ma20 = candles["Close"].rolling(20).mean()
                    fig.add_trace(go.Scatter(
                        x=candles.index, y=ma20,
                        mode="lines", name="MA20",
                        line=dict(color="#f59e0b", width=1.5, dash="dot"),
                    ))

                fig.update_layout(
                    height=420,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15,23,42,0.8)",
                    font=dict(family="IBM Plex Sans", color="#94a3b8", size=12),
                    xaxis=dict(gridcolor="#1e2d4a", showgrid=True, rangeslider=dict(visible=False)),
                    yaxis=dict(gridcolor="#1e2d4a", showgrid=True, tickprefix="R$", side="right"),
                    yaxis2=dict(overlaying="y", side="left", showgrid=False,
                                showticklabels=False, range=[0, candles.get("Volume", pd.Series()).max()*5]
                                if "Volume" in candles.columns else [0,1]),
                    legend=dict(orientation="h", y=1.02, x=0,
                                bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                    margin=dict(l=0, r=0, t=10, b=0),
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("**Posição recomendada** — Kelly fracionado por nível de capital")

    CAPS = [50_000, 100_000, 250_000, 500_000, 1_000_000]
    CAP_LABELS = ["R$50k","R$100k","R$250k","R$500k","R$1M"]

    cap_input = st.number_input("Capital base (R$)", 10_000, 10_000_000,
                                100_000, 10_000, format="%d", key="cap_sz")

    df_sz = df_all[
        df_all["ProfitFactor"].fillna(0).replace([np.inf,-np.inf],0) >= 1.5
    ].sort_values("Score", ascending=False).head(8)

    for _, r in df_sz.iterrows():
        pf  = float(r.get("ProfitFactor") or 1.5)
        hr  = float(r.get("HitRate") or 50)
        ops = int(r.get("Operacoes") or 100)
        inst= bool(r.get("Instavel", True))

        hr_r = hr/100
        b    = max(pf*(1-hr_r)/hr_r, 0.01)
        k    = (hr_r*b-(1-hr_r))/b * 0.25
        if ops < 50: k = 0.02
        if inst: k *= 0.7
        k = float(np.clip(k, 0.01, 0.20))

        sinal_data = SINAIS_DEMO.get(r["Ativo"], ("NEUTRO",0.5,"LowVol"))
        rec = classificar_rec(sinal_data[0], pf, hr, inst)
        est_lbl = "✓ estável" if not inst else "⚠ instável"
        est_c   = "#22c55e" if not inst else "#f59e0b"

        with st.expander(f"{r['Ativo']} · {r['Horizonte']} · {r['Regime']}  —  Kelly {k*100:.1f}%  ·  {est_lbl}"):
            sa,sb,sc2,sd = st.columns(4)
            sa.metric("PF", f"{pf:.2f}")
            sb.metric("HR", f"{hr:.1f}%")
            sc2.metric("Ops/ano", f"~{ops//5}")
            sd.markdown(f"<br>{rec_badge(rec)}", unsafe_allow_html=True)

            cols_cap = st.columns(len(CAPS))
            for j, (cap, lbl) in enumerate(zip(CAPS, CAP_LABELS)):
                pos  = cap * k
                stop = pos * 0.04
                cols_cap[j].markdown(
                    f"<div style='text-align:center;padding:8px;"
                    f"border:1px solid #1e3a5f;border-radius:8px'>"
                    f"<div style='font-size:10px;color:#475569'>{lbl}</div>"
                    f"<div style='font-size:15px;font-weight:600;color:#e2e8f0'>R${pos:,.0f}</div>"
                    f"<div style='font-size:10px;color:#f87171'>stop R${stop:,.0f}</div></div>",
                    unsafe_allow_html=True
                )

# ── footer
st.markdown(f"""
<div style='text-align:center;font-size:11px;color:#334155;
    font-family:IBM Plex Mono,monospace;padding:16px 0 8px'>
MQM v6.4 · {fonte.upper()} · Não constitui recomendação de investimento
</div>""", unsafe_allow_html=True)
