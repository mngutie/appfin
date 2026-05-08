import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import locale
from supabase import create_client

# Dias da semana em português
DIAS_PT = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
MESES_PT = ["janeiro","fevereiro","março","abril","maio","junho",
            "julho","agosto","setembro","outubro","novembro","dezembro"]

def dia_semana_pt(dt):
    return DIAS_PT[dt.weekday()]

def data_pt(dt):
    """Retorna data formatada em dd/mm/yyyy"""
    if isinstance(dt, str):
        dt = datetime.strptime(dt[:10], "%Y-%m-%d")
    return dt.strftime("%d/%m/%Y")

# ── Página ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="💰 Finanças", page_icon="💰", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #08090e; color: #c9d1d9; }
section[data-testid="stSidebar"] { background: #0d0f17; border-right: 1px solid #1c1f2e; }

/* ── Cards executivos ── */
.exec-card {
    position: relative;
    background: #0d0f17;
    border: 1px solid #1c1f2e;
    border-radius: 4px;
    padding: 24px 28px 20px;
    margin-bottom: 8px;
    overflow: hidden;
}
.exec-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: var(--line, #1e3a5f);
}
.exec-card-icon {
    position: absolute;
    top: 20px; right: 22px;
    font-size: 18px;
    opacity: 0.18;
}
.exec-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a5568;
    margin-bottom: 10px;
}
.exec-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 24px;
    font-weight: 600;
    color: var(--val, #e2e8f0);
    letter-spacing: -0.5px;
    line-height: 1;
}
.exec-delta {
    margin-top: 10px;
    font-size: 11px;
    color: #4a5568;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}
.exec-divider {
    width: 28px; height: 2px;
    background: var(--line, #1e3a5f);
    margin: 10px 0 8px;
    border-radius: 2px;
}

/* Cartão saldo */
.card {
    background: #0d0f17;
    border: 1px solid #1c1f2e;
    border-radius: 4px;
    padding: 20px 22px;
    margin-bottom: 8px;
}
.metric-label { font-size: 10px; color: #4a5568; letter-spacing: 2px; text-transform: uppercase; font-weight: 600; }
.metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 24px; font-weight: 600; margin-top: 6px; letter-spacing: -0.5px; }
.green  { color: #38a169; }
.red    { color: #e53e3e; }
.blue   { color: #3182ce; }
.yellow { color: #d69e2e; }
.purple { color: #805ad5; }

/* Tags */
.tag { padding: 2px 10px; border-radius: 2px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; }
.tag-r { background: #0a1f13; color: #38a169; border: 1px solid #1a4731; }
.tag-d { background: #1a0a0a; color: #e53e3e; border: 1px solid #4a1515; }
.tag-c { background: #0a1325; color: #3182ce; border: 1px solid #1a3a6e; }
.tag-f { background: #130a25; color: #805ad5; border: 1px solid #3a1a6e; }

/* Botões */
.stButton > button {
    background: #1a2235;
    color: #90cdf4;
    border: 1px solid #2d3f5e;
    border-radius: 3px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
    padding: 9px 22px;
    transition: all 0.15s;
    text-transform: uppercase;
}
.stButton > button:hover {
    background: #243050;
    border-color: #3182ce;
    color: #bee3f8;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0d0f17;
    border-radius: 0;
    padding: 0;
    gap: 0;
    border-bottom: 1px solid #1c1f2e;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0;
    color: #4a5568;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 12px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #90cdf4 !important;
    border-bottom: 2px solid #3182ce !important;
}

/* Alertas */
.alert-warn   { background: #0f0a00; border-left: 3px solid #d69e2e; border-radius: 0; padding: 12px 16px; margin: 5px 0; color: #d69e2e; font-size: 13px; }
.alert-danger { background: #0f0000; border-left: 3px solid #e53e3e; border-radius: 0; padding: 12px 16px; margin: 5px 0; color: #e53e3e; font-size: 13px; }
.alert-ok     { background: #000f05; border-left: 3px solid #38a169; border-radius: 0; padding: 12px 16px; margin: 5px 0; color: #38a169; font-size: 13px; }

/* Tabelas */
table { width: 100%; border-collapse: collapse; }
th { background: #0d0f17; color: #4a5568; font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; font-weight: 600; padding: 10px 14px; text-align: left; border-bottom: 1px solid #1c1f2e; }
td { padding: 11px 14px; border-bottom: 1px solid #111520; font-size: 13px; font-family: 'Inter', sans-serif; }
tr:hover td { background: #0d0f17; }

/* Inputs */
input, select { background: #0d0f17 !important; border: 1px solid #1c1f2e !important; color: #c9d1d9 !important; border-radius: 3px !important; font-family: 'Inter', sans-serif !important; }
.stSelectbox > div > div { background: #0d0f17 !important; border-color: #1c1f2e !important; border-radius: 3px !important; }

/* Progress */
.prog-bg   { background: #1c1f2e; border-radius: 0; height: 3px; margin-top: 8px; }
.prog-fill { height: 3px; border-radius: 0; }

h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; color: #e2e8f0; letter-spacing: -0.3px; }
</style>
""", unsafe_allow_html=True)

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

sb = get_supabase()

# ── Carregar dados ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def cached_load():
    transacoes   = sb.table("transacoes").select("*").execute().data or []
    contas_fixas = sb.table("contas_fixas").select("*").execute().data or []
    cartoes      = sb.table("cartoes").select("*").execute().data or []
    faturas      = sb.table("faturas").select("*").execute().data or []
    metas_raw    = sb.table("metas").select("*").execute().data or []
    metas        = {m["mes"]: m["valor"] for m in metas_raw}
    baixas       = sb.table("baixas").select("*").execute().data or []
    return transacoes, contas_fixas, cartoes, faturas, metas, baixas

def reload():
    st.cache_data.clear()
    st.rerun()

transacoes, contas_fixas, cartoes, faturas, metas, baixas = cached_load()

# Helpers de baixas
def esta_pago(ref_id):
    return any(b["referencia_id"] == str(ref_id) for b in baixas)

def get_baixa(ref_id):
    return next((b for b in baixas if b["referencia_id"] == str(ref_id)), None)

FORMAS_PAG = ["PIX","Débito","Crédito","Dinheiro","Boleto","TED/DOC","Outros"]

# ── Helpers ───────────────────────────────────────────────────────────────────
CATS_D = [
    "📺 Assinaturas","🛒 Supermercado","🧴 Cuidados Pessoais","💳 Dívidas",
    "📋 Impostos e Taxas","🐾 Pets","✈️ Viagem","🌐 Internet","💧 Água",
    "💡 Luz","📱 Telefonia","🏠 Moradia","🚗 Transporte","⛽ Combustível",
    "🏷️ IPTU","🚘 IPVA","📄 Licenciamento","🎮 Jogos","🎁 Presentes",
    "💊 Saúde","🎓 Educação","🍔 Alimentação","👕 Vestuário","📦 Outros",
]
CATS_R = ["💼 Salário","💰 Freelance","📈 Investimentos","🎁 Presente","📦 Outros"]

def mes_label(dt): return dt.strftime("%m/%Y")
def mes_from_label(s):
    m, y = s.split("/"); return date(int(y), int(m), 1)

def gerar_meses(n=12):
    hoje = date.today()
    return [mes_label(hoje + relativedelta(months=i)) for i in range(-3, n)]

def transacoes_df():
    rows = []
    for t in transacoes:
        rows.append({**t, "origem": "manual"})
    for cf in contas_fixas:
        inicio = mes_from_label(cf["mes_inicio"])
        for i in range(cf["meses"]):
            mes = inicio + relativedelta(months=i)
            dia = min(cf["dia_venc"], calendar.monthrange(mes.year, mes.month)[1])
            dt  = date(mes.year, mes.month, dia)
            rows.append({
                "id": f"cf_{cf['id']}_{i}", "tipo": "Despesa",
                "descricao": cf["descricao"], "valor": cf["valor"],
                "categoria": cf["categoria"], "data": str(dt),
                "origem": "fixa", "cf_id": cf["id"]
            })
    # Agrupa faturas por cartão+mês → uma linha por fatura no calendário
    from collections import defaultdict
    faturas_agrupadas = defaultdict(lambda: {"valor": 0.0, "cartao": "", "cartao_id": None, "dia_venc": 1, "ids": []})
    for fat in faturas:
        parc = fat.get("parcelas", 1)
        for p in range(parc):
            mes_p  = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
            chave  = (fat.get("cartao", ""), mes_label(mes_p))
            val_p  = round(fat["valor"] / parc, 2)
            faturas_agrupadas[chave]["valor"]      += val_p
            faturas_agrupadas[chave]["cartao"]      = fat.get("cartao", "")
            faturas_agrupadas[chave]["cartao_id"]   = fat.get("cartao_id")
            faturas_agrupadas[chave]["dia_venc"]    = fat.get("dia_venc", 1)
            faturas_agrupadas[chave]["ids"].append(f"fat_{fat['id']}_{p}")

    for (nome_cartao, mes_fat), info in faturas_agrupadas.items():
        mes_obj_f = mes_from_label(mes_fat)
        dia       = min(info["dia_venc"], calendar.monthrange(mes_obj_f.year, mes_obj_f.month)[1])
        dt        = date(mes_obj_f.year, mes_obj_f.month, dia)
        ref_id    = f"fatura_{nome_cartao}_{mes_fat}".replace("/","_").replace(" ","_")
        rows.append({
            "id":        ref_id,
            "tipo":      "Despesa",
            "descricao": f"💳 Fatura {nome_cartao}",
            "valor":     round(info["valor"], 2),
            "categoria": "💳 Cartão",
            "data":      str(dt),
            "origem":    "cartao",
            "cartao":    nome_cartao,
            "cartao_id": info["cartao_id"],
            "sub_ids":   info["ids"],
        })
    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["id","tipo","descricao","valor","categoria","data","origem"])
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
        df["mes"]  = df["data"].dt.strftime("%m/%Y")
    return df

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='border-bottom:1px solid #1c1f2e;padding-bottom:16px;margin-bottom:20px'>
  <div style='font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#3182ce;font-weight:600;margin-bottom:6px'>GESTÃO FINANCEIRA PESSOAL</div>
  <div style='font-family:Inter,sans-serif;font-size:1.7rem;font-weight:700;color:#e2e8f0;letter-spacing:-0.5px'>Minhas Finanças</div>
  <div style='font-size:11px;color:#4a5568;margin-top:4px;font-weight:500;letter-spacing:0.5px'>{dia_semana_pt(datetime.now()).upper()} · {datetime.now().strftime('%d/%m/%Y')} · {datetime.now().strftime('%H:%M')}</div>
</div>
""", unsafe_allow_html=True)

df_all = transacoes_df()
hoje   = date.today()

# ── Alertas ───────────────────────────────────────────────────────────────────
alertas = []
# Contas fixas — só alerta se ainda não paga
for cf in contas_fixas:
    inicio = mes_from_label(cf["mes_inicio"])
    for i in range(cf["meses"]):
        mes_v = inicio + relativedelta(months=i)
        dia   = min(cf["dia_venc"], calendar.monthrange(mes_v.year, mes_v.month)[1])
        dt    = date(mes_v.year, mes_v.month, dia)
        diff  = (dt - hoje).days
        ref_id = f"cf_{cf['id']}_{i}"
        if esta_pago(ref_id):
            continue  # já pago, sem alerta
        if 0 <= diff <= 5:
            alertas.append(("warn", f"⚠️ {cf['descricao']} vence em {diff} dia(s) — R$ {cf['valor']:,.2f}"))
        elif -3 <= diff < 0:
            alertas.append(("danger", f"🔴 {cf['descricao']} venceu há {-diff} dia(s) — R$ {cf['valor']:,.2f}"))

# Lançamentos manuais — só alerta se não pago
for t in transacoes:
    if t.get("tipo") != "Despesa":
        continue
    ref_id = str(t["id"])
    if esta_pago(ref_id):
        continue
    try:
        dt   = datetime.strptime(t["data"][:10], "%Y-%m-%d").date()
        diff = (dt - hoje).days
        if 0 <= diff <= 5:
            alertas.append(("warn", f"⚠️ {t['descricao']} vence em {diff} dia(s) — R$ {t['valor']:,.2f}"))
        elif -3 <= diff < 0:
            alertas.append(("danger", f"🔴 {t['descricao']} venceu há {-diff} dia(s) — R$ {t['valor']:,.2f}"))
    except Exception:
        pass

# Faturas de cartão agrupadas por cartão+mês — só alerta se não paga
from collections import defaultdict as _dd
_faturas_alerta = _dd(lambda: {"cartao": "", "dia_venc": 1, "valor": 0.0})
for fat in faturas:
    cartao_obj = next((c for c in cartoes if c["id"] == fat.get("cartao_id")), None)
    if not cartao_obj:
        continue
    parc = fat.get("parcelas", 1)
    for p in range(parc):
        mes_p  = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
        chave  = f"fatura_{cartao_obj['nome']}_{mes_label(mes_p)}".replace("/","_").replace(" ","_")
        _faturas_alerta[chave]["cartao"]   = cartao_obj["nome"]
        _faturas_alerta[chave]["dia_venc"] = cartao_obj["dia_venc"]
        _faturas_alerta[chave]["valor"]   += round(fat["valor"] / parc, 2)
        _faturas_alerta[chave]["mes_p"]    = mes_p

for ref_id, info in _faturas_alerta.items():
    if esta_pago(ref_id):
        continue
    mes_p = info["mes_p"]
    dia   = min(info["dia_venc"], calendar.monthrange(mes_p.year, mes_p.month)[1])
    dt_fat = date(mes_p.year, mes_p.month, dia)
    diff   = (dt_fat - hoje).days
    if 0 <= diff <= 5:
        alertas.append(("warn", f"💳 Fatura {info['cartao']} vence em {diff} dia(s) — R$ {info['valor']:,.2f}"))
    elif -3 <= diff < 0:
        alertas.append(("danger", f"🔴 Fatura {info['cartao']} venceu há {-diff} dia(s) — R$ {info['valor']:,.2f}"))

if alertas:
    with st.expander(f"🔔 {len(alertas)} alerta(s) pendente(s) — clique para ver", expanded=True):
        for tipo_a, msg in alertas:
            css = "alert-warn" if tipo_a == "warn" else "alert-danger"
            st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ABAS
# ════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "🏠 Resumo","📝 Lançamentos","📌 Contas Fixas","💳 Cartões","📅 Calendário","📈 Projeção","📊 Relatórios"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 1 — RESUMO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    meses_disp = sorted(df_all["mes"].unique().tolist(), reverse=True) if not df_all.empty else [mes_label(date.today())]
    mes_sel = st.selectbox("📅 Mês", meses_disp, key="mes_resumo")

    df_m = df_all[df_all["mes"] == mes_sel] if not df_all.empty else pd.DataFrame()
    rec  = df_m[df_m["tipo"] == "Receita"]["valor"].sum() if not df_m.empty else 0
    desp = df_m[df_m["tipo"] == "Despesa"]["valor"].sum() if not df_m.empty else 0
    saldo= rec - desp
    meta = metas.get(mes_sel, 0)
    pct  = (desp / meta * 100) if meta > 0 else 0

    c1,c2,c3,c4 = st.columns(4)

    # Cores corporativas
    cor_saldo = "#38a169" if saldo >= 0 else "#e53e3e"
    lin_saldo = "#1a4731" if saldo >= 0 else "#4a1515"
    icon_saldo = "↑" if saldo >= 0 else "↓"
    cor_m = "#38a169" if pct <= 80 else "#d69e2e" if pct <= 100 else "#e53e3e"
    lin_m = "#1a4731" if pct <= 80 else "#4a2e00" if pct <= 100 else "#4a1515"
    margem = ((rec - desp) / rec * 100) if rec > 0 else 0

    c1.markdown(f"""
    <div class="exec-card" style="--line:{lin_saldo};--val:{cor_saldo}">
      <div class="exec-card-icon">{icon_saldo}</div>
      <div class="exec-label">Resultado do Mês</div>
      <div class="exec-divider"></div>
      <div class="exec-value" style="color:{cor_saldo}">R$ {saldo:,.2f}</div>
      <div class="exec-delta">Margem: <span style="color:{cor_saldo}">{margem:.1f}%</span></div>
    </div>""", unsafe_allow_html=True)

    c2.markdown(f"""
    <div class="exec-card" style="--line:#1a4731;--val:#38a169">
      <div class="exec-card-icon">+</div>
      <div class="exec-label">Total de Receitas</div>
      <div class="exec-divider" style="background:#1a4731"></div>
      <div class="exec-value" style="color:#38a169">R$ {rec:,.2f}</div>
      <div class="exec-delta">Período: <span style="color:#718096">{mes_sel}</span></div>
    </div>""", unsafe_allow_html=True)

    c3.markdown(f"""
    <div class="exec-card" style="--line:#4a1515;--val:#e53e3e">
      <div class="exec-card-icon">−</div>
      <div class="exec-label">Total de Despesas</div>
      <div class="exec-divider" style="background:#4a1515"></div>
      <div class="exec-value" style="color:#e53e3e">R$ {desp:,.2f}</div>
      <div class="exec-delta">Comprometimento: <span style="color:#718096">{(desp/rec*100 if rec>0 else 0):.1f}%</span></div>
    </div>""", unsafe_allow_html=True)

    c4.markdown(f"""
    <div class="exec-card" style="--line:{lin_m};--val:{cor_m}">
      <div class="exec-card-icon">◎</div>
      <div class="exec-label">Meta de Gastos</div>
      <div class="exec-divider" style="background:{lin_m}"></div>
      <div class="exec-value" style="color:{cor_m}">{pct:.1f}<span style="font-size:14px;font-weight:400">%</span></div>
      <div class="exec-delta">R$ {desp:,.2f} <span style="color:#4a5568">/ R$ {meta:,.2f}</span></div>
      <div class="prog-bg" style="margin-top:10px"><div class="prog-fill" style="width:{min(pct,100):.0f}%;background:{cor_m}"></div></div>
    </div>""", unsafe_allow_html=True)

    with st.expander("🎯 Definir meta mensal"):
        m_val = st.number_input("Limite de gastos (R$)", 0.0, step=50.0, format="%.2f", key="meta_val")
        if st.button("Salvar meta"):
            existe = sb.table("metas").select("id").eq("mes", mes_sel).execute().data
            if existe:
                sb.table("metas").update({"valor": m_val}).eq("mes", mes_sel).execute()
            else:
                sb.table("metas").insert({"mes": mes_sel, "valor": m_val}).execute()
            st.success("Meta salva!"); reload()

    st.markdown("<br>", unsafe_allow_html=True)
    if not df_m.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("### Despesas por Categoria")
            dc = df_m[df_m["tipo"] == "Despesa"].groupby("categoria")["valor"].sum().reset_index()
            if not dc.empty:
                fig = px.pie(dc, values="valor", names="categoria", hole=.45,
                             color_discrete_sequence=px.colors.sequential.Plasma_r)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e8e8f0",
                                  margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig, use_container_width=True)
        with g2:
            st.markdown("### Receitas vs Despesas")
            res = df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
            fig2 = px.bar(res, x="mes", y="valor", color="tipo", barmode="group",
                          color_discrete_map={"Receita":"#4ade80","Despesa":"#f87171"})
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#e8e8f0",
                               plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(gridcolor="#1e1e2e"),
                               yaxis=dict(gridcolor="#1e1e2e"), legend_title="",
                               margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig2, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 2 — LANÇAMENTOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown("### ➕ Novo Lançamento")
    c1,c2,c3 = st.columns(3)
    tipo_l = c1.selectbox("Tipo", ["Despesa","Receita"], key="tipo_l")
    desc_l = c2.text_input("Descrição", key="desc_l")
    val_l  = c3.number_input("Valor (R$)", 0.01, step=0.01, format="%.2f", key="val_l")
    c4,c5  = st.columns(2)
    cats   = CATS_D if tipo_l == "Despesa" else CATS_R
    cat_l  = c4.selectbox("Categoria", cats, key="cat_l")
    data_l = c5.date_input("Data", date.today(), key="data_l")
    if st.button("💾 Salvar Lançamento"):
        if desc_l:
            sb.table("transacoes").insert({
                "tipo": tipo_l, "descricao": desc_l,
                "valor": val_l, "categoria": cat_l, "data": str(data_l)
            }).execute()
            st.success("✅ Lançamento salvo!")
            # Limpar campos
            for k in ["desc_l","val_l","data_l"]:
                if k in st.session_state:
                    del st.session_state[k]
            reload()
        else:
            st.error("Preencha a descrição.")

    st.markdown("---")
    st.markdown("### 📋 Lançamentos")
    if transacoes:
        df_man = pd.DataFrame(transacoes).sort_values("data", ascending=False)
        df_man["Data"]  = pd.to_datetime(df_man["data"]).dt.strftime("%d/%m/%Y")
        df_man["Tipo"]  = df_man["tipo"].apply(lambda x:
            '<span class="tag tag-r">Receita</span>' if x == "Receita"
            else '<span class="tag tag-d">Despesa</span>')
        df_man["Valor"] = df_man["valor"].apply(lambda v: f"R$ {v:,.2f}")
        df_man = df_man.rename(columns={"descricao":"Descrição","categoria":"Categoria"})
        st.write(df_man[["Data","Tipo","Descrição","Categoria","Valor"]].to_html(
            escape=False, index=False, border=0), unsafe_allow_html=True)
        with st.expander("🗑️ Excluir lançamento"):
            descs = [f'{t["id"]} — {t["descricao"]} ({data_pt(t["data"])})' for t in transacoes]
            sel   = st.selectbox("Lançamento", descs, key="del_man") if descs else None
            if sel and st.button("Excluir", key="btn_del_man"):
                del_id = int(sel.split(" — ")[0])
                sb.table("transacoes").delete().eq("id", del_id).execute()
                st.success("Excluído!"); reload()
    else:
        st.info("Nenhum lançamento ainda.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 3 — CONTAS FIXAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown("### 📌 Cadastrar Conta Fixa / Recorrente")
    c1,c2,c3 = st.columns(3)
    desc_f    = c1.text_input("Descrição", key="desc_f")
    val_f     = c2.number_input("Valor (R$)", 0.01, step=0.01, format="%.2f", key="val_f")
    cat_f     = c3.selectbox("Categoria", CATS_D, key="cat_f")
    c4,c5,c6  = st.columns(3)
    dia_f     = c4.number_input("Dia de vencimento", 1, 31, step=1, key="dia_f")
    meses_opts= gerar_meses(24)
    mes_ini_f = c5.selectbox("Mês início", meses_opts,
                             index=meses_opts.index(mes_label(date.today())), key="mes_ini_f")
    rep_f     = c6.number_input("Repetir por quantos meses", 1, 120, step=1, key="rep_f")

    if st.button("💾 Salvar Conta Fixa"):
        if desc_f:
            sb.table("contas_fixas").insert({
                "descricao": desc_f, "valor": val_f, "categoria": cat_f,
                "dia_venc": int(dia_f), "mes_inicio": mes_ini_f, "meses": int(rep_f)
            }).execute()
            st.success("✅ Conta fixa salva!")
            for k in ["desc_f","val_f","dia_f","rep_f"]:
                if k in st.session_state:
                    del st.session_state[k]
            reload()
        else:
            st.error("Preencha a descrição.")

    st.markdown("---")
    st.markdown("### 📋 Contas Fixas Cadastradas")
    if contas_fixas:
        rows = []
        for cf in contas_fixas:
            fim = mes_label(mes_from_label(cf["mes_inicio"]) + relativedelta(months=cf["meses"]-1))
            rows.append({
                "ID": cf["id"], "Descrição": cf["descricao"],
                "Valor": f'R$ {cf["valor"]:,.2f}', "Categoria": cf["categoria"],
                "Venc.": f'Dia {cf["dia_venc"]}',
                "Período": f'{cf["mes_inicio"]} → {fim}', "Meses": cf["meses"]
            })
        st.write(pd.DataFrame(rows).to_html(index=False, border=0), unsafe_allow_html=True)
        with st.expander("🗑️ Excluir conta fixa"):
            descs_f = [f'{cf["id"]} — {cf["descricao"]}' for cf in contas_fixas]
            sel_f   = st.selectbox("Conta", descs_f, key="del_cf") if descs_f else None
            if sel_f and st.button("Excluir", key="btn_del_cf"):
                del_id = int(sel_f.split(" — ")[0])
                sb.table("contas_fixas").delete().eq("id", del_id).execute()
                st.success("Excluído!"); reload()
    else:
        st.info("Nenhuma conta fixa cadastrada.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 4 — CARTÕES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 💳 Cadastrar Cartão")
        nome_c = st.text_input("Nome do cartão (ex: Nubank)", key="nome_c")
        lim_c  = st.number_input("Limite (R$)", 0.0, step=50.0, format="%.2f", key="lim_c")
        fech_c = st.number_input("Dia de fechamento", 1, 28, step=1, key="fech_c")
        venc_c = st.number_input("Dia de vencimento", 1, 31, step=1, key="venc_c")
        if st.button("💾 Salvar Cartão"):
            if nome_c:
                sb.table("cartoes").insert({
                    "nome": nome_c, "limite": lim_c,
                    "dia_fech": int(fech_c), "dia_venc": int(venc_c)
                }).execute()
                st.success("Cartão salvo!"); reload()
            else:
                st.error("Informe o nome.")

    with col_b:
        st.markdown("### 💳 Cartões cadastrados")
        if cartoes:
            for c in cartoes:
                # Soma todos os lançamentos não pagos do cartão (todas as parcelas em aberto)
                total_utilizado = 0.0
                for fat in faturas:
                    if fat.get("cartao_id") != c["id"]:
                        continue
                    parc = fat.get("parcelas", 1)
                    for p in range(parc):
                        mes_p   = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
                        ref_fat = f"fatura_{c['nome']}_{mes_label(mes_p)}".replace("/","_").replace(" ","_")
                        if not esta_pago(ref_fat):
                            total_utilizado += round(fat["valor"] / parc, 2)

                disponivel = max(c["limite"] - total_utilizado, 0)
                uso        = (total_utilizado / c["limite"] * 100) if c["limite"] > 0 else 0
                cor_u      = "#38a169" if uso <= 70 else "#d69e2e" if uso <= 90 else "#e53e3e"

                st.markdown(f"""
                <div class="exec-card" style="--line:#1a3a6e;margin-bottom:10px">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <div style="font-size:15px;font-weight:700;color:#e2e8f0">{c['nome']}</div>
                      <div style="font-size:11px;color:#4a5568;margin-top:2px">
                        Fecha dia {c['dia_fech']} · Vence dia {c['dia_venc']}
                      </div>
                    </div>
                    <div style="text-align:right">
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Limite Total</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:600;color:#c9d1d9">R$ {c['limite']:,.2f}</div>
                    </div>
                  </div>
                  <div style="display:flex;gap:24px;margin-top:14px">
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Utilizado</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:600;color:#e53e3e">R$ {total_utilizado:,.2f}</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Disponível</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:600;color:#38a169">R$ {disponivel:,.2f}</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Uso</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:600;color:{cor_u}">{uso:.1f}%</div>
                    </div>
                  </div>
                  <div class="prog-bg" style="margin-top:10px">
                    <div class="prog-fill" style="width:{min(uso,100):.0f}%;background:{cor_u}"></div>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Nenhum cartão cadastrado.")

    st.markdown("---")
    st.markdown("### ➕ Lançar Gasto no Cartão")
    if cartoes:
        c1,c2,c3   = st.columns(3)
        cart_opts  = {c["nome"]: c["id"] for c in cartoes}
        cart_sel   = c1.selectbox("Cartão", list(cart_opts.keys()), key="cart_sel")
        desc_fat   = c2.text_input("Descrição", key="desc_fat")
        val_fat    = c3.number_input("Valor total (R$)", 0.01, step=0.01, format="%.2f", key="val_fat")
        c4,c5,c6   = st.columns(3)
        parc_fat   = c4.number_input("Parcelas", 1, 48, step=1, key="parc_fat")
        cat_fat    = c5.selectbox("Categoria", CATS_D, key="cat_fat")
        meses_opts2= gerar_meses(24)
        mes_fat_ini= c6.selectbox("Mês 1ª parcela", meses_opts2,
                                   index=meses_opts2.index(mes_label(date.today())), key="mes_fat_ini")
        cartao_obj = next(c for c in cartoes if c["nome"] == cart_sel)
        if st.button("💾 Salvar Gasto"):
            if desc_fat:
                sb.table("faturas").insert({
                    "cartao_id": cart_opts[cart_sel], "cartao": cart_sel,
                    "descricao": desc_fat, "valor": val_fat,
                    "parcelas": int(parc_fat), "categoria": cat_fat,
                    "mes_inicio": mes_fat_ini, "dia_venc": cartao_obj["dia_venc"]
                }).execute()
                st.success("✅ Gasto no cartão salvo!")
                for k in ["desc_fat","val_fat","parc_fat"]:
                    if k in st.session_state:
                        del st.session_state[k]
                reload()
            else:
                st.error("Preencha a descrição.")

        st.markdown("### 📋 Gastos no Cartão")
        if faturas:
            rows_f = []
            for f in faturas:
                fim_f = mes_label(mes_from_label(f["mes_inicio"]) + relativedelta(months=f["parcelas"]-1))
                rows_f.append({
                    "Cartão": f.get("cartao",""), "Descrição": f["descricao"],
                    "Valor Total": f'R$ {f["valor"]:,.2f}',
                    "Parc.": f'{f["parcelas"]}x R$ {f["valor"]/f["parcelas"]:,.2f}',
                    "Período": f'{f["mes_inicio"]} → {fim_f}'
                })
            st.write(pd.DataFrame(rows_f).to_html(index=False, border=0), unsafe_allow_html=True)
            with st.expander("🗑️ Excluir gasto"):
                descs_fat = [f'{f["id"]} — {f["descricao"]} ({f.get("cartao","")})' for f in faturas]
                sel_fat   = st.selectbox("Gasto", descs_fat, key="del_fat") if descs_fat else None
                if sel_fat and st.button("Excluir", key="btn_del_fat"):
                    del_id = int(sel_fat.split(" — ")[0])
                    sb.table("faturas").delete().eq("id", del_id).execute()
                    st.success("Excluído!"); reload()
    else:
        st.warning("Cadastre um cartão primeiro.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 5 — CALENDÁRIO + BAIXAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab5:
    subtab_cal, subtab_baixas, subtab_hist = st.tabs(["📅 Calendário","✅ Dar Baixa / Pendências","📋 Histórico de Pagamentos"])
    meses_cal = gerar_meses(6)

    # ── Sub-aba Calendário ─────────────────────────────────────────────────────
    with subtab_cal:
        mes_cal = st.selectbox("Mês", meses_cal, index=3, key="mes_cal")
        df_cal  = df_all[(df_all["mes"] == mes_cal) & (df_all["tipo"] == "Despesa")] if not df_all.empty else pd.DataFrame()
        if not df_cal.empty:
            df_cal_s = df_cal.sort_values("data").copy()
            mes_obj  = mes_from_label(mes_cal)
            semanas  = calendar.monthcalendar(mes_obj.year, mes_obj.month)
            dias_semana = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
            html = '<table style="width:100%;table-layout:fixed">'
            html += '<tr>' + ''.join(f'<th style="text-align:center">{d}</th>' for d in dias_semana) + '</tr>'
            for sem in semanas:
                html += '<tr>'
                for dia in sem:
                    if dia == 0:
                        html += '<td style="height:80px;vertical-align:top;background:#08090e"></td>'
                    else:
                        dt_dia     = date(mes_obj.year, mes_obj.month, dia)
                        contas_dia = df_cal_s[df_cal_s["data"].dt.date == dt_dia]
                        bg  = "#0d0f17" if dt_dia != hoje else "#0f1a2e"
                        brd = "2px solid #3182ce" if dt_dia == hoje else "1px solid #1c1f2e"
                        cell = f'<div style="font-size:12px;color:#4a5568;font-weight:600">{dia}</div>'
                        for _, row in contas_dia.iterrows():
                            pago = esta_pago(str(row["id"]))
                            if pago:
                                cor  = "#38a169"
                                icon = "✓ "
                                op   = "0.7"
                            else:
                                cor  = "#3182ce" if row.get("origem") == "cartao" else "#805ad5" if row.get("origem") == "fixa" else "#e53e3e"
                                icon = ""
                                op   = "1"
                            cell += (
                                f'<div style="background:{cor}22;color:{cor};font-size:10px;opacity:{op};'
                                f'border-radius:2px;padding:2px 5px;margin-top:2px;overflow:hidden;'
                                f'white-space:nowrap;text-overflow:ellipsis">'
                                f'{icon}{row["descricao"][:14]} R${row["valor"]:,.0f}</div>'
                            )
                        html += f'<td style="height:90px;vertical-align:top;padding:6px;background:{bg};border:{brd};border-radius:2px">{cell}</td>'
                html += '</tr>'
            html += '</table>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                "<span style='color:#805ad5'>■ Fixa</span> &nbsp;"
                "<span style='color:#3182ce'>■ Cartão</span> &nbsp;"
                "<span style='color:#e53e3e'>■ Manual</span> &nbsp;"
                "<span style='color:#38a169'>■ Pago</span>",
                unsafe_allow_html=True)
        else:
            st.info("Nenhuma despesa neste mês.")

    # ── Sub-aba Dar Baixa ──────────────────────────────────────────────────────
    with subtab_baixas:
        mes_baixa = st.selectbox("Mês", meses_cal, index=3, key="mes_baixa")
        df_baixa  = df_all[(df_all["mes"] == mes_baixa) & (df_all["tipo"] == "Despesa")] if not df_all.empty else pd.DataFrame()

        if not df_baixa.empty:
            df_baixa = df_baixa.sort_values("data").copy()

            total_contas = len(df_baixa)
            pagas        = sum(1 for _, r in df_baixa.iterrows() if esta_pago(str(r["id"])))
            pendentes    = total_contas - pagas
            val_pago     = sum(r["valor"] for _, r in df_baixa.iterrows() if esta_pago(str(r["id"])))
            val_pendente = sum(r["valor"] for _, r in df_baixa.iterrows() if not esta_pago(str(r["id"])))
            pct_pago     = (pagas / total_contas * 100) if total_contas > 0 else 0
            cor_pct      = "#38a169" if pct_pago == 100 else "#d69e2e" if pct_pago >= 50 else "#e53e3e"

            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(
                f'<div class="exec-card" style="--line:#1a4731;--val:#38a169">'
                f'<div class="exec-label">Pagas</div>'
                f'<div class="exec-divider" style="background:#1a4731"></div>'
                f'<div class="exec-value" style="color:#38a169">{pagas}/{total_contas}</div>'
                f'<div class="exec-delta">R$ {val_pago:,.2f}</div></div>',
                unsafe_allow_html=True)
            k2.markdown(
                f'<div class="exec-card" style="--line:#4a1515;--val:#e53e3e">'
                f'<div class="exec-label">Pendentes</div>'
                f'<div class="exec-divider" style="background:#4a1515"></div>'
                f'<div class="exec-value" style="color:#e53e3e">{pendentes}</div>'
                f'<div class="exec-delta">R$ {val_pendente:,.2f}</div></div>',
                unsafe_allow_html=True)
            k3.markdown(
                f'<div class="exec-card" style="--line:#1a3a6e;--val:{cor_pct}">'
                f'<div class="exec-label">Progresso</div>'
                f'<div class="exec-divider" style="background:#1a3a6e"></div>'
                f'<div class="exec-value" style="color:{cor_pct}">{pct_pago:.0f}%</div>'
                f'<div class="prog-bg"><div class="prog-fill" style="width:{pct_pago:.0f}%;background:{cor_pct}"></div></div>'
                f'</div>',
                unsafe_allow_html=True)
            k4.markdown(
                f'<div class="exec-card" style="--line:#3a1a6e;--val:#c9d1d9">'
                f'<div class="exec-label">Total do Mês</div>'
                f'<div class="exec-divider" style="background:#3a1a6e"></div>'
                f'<div class="exec-value">R$ {val_pago + val_pendente:,.2f}</div>'
                f'<div class="exec-delta">Pago + Pendente</div></div>',
                unsafe_allow_html=True)

            st.markdown("---")
            mostrar = st.radio("Mostrar", ["Só pendentes","Todas"], horizontal=True, key="filtro_baixa")

            for _, row in df_baixa.iterrows():
                ref_id     = str(row["id"])
                pago       = esta_pago(ref_id)
                baixa_info = get_baixa(ref_id)
                if mostrar == "Só pendentes" and pago:
                    continue
                venc_dt  = row["data"].date() if hasattr(row["data"], "date") else row["data"]
                atrasado = not pago and venc_dt < hoje
                brd_cor  = "#38a169" if pago else ("#e53e3e" if atrasado else "#1c1f2e")
                status_badge = ""
                if atrasado:
                    status_badge = '<span style="font-size:10px;background:#1a0000;color:#e53e3e;padding:2px 8px;border-radius:2px;margin-left:8px;font-weight:700;letter-spacing:1px">ATRASADO</span>'
                pago_info = ""
                if pago and baixa_info:
                    pago_info = (
                        f'<div style="margin-top:8px;font-size:11px;color:#38a169">'
                        f'✓ Pago em {data_pt(baixa_info["data_pagamento"])} via {baixa_info.get("forma_pagamento","—")}'
                        f'{(" · " + baixa_info["observacao"]) if baixa_info.get("observacao") else ""}'
                        f'</div>'
                    )
                venc_fmt = row["data"].strftime("%d/%m/%Y") if hasattr(row["data"], "strftime") else str(row["data"])
                st.markdown(
                    f'<div style="border:1px solid {brd_cor};border-left:3px solid {brd_cor};'
                    f'border-radius:2px;padding:14px 18px;margin:6px 0;background:#0d0f17">'
                    f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
                    f'<div><span style="font-weight:600;color:#e2e8f0">{row["descricao"]}</span>'
                    f'<span style="font-size:11px;color:#4a5568;margin-left:10px">{row.get("categoria","")}</span>'
                    f'{status_badge}</div>'
                    f'<div style="text-align:right">'
                    f'<div style="font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:600;color:#e2e8f0">R$ {row["valor"]:,.2f}</div>'
                    f'<div style="font-size:11px;color:#4a5568">Venc: {venc_fmt}</div>'
                    f'</div></div>'
                    f'{pago_info}</div>',
                    unsafe_allow_html=True)

                if not pago:
                    with st.expander(f"✅ Dar baixa — {row['descricao'][:40]}"):
                        bc1, bc2, bc3 = st.columns(3)
                        dp  = bc1.date_input("Data do pagamento", date.today(), key=f"dp_{ref_id}")
                        fp  = bc2.selectbox("Forma de pagamento", FORMAS_PAG, key=f"fp_{ref_id}")
                        obs = bc3.text_input("Observação", key=f"obs_{ref_id}", placeholder="Opcional")
                        if st.button("✅ Confirmar pagamento", key=f"btn_baixa_{ref_id}"):
                            sb.table("baixas").insert({
                                "referencia_id":   ref_id,
                                "tipo_origem":     row.get("origem", "manual"),
                                "data_vencimento": str(venc_dt),
                                "data_pagamento":  str(dp),
                                "valor":           float(row["valor"]),
                                "forma_pagamento": fp,
                                "observacao":      obs
                            }).execute()
                            st.success("✅ Baixa registrada com sucesso!"); reload()
                else:
                    if st.button("↩ Estornar pagamento", key=f"est_{ref_id}"):
                        sb.table("baixas").delete().eq("id", baixa_info["id"]).execute()
                        st.success("Estorno realizado!"); reload()
        else:
            st.info("Nenhuma despesa neste mês.")

    # ── Sub-aba Histórico de Pagamentos ────────────────────────────────────────
    with subtab_hist:
        st.markdown("### 📋 Histórico de Pagamentos")
        if baixas:
            df_hist_b = pd.DataFrame(baixas).sort_values("data_pagamento", ascending=False)
            df_hist_b["Data Pgto"] = pd.to_datetime(df_hist_b["data_pagamento"]).dt.strftime("%d/%m/%Y")
            df_hist_b["Data Venc"] = pd.to_datetime(df_hist_b["data_vencimento"]).dt.strftime("%d/%m/%Y")

            # Enriquecer com descrição
            def get_nome_baixa(ref_id, tipo):
                t = next((x for x in transacoes if str(x["id"]) == str(ref_id)), None)
                return t["descricao"] if t else f"Ref. {ref_id}"
            df_hist_b["Conta"] = df_hist_b.apply(lambda r: get_nome_baixa(r["referencia_id"], r["tipo_origem"]), axis=1)

            # KPI
            total_registrado = df_hist_b["valor"].sum()
            st.markdown(
                f'<div class="exec-card" style="--line:#1a4731;--val:#38a169;margin-bottom:16px">'
                f'<div class="exec-label">Total Pago (todos os períodos)</div>'
                f'<div class="exec-divider" style="background:#1a4731"></div>'
                f'<div class="exec-value" style="color:#38a169">R$ {total_registrado:,.2f}</div>'
                f'<div class="exec-delta">{len(df_hist_b)} pagamentos registrados</div></div>',
                unsafe_allow_html=True)

            # Filtro
            formas_disp = ["Todas"] + sorted(df_hist_b["forma_pagamento"].dropna().unique().tolist())
            filtro_fp   = st.selectbox("Filtrar por forma de pagamento", formas_disp, key="filtro_hist_fp")
            if filtro_fp != "Todas":
                df_hist_b = df_hist_b[df_hist_b["forma_pagamento"] == filtro_fp]

            html = "<table><tr><th>Data Pgto</th><th>Vencimento</th><th>Conta</th><th>Forma</th><th>Valor</th><th>Observação</th></tr>"
            for _, r in df_hist_b.iterrows():
                html += (
                    f"<tr>"
                    f"<td><b>{r['Data Pgto']}</b></td>"
                    f"<td style='color:#4a5568'>{r['Data Venc']}</td>"
                    f"<td>{r['Conta']}</td>"
                    f"<td><span class='tag tag-c'>{r.get('forma_pagamento','—')}</span></td>"
                    f"<td style='font-family:IBM Plex Mono,monospace;color:#38a169;font-weight:600'>R$ {r['valor']:,.2f}</td>"
                    f"<td style='color:#4a5568'>{r.get('observacao','') or '—'}</td>"
                    f"</tr>"
                )
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Nenhum pagamento registrado ainda.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 6 — PROJEÇÃO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab6:
    st.markdown("### 📈 Projeção de Saldo — Próximos 12 Meses")
    meses_proj = [mes_label(date.today() + relativedelta(months=i)) for i in range(13)]

    rows_proj  = []
    saldo_acum = 0
    for mes_p in meses_proj:
        df_p   = df_all[df_all["mes"] == mes_p] if not df_all.empty else pd.DataFrame()
        rec_p  = df_p[df_p["tipo"] == "Receita"]["valor"].sum() if not df_p.empty else 0
        desp_p = df_p[df_p["tipo"] == "Despesa"]["valor"].sum() if not df_p.empty else 0
        saldo_mes  = rec_p - desp_p
        saldo_acum += saldo_mes
        rows_proj.append({"Mês":mes_p,"Receitas":rec_p,"Despesas":desp_p,
                          "Resultado":saldo_mes,"Saldo Acumulado":saldo_acum})

    df_proj = pd.DataFrame(rows_proj)

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=df_proj["Mês"], y=df_proj["Saldo Acumulado"],
        mode="lines+markers", name="Saldo Acumulado",
        line=dict(color="#6366f1", width=3), fill="tozeroy",
        fillcolor="rgba(99,102,241,0.12)", marker=dict(size=7)))
    fig_proj.add_trace(go.Bar(x=df_proj["Mês"], y=df_proj["Receitas"],
        name="Receitas", marker_color="rgba(74,222,128,0.33)"))
    fig_proj.add_trace(go.Bar(x=df_proj["Mês"], y=[-v for v in df_proj["Despesas"]],
        name="Despesas", marker_color="rgba(248,113,113,0.33)"))
    fig_proj.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8e8f0", xaxis=dict(gridcolor="#1e1e2e"),
        yaxis=dict(gridcolor="#1e1e2e"), barmode="relative",
        legend=dict(orientation="h", y=1.1), margin=dict(t=20,b=10,l=10,r=10))
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("### Tabela de Projeção")
    df_show = df_proj.copy()
    def fmt(v):
        cor = "#4ade80" if v >= 0 else "#f87171"
        return f'<span style="color:{cor}">R$ {v:,.2f}</span>'
    df_show["Receitas"]        = df_show["Receitas"].apply(lambda v: f"R$ {v:,.2f}")
    df_show["Despesas"]        = df_show["Despesas"].apply(lambda v: f"R$ {v:,.2f}")
    df_show["Resultado"]       = df_show["Resultado"].apply(fmt)
    df_show["Saldo Acumulado"] = df_show["Saldo Acumulado"].apply(fmt)
    st.write(df_show.to_html(escape=False, index=False, border=0), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Análise")
    meses_neg = [r["Mês"] for r in rows_proj if r["Resultado"] < 0]
    if meses_neg:
        st.markdown(f'<div class="alert-warn">⚠️ Meses com resultado negativo: {", ".join(meses_neg)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-ok">✅ Todos os meses projetados com resultado positivo!</div>', unsafe_allow_html=True)

    melhor = df_proj.loc[df_proj["Resultado"].idxmax()]["Mês"]
    pior   = df_proj.loc[df_proj["Resultado"].idxmin()]["Mês"]
    st.markdown(f'<div class="card" style="margin-top:12px">🏆 <b>Melhor mês projetado:</b> {melhor} &nbsp;&nbsp; 📉 <b>Pior mês:</b> {pior}</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 7 — RELATÓRIOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab7:

    PLOT_THEME = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        font_family="Inter",
        xaxis=dict(gridcolor="#1c1f2e", showgrid=True),
        yaxis=dict(gridcolor="#1c1f2e", showgrid=True),
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(orientation="h", y=1.12, font=dict(size=11)),
    )

    def fmt_val(v):
        cor = "#38a169" if v >= 0 else "#e53e3e"
        return f'<span style="font-family:IBM Plex Mono,monospace;color:{cor};font-weight:600">R$ {v:,.2f}</span>'

    def fmt_mon(v):
        return f'<span style="font-family:IBM Plex Mono,monospace">R$ {v:,.2f}</span>'

    def section(title):
        st.markdown(f'<div style="border-left:3px solid #3182ce;padding-left:12px;margin:24px 0 14px;font-size:16px;font-weight:700;color:#e2e8f0;letter-spacing:-0.3px">{title}</div>', unsafe_allow_html=True)

    # ── Seletor de relatório ────────────────────────────────────────────────────
    rel_opts = [
        "📅 DRE Mensal — Demonstrativo de Resultado",
        "📆 Comparativo Mensal (Ano a Ano)",
        "🏷️ Gastos por Categoria — Detalhado",
        "📈 Evolução do Saldo",
        "✅ Inadimplência — Contas em Aberto",
        "💳 Relatório de Cartões",
        "📌 Contas Fixas — Projeção de Compromissos",
        "💰 Fluxo de Caixa — Entradas e Saídas",
        "🏆 Ranking de Gastos",
        "📊 Resumo Anual Consolidado",
    ]
    rel_sel = st.selectbox("Selecionar relatório", rel_opts, key="rel7_sel")

    # Período padrão para relatórios
    hoje_r = date.today()
    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════════
    # 1. DRE MENSAL
    # ════════════════════════════════════════════════════════════════════════════
    if rel_sel == rel_opts[0]:
        section("DRE — Demonstrativo de Resultado do Exercício")
        meses_dre  = sorted(df_all["mes"].unique().tolist(), reverse=True) if not df_all.empty else [mes_label(date.today())]
        mes_dre    = st.selectbox("Mês de referência", meses_dre, key="dre_mes")
        df_dre     = df_all[df_all["mes"] == mes_dre] if not df_all.empty else pd.DataFrame()

        rec_total  = df_dre[df_dre["tipo"] == "Receita"]["valor"].sum() if not df_dre.empty else 0
        desp_total = df_dre[df_dre["tipo"] == "Despesa"]["valor"].sum() if not df_dre.empty else 0
        resultado  = rec_total - desp_total
        margem     = (resultado / rec_total * 100) if rec_total > 0 else 0

        # Bloco DRE estilo corporativo
        st.markdown(f"""
        <div style="background:#0d0f17;border:1px solid #1c1f2e;border-radius:4px;padding:28px 32px;margin:12px 0">
          <div style="font-size:10px;letter-spacing:3px;text-transform:uppercase;color:#3182ce;font-weight:600;margin-bottom:4px">DEMONSTRATIVO DE RESULTADO</div>
          <div style="font-size:18px;font-weight:700;color:#e2e8f0;margin-bottom:24px">Período: {mes_dre}</div>

          <div style="border-bottom:1px solid #1c1f2e;padding-bottom:14px;margin-bottom:14px">
            <div style="font-size:10px;letter-spacing:2px;color:#4a5568;text-transform:uppercase;margin-bottom:10px">RECEITAS</div>
            <div style="display:flex;justify-content:space-between;padding:6px 0">
              <span style="color:#c9d1d9">Total de Receitas</span>
              <span style="font-family:IBM Plex Mono,monospace;color:#38a169;font-weight:600;font-size:16px">R$ {rec_total:,.2f}</span>
            </div>
          </div>

          <div style="border-bottom:1px solid #1c1f2e;padding-bottom:14px;margin-bottom:14px">
            <div style="font-size:10px;letter-spacing:2px;color:#4a5568;text-transform:uppercase;margin-bottom:10px">DESPESAS</div>
            <div style="display:flex;justify-content:space-between;padding:6px 0">
              <span style="color:#c9d1d9">Total de Despesas</span>
              <span style="font-family:IBM Plex Mono,monospace;color:#e53e3e;font-weight:600;font-size:16px">(R$ {desp_total:,.2f})</span>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;padding:12px 0;border-top:2px solid #3182ce">
            <span style="font-weight:700;font-size:15px;color:#e2e8f0">RESULTADO LÍQUIDO</span>
            <span style="font-family:IBM Plex Mono,monospace;font-weight:700;font-size:20px;color:{'#38a169' if resultado>=0 else '#e53e3e'}">R$ {resultado:,.2f}</span>
          </div>

          <div style="display:flex;gap:32px;margin-top:16px;padding-top:14px;border-top:1px solid #1c1f2e">
            <div><div style="font-size:10px;color:#4a5568;letter-spacing:1px;text-transform:uppercase">Margem</div>
                 <div style="font-family:IBM Plex Mono,monospace;font-size:18px;font-weight:600;color:{'#38a169' if margem>=0 else '#e53e3e'}">{margem:.1f}%</div></div>
            <div><div style="font-size:10px;color:#4a5568;letter-spacing:1px;text-transform:uppercase">Comprometimento</div>
                 <div style="font-family:IBM Plex Mono,monospace;font-size:18px;font-weight:600;color:#c9d1d9">{(desp_total/rec_total*100 if rec_total>0 else 0):.1f}%</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if not df_dre.empty:
            c1, c2 = st.columns(2)
            with c1:
                section("Receitas por Categoria")
                rc = df_dre[df_dre["tipo"]=="Receita"].groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                if not rc.empty:
                    html = "<table><tr><th>Categoria</th><th style='text-align:right'>Valor</th><th style='text-align:right'>%</th></tr>"
                    for _, r in rc.iterrows():
                        pct_r = r["valor"]/rec_total*100 if rec_total > 0 else 0
                        html += f"<tr><td>{r['categoria']}</td><td style='text-align:right'>{fmt_mon(r['valor'])}</td><td style='text-align:right;color:#4a5568'>{pct_r:.1f}%</td></tr>"
                    html += f"<tr style='border-top:1px solid #3182ce'><td><b>Total</b></td><td style='text-align:right'>{fmt_mon(rec_total)}</td><td style='text-align:right'>100%</td></tr>"
                    html += "</table>"
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("Sem receitas neste mês.")

            with c2:
                section("Despesas por Categoria")
                dc = df_dre[df_dre["tipo"]=="Despesa"].groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
                if not dc.empty:
                    html = "<table><tr><th>Categoria</th><th style='text-align:right'>Valor</th><th style='text-align:right'>%</th></tr>"
                    for _, r in dc.iterrows():
                        pct_d = r["valor"]/desp_total*100 if desp_total > 0 else 0
                        html += f"<tr><td>{r['categoria']}</td><td style='text-align:right'>{fmt_mon(r['valor'])}</td><td style='text-align:right;color:#4a5568'>{pct_d:.1f}%</td></tr>"
                    html += f"<tr style='border-top:1px solid #e53e3e'><td><b>Total</b></td><td style='text-align:right'>{fmt_mon(desp_total)}</td><td style='text-align:right'>100%</td></tr>"
                    html += "</table>"
                    st.markdown(html, unsafe_allow_html=True)

            section("Todas as Transações do Mês")
            df_lista = df_dre.sort_values("data").copy()
            df_lista["Data"] = df_lista["data"].dt.strftime("%d/%m/%Y")
            html = "<table><tr><th>Data</th><th>Tipo</th><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Valor</th></tr>"
            for _, r in df_lista.iterrows():
                cor = "#38a169" if r["tipo"]=="Receita" else "#e53e3e"
                sinal = "+" if r["tipo"]=="Receita" else "−"
                html += (f"<tr><td>{r['Data']}</td>"
                         f"<td><span class='tag {'tag-r' if r['tipo']=='Receita' else 'tag-d'}'>{r['tipo']}</span></td>"
                         f"<td>{r['descricao']}</td><td>{r['categoria']}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor};font-weight:600'>{sinal} R$ {r['valor']:,.2f}</td></tr>")
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            # Exportar CSV
            csv_dre = df_lista[["Data","tipo","descricao","categoria","valor"]].rename(
                columns={"tipo":"Tipo","descricao":"Descrição","categoria":"Categoria","valor":"Valor"}).to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar CSV", csv_dre, f"DRE_{mes_dre.replace('/','_')}.csv", "text/csv")

    # ════════════════════════════════════════════════════════════════════════════
    # 2. COMPARATIVO MENSAL
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[1]:
        section("Comparativo Mensal — Evolução ao Longo do Tempo")
        if not df_all.empty:
            resumo = df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
            pivot  = resumo.pivot(index="mes", columns="tipo", values="valor").fillna(0).reset_index()
            pivot.columns.name = None
            if "Receita" not in pivot.columns: pivot["Receita"] = 0
            if "Despesa" not in pivot.columns: pivot["Despesa"] = 0
            pivot["Resultado"] = pivot["Receita"] - pivot["Despesa"]
            pivot["Margem %"]  = pivot.apply(lambda r: (r["Resultado"]/r["Receita"]*100) if r["Receita"]>0 else 0, axis=1)

            fig = go.Figure()
            fig.add_trace(go.Bar(x=pivot["mes"], y=pivot["Receita"], name="Receitas", marker_color="#38a169", opacity=0.8))
            fig.add_trace(go.Bar(x=pivot["mes"], y=pivot["Despesa"], name="Despesas", marker_color="#e53e3e", opacity=0.8))
            fig.add_trace(go.Scatter(x=pivot["mes"], y=pivot["Resultado"], name="Resultado",
                mode="lines+markers", line=dict(color="#3182ce", width=2), marker=dict(size=7), yaxis="y"))
            fig.update_layout(**PLOT_THEME, barmode="group")
            st.plotly_chart(fig, use_container_width=True)

            section("Tabela Comparativa")
            html = "<table><tr><th>Mês</th><th style='text-align:right'>Receitas</th><th style='text-align:right'>Despesas</th><th style='text-align:right'>Resultado</th><th style='text-align:right'>Margem</th></tr>"
            for _, r in pivot.sort_values("mes", ascending=False).iterrows():
                cor_res = "#38a169" if r["Resultado"] >= 0 else "#e53e3e"
                html += (f"<tr><td><b>{r['mes']}</b></td>"
                         f"<td style='text-align:right;color:#38a169;font-family:IBM Plex Mono,monospace'>R$ {r['Receita']:,.2f}</td>"
                         f"<td style='text-align:right;color:#e53e3e;font-family:IBM Plex Mono,monospace'>R$ {r['Despesa']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_res};font-weight:600'>R$ {r['Resultado']:,.2f}</td>"
                         f"<td style='text-align:right;color:#4a5568'>{r['Margem %']:.1f}%</td></tr>")
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            csv_comp = pivot.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar CSV", csv_comp, "comparativo_mensal.csv", "text/csv")
        else:
            st.info("Sem dados para exibir.")

    # ════════════════════════════════════════════════════════════════════════════
    # 3. GASTOS POR CATEGORIA DETALHADO
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[2]:
        section("Gastos por Categoria — Análise Detalhada")
        p1, p2 = st.columns(2)
        meses_cat  = gerar_meses(12)
        mes_ini_c  = p1.selectbox("De", meses_cat, index=0, key="cat_ini")
        mes_fim_c  = p2.selectbox("Até", meses_cat, index=len(meses_cat)-1, key="cat_fim")

        if not df_all.empty:
            df_c = df_all[df_all["tipo"]=="Despesa"].copy()
            meses_range = []
            cur = mes_from_label(mes_ini_c)
            fim = mes_from_label(mes_fim_c)
            while cur <= fim:
                meses_range.append(mes_label(cur))
                cur += relativedelta(months=1)
            df_c = df_c[df_c["mes"].isin(meses_range)]

            if not df_c.empty:
                total_periodo = df_c["valor"].sum()
                cat_group     = df_c.groupby("categoria")["valor"].agg(["sum","count","mean"]).reset_index()
                cat_group.columns = ["categoria","total","qtd","media"]
                cat_group = cat_group.sort_values("total", ascending=False)
                cat_group["pct"] = cat_group["total"] / total_periodo * 100

                c1, c2 = st.columns(2)
                with c1:
                    fig_pie = px.pie(cat_group, values="total", names="categoria", hole=0.5,
                                     color_discrete_sequence=["#3182ce","#38a169","#805ad5","#d69e2e","#e53e3e","#06b6d4","#f97316","#ec4899","#84cc16","#a78bfa"])
                    fig_pie.update_layout(**PLOT_THEME)
                    st.plotly_chart(fig_pie, use_container_width=True)
                with c2:
                    fig_bar = px.bar(cat_group.head(10), x="total", y="categoria", orientation="h",
                                     color="total", color_continuous_scale="Blues")
                    fig_bar.update_layout(**PLOT_THEME, showlegend=False)
                    st.plotly_chart(fig_bar, use_container_width=True)

                section("Detalhamento por Categoria")
                html = "<table><tr><th>Categoria</th><th style='text-align:right'>Total</th><th style='text-align:right'>Lançamentos</th><th style='text-align:right'>Média/Lanç.</th><th style='text-align:right'>% do Total</th></tr>"
                for _, r in cat_group.iterrows():
                    pct_bar = f'<div style="display:inline-block;width:{r["pct"]*1.5:.0f}px;height:6px;background:#3182ce;border-radius:2px;vertical-align:middle;margin-right:6px"></div>'
                    html += (f"<tr><td>{r['categoria']}</td>"
                             f"<td style='text-align:right'>{fmt_mon(r['total'])}</td>"
                             f"<td style='text-align:right;color:#4a5568'>{int(r['qtd'])}</td>"
                             f"<td style='text-align:right'>{fmt_mon(r['media'])}</td>"
                             f"<td style='text-align:right'>{pct_bar}{r['pct']:.1f}%</td></tr>")
                html += f"<tr style='border-top:2px solid #3182ce'><td><b>TOTAL</b></td><td style='text-align:right'><b>{fmt_mon(total_periodo)}</b></td><td style='text-align:right;color:#4a5568'>{int(cat_group['qtd'].sum())}</td><td></td><td style='text-align:right'>100%</td></tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

                section("Evolução por Categoria ao Longo dos Meses")
                cat_mes = df_c.groupby(["mes","categoria"])["valor"].sum().reset_index()
                fig_ev  = px.line(cat_mes, x="mes", y="valor", color="categoria", markers=True)
                fig_ev.update_layout(**PLOT_THEME)
                st.plotly_chart(fig_ev, use_container_width=True)

                csv_cat = cat_group.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Exportar CSV", csv_cat, "gastos_categoria.csv", "text/csv")
            else:
                st.info("Sem despesas no período selecionado.")
        else:
            st.info("Sem dados.")

    # ════════════════════════════════════════════════════════════════════════════
    # 4. EVOLUÇÃO DO SALDO
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[3]:
        section("Evolução do Saldo — Linha do Tempo")
        if not df_all.empty:
            df_ev = df_all.sort_values("data").copy()
            df_ev["fluxo"] = df_ev.apply(lambda r: r["valor"] if r["tipo"]=="Receita" else -r["valor"], axis=1)
            df_ev["saldo_acum"] = df_ev["fluxo"].cumsum()
            df_ev["Data"] = df_ev["data"].dt.strftime("%d/%m/%Y")

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_ev["data"], y=df_ev["saldo_acum"],
                mode="lines", name="Saldo Acumulado",
                line=dict(color="#3182ce", width=2.5),
                fill="tozeroy", fillcolor="rgba(49,130,206,0.08)"))
            fig.add_hline(y=0, line_dash="dash", line_color="#4a5568", line_width=1)
            fig.update_layout(**PLOT_THEME)
            st.plotly_chart(fig, use_container_width=True)

            # Saldo por mês
            section("Saldo Mensal Acumulado")
            saldo_mes_rows = []
            acum = 0
            for mes_s in sorted(df_all["mes"].unique()):
                df_ms  = df_all[df_all["mes"]==mes_s]
                rec_ms = df_ms[df_ms["tipo"]=="Receita"]["valor"].sum()
                des_ms = df_ms[df_ms["tipo"]=="Despesa"]["valor"].sum()
                res_ms = rec_ms - des_ms
                acum  += res_ms
                saldo_mes_rows.append({"Mês":mes_s,"Receitas":rec_ms,"Despesas":des_ms,"Resultado":res_ms,"Saldo Acum.":acum})

            html = "<table><tr><th>Mês</th><th style='text-align:right'>Receitas</th><th style='text-align:right'>Despesas</th><th style='text-align:right'>Resultado</th><th style='text-align:right'>Saldo Acum.</th></tr>"
            for r in reversed(saldo_mes_rows):
                cor_r = "#38a169" if r["Resultado"]>=0 else "#e53e3e"
                cor_a = "#38a169" if r["Saldo Acum."]>=0 else "#e53e3e"
                html += (f"<tr><td><b>{r['Mês']}</b></td>"
                         f"<td style='text-align:right;color:#38a169;font-family:IBM Plex Mono,monospace'>R$ {r['Receitas']:,.2f}</td>"
                         f"<td style='text-align:right;color:#e53e3e;font-family:IBM Plex Mono,monospace'>R$ {r['Despesas']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_r};font-weight:600'>R$ {r['Resultado']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_a};font-weight:700'>R$ {r['Saldo Acum.']:,.2f}</td></tr>")
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Sem dados para exibir.")

    # ════════════════════════════════════════════════════════════════════════════
    # 5. INADIMPLÊNCIA — CONTAS EM ABERTO
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[4]:
        section("Inadimplência — Contas em Aberto e Atrasadas")
        if not df_all.empty:
            df_inad = df_all[df_all["tipo"]=="Despesa"].copy()
            df_inad["pago"]     = df_inad["id"].apply(lambda i: esta_pago(str(i)))
            df_inad["venc_dt"]  = df_inad["data"].dt.date
            df_inad["atrasado"] = df_inad.apply(lambda r: not r["pago"] and r["venc_dt"] < hoje_r, axis=1)
            df_inad["dias_atr"] = df_inad.apply(lambda r: (hoje_r - r["venc_dt"]).days if r["atrasado"] else 0, axis=1)
            df_inad["Data"]     = df_inad["data"].dt.strftime("%d/%m/%Y")

            em_aberto  = df_inad[~df_inad["pago"]]
            atrasadas  = df_inad[df_inad["atrasado"]]
            a_vencer   = df_inad[(~df_inad["pago"]) & (~df_inad["atrasado"])]

            k1,k2,k3,k4 = st.columns(4)
            k1.markdown(f'<div class="exec-card" style="--line:#4a1515;--val:#e53e3e"><div class="exec-label">Em Aberto</div><div class="exec-divider" style="background:#4a1515"></div><div class="exec-value" style="color:#e53e3e">{len(em_aberto)}</div><div class="exec-delta">R$ {em_aberto["valor"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="exec-card" style="--line:#4a2e00;--val:#d69e2e"><div class="exec-label">Atrasadas</div><div class="exec-divider" style="background:#4a2e00"></div><div class="exec-value" style="color:#d69e2e">{len(atrasadas)}</div><div class="exec-delta">R$ {atrasadas["valor"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="exec-card" style="--line:#1a3a6e;--val:#3182ce"><div class="exec-label">A Vencer</div><div class="exec-divider" style="background:#1a3a6e"></div><div class="exec-value" style="color:#3182ce">{len(a_vencer)}</div><div class="exec-delta">R$ {a_vencer["valor"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            k4.markdown(f'<div class="exec-card" style="--line:#1a4731;--val:#38a169"><div class="exec-label">Pagas</div><div class="exec-divider" style="background:#1a4731"></div><div class="exec-value" style="color:#38a169">{df_inad["pago"].sum()}</div><div class="exec-delta">R$ {df_inad[df_inad["pago"]]["valor"].sum():,.2f}</div></div>', unsafe_allow_html=True)

            if not atrasadas.empty:
                section("🔴 Contas Atrasadas")
                html = "<table><tr><th>Vencimento</th><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Dias Atraso</th><th style='text-align:right'>Valor</th></tr>"
                for _, r in atrasadas.sort_values("dias_atr", ascending=False).iterrows():
                    html += (f"<tr><td style='color:#e53e3e'><b>{r['Data']}</b></td>"
                             f"<td>{r['descricao']}</td><td>{r['categoria']}</td>"
                             f"<td style='text-align:right;color:#e53e3e;font-weight:700'>{int(r['dias_atr'])} dias</td>"
                             f"<td style='text-align:right'>{fmt_mon(r['valor'])}</td></tr>")
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

            if not a_vencer.empty:
                section("🟡 A Vencer")
                html = "<table><tr><th>Vencimento</th><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Valor</th></tr>"
                for _, r in a_vencer.sort_values("data").iterrows():
                    html += (f"<tr><td>{r['Data']}</td>"
                             f"<td>{r['descricao']}</td><td>{r['categoria']}</td>"
                             f"<td style='text-align:right'>{fmt_mon(r['valor'])}</td></tr>")
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("Sem dados de despesas.")

    # ════════════════════════════════════════════════════════════════════════════
    # 6. RELATÓRIO DE CARTÕES
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[5]:
        section("Relatório de Cartões de Crédito")
        if cartoes:
            # ── Seletor de mês e visão ────────────────────────────────────────
            rc1, rc2 = st.columns([2, 1])
            meses_cartao = gerar_meses(24)
            mes_cartao   = rc1.selectbox("Mês de referência", meses_cartao,
                                          index=meses_cartao.index(mes_label(date.today())),
                                          key="rel_cartao_mes")
            visao_cartao = rc2.radio("Visão", ["Mês selecionado", "Todas as faturas"],
                                      horizontal=True, key="rel_cartao_visao")

            st.markdown("---")

            # ── KPIs globais do mês ───────────────────────────────────────────
            total_geral_mes   = 0.0
            total_geral_pago  = 0.0
            total_geral_aberto= 0.0
            for cartao in cartoes:
                for fat in faturas:
                    if fat.get("cartao_id") != cartao["id"]:
                        continue
                    parc = fat.get("parcelas", 1)
                    for p in range(parc):
                        mes_p = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
                        if mes_label(mes_p) != mes_cartao:
                            continue
                        val_p  = round(fat["valor"] / parc, 2)
                        ref_id = f"fatura_{cartao['nome']}_{mes_cartao}".replace("/","_").replace(" ","_")
                        total_geral_mes += val_p
                        if esta_pago(ref_id):
                            total_geral_pago += val_p
                        else:
                            total_geral_aberto += val_p

            gk1,gk2,gk3,gk4 = st.columns(4)
            gk1.markdown(f'<div class="exec-card" style="--line:#1a3a6e;--val:#3182ce"><div class="exec-label">Total Faturas — {mes_cartao}</div><div class="exec-divider" style="background:#1a3a6e"></div><div class="exec-value" style="color:#3182ce">R$ {total_geral_mes:,.2f}</div><div class="exec-delta">{len(cartoes)} cartão(ões)</div></div>', unsafe_allow_html=True)
            gk2.markdown(f'<div class="exec-card" style="--line:#1a4731;--val:#38a169"><div class="exec-label">Pago</div><div class="exec-divider" style="background:#1a4731"></div><div class="exec-value" style="color:#38a169">R$ {total_geral_pago:,.2f}</div></div>', unsafe_allow_html=True)
            gk3.markdown(f'<div class="exec-card" style="--line:#4a1515;--val:#e53e3e"><div class="exec-label">Em Aberto</div><div class="exec-divider" style="background:#4a1515"></div><div class="exec-value" style="color:#e53e3e">R$ {total_geral_aberto:,.2f}</div></div>', unsafe_allow_html=True)
            limite_total = sum(c["limite"] for c in cartoes)
            uso_total    = (total_geral_aberto / limite_total * 100) if limite_total > 0 else 0
            cor_uso_t    = "#38a169" if uso_total<=70 else "#d69e2e" if uso_total<=90 else "#e53e3e"
            gk4.markdown(f'<div class="exec-card" style="--line:#3a1a6e;--val:{cor_uso_t}"><div class="exec-label">Uso Total Limite</div><div class="exec-divider" style="background:#3a1a6e"></div><div class="exec-value" style="color:{cor_uso_t}">{uso_total:.1f}%</div><div class="exec-delta">Limite total: R$ {limite_total:,.2f}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Detalhe por cartão ────────────────────────────────────────────
            for cartao in cartoes:
                # Calcular fatura do mês selecionado
                fatura_mes   = 0.0
                lancamentos_mes = []
                fatura_total = 0.0
                lancamentos_todos = []

                for fat in faturas:
                    if fat.get("cartao_id") != cartao["id"]:
                        continue
                    parc  = fat.get("parcelas", 1)
                    fim_f = mes_label(mes_from_label(fat["mes_inicio"]) + relativedelta(months=parc-1))
                    for p in range(parc):
                        mes_p = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
                        val_p = round(fat["valor"] / parc, 2)
                        desc_p = fat["descricao"] if parc == 1 else f"{fat['descricao']} ({p+1}/{parc})"
                        row_l  = {
                            "desc": desc_p, "cat": fat.get("categoria",""),
                            "val": val_p, "mes": mes_label(mes_p),
                            "total": fat["valor"], "parc": parc, "periodo": f"{fat['mes_inicio']} → {fim_f}"
                        }
                        fatura_total += val_p
                        lancamentos_todos.append(row_l)
                        if mes_label(mes_p) == mes_cartao:
                            fatura_mes += val_p
                            lancamentos_mes.append(row_l)

                ref_id_mes  = f"fatura_{cartao['nome']}_{mes_cartao}".replace("/","_").replace(" ","_")
                pago_mes    = esta_pago(ref_id_mes)
                status_cor  = "#38a169" if pago_mes else "#e53e3e"
                status_txt  = "PAGO" if pago_mes else "EM ABERTO"
                brd_cor     = "#1a4731" if pago_mes else "#1a3a6e"

                # Limite considerando apenas faturas em aberto
                utilizado_limite = 0.0
                for fat2 in faturas:
                    if fat2.get("cartao_id") != cartao["id"]: continue
                    parc2 = fat2.get("parcelas", 1)
                    for p2 in range(parc2):
                        mes_p2  = mes_from_label(fat2["mes_inicio"]) + relativedelta(months=p2)
                        ref2    = f"fatura_{cartao['nome']}_{mes_label(mes_p2)}".replace("/","_").replace(" ","_")
                        if not esta_pago(ref2):
                            utilizado_limite += round(fat2["valor"] / parc2, 2)
                disponivel  = max(cartao["limite"] - utilizado_limite, 0)
                uso_lim     = (utilizado_limite / cartao["limite"] * 100) if cartao["limite"] > 0 else 0
                cor_lim     = "#38a169" if uso_lim<=70 else "#d69e2e" if uso_lim<=90 else "#e53e3e"

                st.markdown(f"""
                <div style="background:#0d0f17;border:1px solid #1c1f2e;border-left:3px solid #3182ce;
                     border-radius:2px;padding:22px 26px;margin:12px 0">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px">
                    <div>
                      <div style="font-size:16px;font-weight:700;color:#e2e8f0">{cartao['nome']}</div>
                      <div style="font-size:11px;color:#4a5568;margin-top:3px">
                        Fecha dia {cartao['dia_fech']} · Vence dia {cartao['dia_venc']} · Limite: R$ {cartao['limite']:,.2f}
                      </div>
                    </div>
                    <div style="text-align:right">
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Fatura {mes_cartao}</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:22px;font-weight:700;color:#e2e8f0">R$ {fatura_mes:,.2f}</div>
                      <div style="font-size:11px;font-weight:700;color:{status_cor};margin-top:2px">{status_txt}</div>
                    </div>
                  </div>
                  <div style="display:flex;gap:28px;border-top:1px solid #1c1f2e;padding-top:14px">
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Limite utilizado</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:600;color:#e53e3e">R$ {utilizado_limite:,.2f}</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Disponível</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:600;color:#38a169">R$ {disponivel:,.2f}</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Uso do limite</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:600;color:{cor_lim}">{uso_lim:.1f}%</div>
                    </div>
                    <div>
                      <div style="font-size:10px;color:#4a5568;text-transform:uppercase;letter-spacing:1px">Total no mês</div>
                      <div style="font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:600;color:#c9d1d9">{len(lancamentos_mes)} lanç.</div>
                    </div>
                  </div>
                  <div class="prog-bg" style="margin-top:10px">
                    <div class="prog-fill" style="width:{min(uso_lim,100):.0f}%;background:{cor_lim}"></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Lançamentos detalhados
                lances_exibir = lancamentos_mes if visao_cartao == "Mês selecionado" else lancamentos_todos
                if lances_exibir:
                    label_exp = f"📋 Lançamentos — {mes_cartao}" if visao_cartao == "Mês selecionado" else "📋 Todos os lançamentos"
                    with st.expander(f"{label_exp} — {cartao['nome']}"):
                        html = "<table><tr><th>Mês</th><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Valor Parcela</th><th style='text-align:right'>Valor Total</th><th>Parcelamento</th></tr>"
                        total_exib = 0.0
                        for l in sorted(lances_exibir, key=lambda x: x["mes"]):
                            total_exib += l["val"]
                            parc_info = f'{l["parc"]}x R$ {l["total"]/l["parc"]:,.2f}' if l["parc"] > 1 else "À vista"
                            html += (f"<tr>"
                                     f"<td style='color:#4a5568'><b>{l['mes']}</b></td>"
                                     f"<td>{l['desc']}</td>"
                                     f"<td>{l['cat']}</td>"
                                     f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#e53e3e;font-weight:600'>R$ {l['val']:,.2f}</td>"
                                     f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#4a5568'>R$ {l['total']:,.2f}</td>"
                                     f"<td style='color:#4a5568'>{parc_info}</td>"
                                     f"</tr>")
                        html += f"<tr style='border-top:2px solid #3182ce'><td colspan='3'><b>TOTAL</b></td><td style='text-align:right;font-family:IBM Plex Mono,monospace;font-weight:700;color:#e53e3e'>R$ {total_exib:,.2f}</td><td colspan='2'></td></tr>"
                        html += "</table>"
                        st.markdown(html, unsafe_allow_html=True)

            # ── Evolução mensal de todos os cartões ───────────────────────────
            section("Evolução das Faturas por Mês")
            meses_ev = sorted(set(
                mes_label(mes_from_label(f["mes_inicio"]) + relativedelta(months=p))
                for f in faturas
                for p in range(f.get("parcelas",1))
            ))
            if meses_ev:
                rows_ev = []
                for m_ev in meses_ev:
                    for cartao in cartoes:
                        val_m = sum(
                            round(f["valor"]/f.get("parcelas",1), 2)
                            for f in faturas
                            if f.get("cartao_id") == cartao["id"]
                            for p in range(f.get("parcelas",1))
                            if mes_label(mes_from_label(f["mes_inicio"]) + relativedelta(months=p)) == m_ev
                        )
                        if val_m > 0:
                            rows_ev.append({"Mês": m_ev, "Cartão": cartao["nome"], "Valor": val_m})
                if rows_ev:
                    df_ev_c = pd.DataFrame(rows_ev)
                    fig_ev_c = px.bar(df_ev_c, x="Mês", y="Valor", color="Cartão", barmode="group",
                                      color_discrete_sequence=["#3182ce","#38a169","#805ad5","#d69e2e","#e53e3e"])
                    fig_ev_c.update_layout(**PLOT_THEME)
                    st.plotly_chart(fig_ev_c, use_container_width=True)
        else:
            st.info("Nenhum cartão cadastrado.")

    # ════════════════════════════════════════════════════════════════════════════
    # 7. CONTAS FIXAS — PROJEÇÃO
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[6]:
        section("Contas Fixas — Projeção de Compromissos")
        if contas_fixas:
            total_anual = 0
            html = "<table><tr><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Valor/Mês</th><th style='text-align:right'>Meses</th><th style='text-align:right'>Total Comprometido</th><th>Vence dia</th><th>Período</th></tr>"
            for cf in sorted(contas_fixas, key=lambda x: x["valor"], reverse=True):
                total_cf = cf["valor"] * cf["meses"]
                total_anual += total_cf
                fim_cf = mes_label(mes_from_label(cf["mes_inicio"]) + relativedelta(months=cf["meses"]-1))
                html += (f"<tr><td><b>{cf['descricao']}</b></td><td>{cf['categoria']}</td>"
                         f"<td style='text-align:right'>{fmt_mon(cf['valor'])}</td>"
                         f"<td style='text-align:right;color:#4a5568'>{cf['meses']}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;font-weight:600'>{fmt_mon(total_cf)}</td>"
                         f"<td style='color:#4a5568'>Dia {cf['dia_venc']}</td>"
                         f"<td style='color:#4a5568'>{cf['mes_inicio']} → {fim_cf}</td></tr>")
            html += f"<tr style='border-top:2px solid #3182ce'><td colspan='4'><b>TOTAL COMPROMETIDO</b></td><td style='text-align:right;font-family:IBM Plex Mono,monospace;font-weight:700;color:#e53e3e'>{fmt_mon(total_anual)}</td><td colspan='2'></td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            # Projeção mês a mês
            section("Projeção Mês a Mês — Próximos 12 Meses")
            meses_12 = [mes_label(date.today() + relativedelta(months=i)) for i in range(12)]
            rows_proj_cf = []
            for mes_p in meses_12:
                dt_mes = mes_from_label(mes_p)
                total_mes_cf = 0
                items_mes = []
                for cf in contas_fixas:
                    inicio = mes_from_label(cf["mes_inicio"])
                    for i in range(cf["meses"]):
                        mes_cf = inicio + relativedelta(months=i)
                        if mes_label(mes_cf) == mes_p:
                            total_mes_cf += cf["valor"]
                            items_mes.append(cf["descricao"])
                rows_proj_cf.append({"Mês":mes_p,"Total":total_mes_cf,"Itens":len(items_mes)})

            html2 = "<table><tr><th>Mês</th><th style='text-align:right'>Qtd. Contas</th><th style='text-align:right'>Total Fixo</th></tr>"
            for r in rows_proj_cf:
                html2 += (f"<tr><td><b>{r['Mês']}</b></td>"
                          f"<td style='text-align:right;color:#4a5568'>{r['Itens']}</td>"
                          f"<td style='text-align:right'>{fmt_mon(r['Total'])}</td></tr>")
            html2 += "</table>"
            st.markdown(html2, unsafe_allow_html=True)
        else:
            st.info("Nenhuma conta fixa cadastrada.")

    # ════════════════════════════════════════════════════════════════════════════
    # 8. FLUXO DE CAIXA
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[7]:
        section("Fluxo de Caixa — Entradas e Saídas")
        p1, p2 = st.columns(2)
        meses_fluxo = gerar_meses(12)
        mes_ini_f2  = p1.selectbox("De", meses_fluxo, index=0, key="fluxo_ini")
        mes_fim_f2  = p2.selectbox("Até", meses_fluxo, index=len(meses_fluxo)-1, key="fluxo_fim")

        if not df_all.empty:
            cur = mes_from_label(mes_ini_f2)
            fim = mes_from_label(mes_fim_f2)
            meses_r = []
            while cur <= fim:
                meses_r.append(mes_label(cur)); cur += relativedelta(months=1)

            rows_fluxo = []
            saldo_ant  = 0
            for mes_f in meses_r:
                df_f   = df_all[df_all["mes"]==mes_f]
                rec_f  = df_f[df_f["tipo"]=="Receita"]["valor"].sum()
                des_f  = df_f[df_f["tipo"]=="Despesa"]["valor"].sum()
                res_f  = rec_f - des_f
                saldo_f = saldo_ant + res_f
                rows_fluxo.append({"Mês":mes_f,"Saldo Anterior":saldo_ant,"Entradas":rec_f,"Saídas":des_f,"Resultado":res_f,"Saldo Final":saldo_f})
                saldo_ant = saldo_f

            df_fluxo = pd.DataFrame(rows_fluxo)

            fig_fl = go.Figure()
            fig_fl.add_trace(go.Bar(x=df_fluxo["Mês"], y=df_fluxo["Entradas"], name="Entradas", marker_color="#38a169"))
            fig_fl.add_trace(go.Bar(x=df_fluxo["Mês"], y=-df_fluxo["Saídas"], name="Saídas", marker_color="#e53e3e"))
            fig_fl.add_trace(go.Scatter(x=df_fluxo["Mês"], y=df_fluxo["Saldo Final"], name="Saldo Final",
                mode="lines+markers", line=dict(color="#3182ce", width=2), marker=dict(size=8)))
            fig_fl.update_layout(**PLOT_THEME, barmode="relative")
            st.plotly_chart(fig_fl, use_container_width=True)

            html = "<table><tr><th>Mês</th><th style='text-align:right'>Saldo Anterior</th><th style='text-align:right'>Entradas</th><th style='text-align:right'>Saídas</th><th style='text-align:right'>Resultado</th><th style='text-align:right'>Saldo Final</th></tr>"
            for _, r in df_fluxo.iterrows():
                cor_r = "#38a169" if r["Resultado"]>=0 else "#e53e3e"
                cor_sf = "#38a169" if r["Saldo Final"]>=0 else "#e53e3e"
                html += (f"<tr><td><b>{r['Mês']}</b></td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#4a5568'>R$ {r['Saldo Anterior']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#38a169'>+ R$ {r['Entradas']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#e53e3e'>− R$ {r['Saídas']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_r};font-weight:600'>R$ {r['Resultado']:,.2f}</td>"
                         f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_sf};font-weight:700'>R$ {r['Saldo Final']:,.2f}</td></tr>")
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

            csv_fl = df_fluxo.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar Fluxo de Caixa CSV", csv_fl, "fluxo_caixa.csv", "text/csv")
        else:
            st.info("Sem dados para exibir.")

    # ════════════════════════════════════════════════════════════════════════════
    # 9. RANKING DE GASTOS
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[8]:
        section("Ranking de Gastos — Top Despesas")
        meses_rank = sorted(df_all["mes"].unique().tolist(), reverse=True) if not df_all.empty else []
        opcao_rank = st.radio("Período", ["Mês específico","Todos os meses"], horizontal=True, key="rank_op")

        if not df_all.empty:
            if opcao_rank == "Mês específico":
                mes_rank = st.selectbox("Mês", meses_rank, key="mes_rank")
                df_rank  = df_all[(df_all["mes"]==mes_rank) & (df_all["tipo"]=="Despesa")]
            else:
                df_rank  = df_all[df_all["tipo"]=="Despesa"]

            if not df_rank.empty:
                top_n = st.slider("Exibir top", 5, 30, 10, key="rank_n")
                df_rank_s = df_rank.sort_values("valor", ascending=False).head(top_n).copy()
                df_rank_s["Data"] = df_rank_s["data"].dt.strftime("%d/%m/%Y")
                df_rank_s["Rank"] = range(1, len(df_rank_s)+1)
                total_rank = df_rank["valor"].sum()

                fig_rank = px.bar(df_rank_s, x="valor", y="descricao", orientation="h",
                                  color="categoria",
                                  color_discrete_sequence=["#3182ce","#38a169","#805ad5","#d69e2e","#e53e3e","#06b6d4"])
                fig_rank.update_layout(**PLOT_THEME)
                st.plotly_chart(fig_rank, use_container_width=True)

                html = "<table><tr><th>#</th><th>Data</th><th>Descrição</th><th>Categoria</th><th style='text-align:right'>Valor</th><th style='text-align:right'>% Total</th></tr>"
                for _, r in df_rank_s.iterrows():
                    pct_r = r["valor"]/total_rank*100 if total_rank>0 else 0
                    medal = "🥇" if r["Rank"]==1 else "🥈" if r["Rank"]==2 else "🥉" if r["Rank"]==3 else str(int(r["Rank"]))
                    html += (f"<tr><td style='font-weight:700;color:#3182ce'>{medal}</td>"
                             f"<td style='color:#4a5568'>{r['Data']}</td>"
                             f"<td>{r['descricao']}</td><td>{r['categoria']}</td>"
                             f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:#e53e3e;font-weight:600'>R$ {r['valor']:,.2f}</td>"
                             f"<td style='text-align:right;color:#4a5568'>{pct_r:.1f}%</td></tr>")
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("Sem despesas no período.")
        else:
            st.info("Sem dados.")

    # ════════════════════════════════════════════════════════════════════════════
    # 10. RESUMO ANUAL CONSOLIDADO
    # ════════════════════════════════════════════════════════════════════════════
    elif rel_sel == rel_opts[9]:
        section("Resumo Anual Consolidado")
        anos_disp = sorted(set(pd.to_datetime(df_all["data"]).dt.year.unique()) if not df_all.empty else [date.today().year], reverse=True)
        ano_sel   = st.selectbox("Ano", anos_disp, key="ano_anual")

        if not df_all.empty:
            df_ano = df_all[df_all["data"].dt.year == ano_sel].copy()
            df_ano["mes_num"] = df_ano["data"].dt.month

            rec_ano  = df_ano[df_ano["tipo"]=="Receita"]["valor"].sum()
            des_ano  = df_ano[df_ano["tipo"]=="Despesa"]["valor"].sum()
            res_ano  = rec_ano - des_ano
            margem_a = (res_ano/rec_ano*100) if rec_ano>0 else 0

            # KPIs anuais
            k1,k2,k3,k4 = st.columns(4)
            k1.markdown(f'<div class="exec-card" style="--line:#1a4731;--val:#38a169"><div class="exec-label">Receitas {ano_sel}</div><div class="exec-divider" style="background:#1a4731"></div><div class="exec-value" style="color:#38a169">R$ {rec_ano:,.2f}</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="exec-card" style="--line:#4a1515;--val:#e53e3e"><div class="exec-label">Despesas {ano_sel}</div><div class="exec-divider" style="background:#4a1515"></div><div class="exec-value" style="color:#e53e3e">R$ {des_ano:,.2f}</div></div>', unsafe_allow_html=True)
            cor_res = "#38a169" if res_ano>=0 else "#e53e3e"
            k3.markdown(f'<div class="exec-card" style="--line:#1a3a6e;--val:{cor_res}"><div class="exec-label">Resultado {ano_sel}</div><div class="exec-divider" style="background:#1a3a6e"></div><div class="exec-value" style="color:{cor_res}">R$ {res_ano:,.2f}</div></div>', unsafe_allow_html=True)
            k4.markdown(f'<div class="exec-card" style="--line:#3a1a6e;--val:#c9d1d9"><div class="exec-label">Margem Anual</div><div class="exec-divider" style="background:#3a1a6e"></div><div class="exec-value">{margem_a:.1f}%</div></div>', unsafe_allow_html=True)

            # Gráfico mensal do ano
            MESES_NOME = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
            rows_ano = []
            for m in range(1,13):
                df_m_a = df_ano[df_ano["mes_num"]==m]
                rows_ano.append({
                    "Mês": MESES_NOME[m-1],
                    "Receitas": df_m_a[df_m_a["tipo"]=="Receita"]["valor"].sum(),
                    "Despesas": df_m_a[df_m_a["tipo"]=="Despesa"]["valor"].sum(),
                })
            df_ano_plot = pd.DataFrame(rows_ano)
            df_ano_plot["Resultado"] = df_ano_plot["Receitas"] - df_ano_plot["Despesas"]

            fig_ano = go.Figure()
            fig_ano.add_trace(go.Bar(x=df_ano_plot["Mês"], y=df_ano_plot["Receitas"], name="Receitas", marker_color="#38a169", opacity=0.85))
            fig_ano.add_trace(go.Bar(x=df_ano_plot["Mês"], y=df_ano_plot["Despesas"], name="Despesas", marker_color="#e53e3e", opacity=0.85))
            fig_ano.add_trace(go.Scatter(x=df_ano_plot["Mês"], y=df_ano_plot["Resultado"], name="Resultado",
                mode="lines+markers", line=dict(color="#3182ce", width=2.5), marker=dict(size=8)))
            fig_ano.update_layout(**PLOT_THEME, barmode="group")
            st.plotly_chart(fig_ano, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                section("Top Categorias de Despesa")
                top_cat = df_ano[df_ano["tipo"]=="Despesa"].groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False).head(8)
                fig_tc  = px.pie(top_cat, values="valor", names="categoria", hole=0.5,
                                 color_discrete_sequence=["#e53e3e","#d69e2e","#805ad5","#3182ce","#38a169","#06b6d4","#f97316","#ec4899"])
                fig_tc.update_layout(**PLOT_THEME)
                st.plotly_chart(fig_tc, use_container_width=True)

            with c2:
                section("Tabela Mensal")
                html = "<table><tr><th>Mês</th><th style='text-align:right'>Receitas</th><th style='text-align:right'>Despesas</th><th style='text-align:right'>Resultado</th></tr>"
                for _, r in df_ano_plot.iterrows():
                    cor_r = "#38a169" if r["Resultado"]>=0 else "#e53e3e"
                    html += (f"<tr><td><b>{r['Mês']}/{ano_sel}</b></td>"
                             f"<td style='text-align:right;color:#38a169;font-family:IBM Plex Mono,monospace'>R$ {r['Receitas']:,.2f}</td>"
                             f"<td style='text-align:right;color:#e53e3e;font-family:IBM Plex Mono,monospace'>R$ {r['Despesas']:,.2f}</td>"
                             f"<td style='text-align:right;font-family:IBM Plex Mono,monospace;color:{cor_r};font-weight:600'>R$ {r['Resultado']:,.2f}</td></tr>")
                html += f"<tr style='border-top:2px solid #3182ce'><td><b>TOTAL</b></td><td style='text-align:right;color:#38a169;font-family:IBM Plex Mono,monospace;font-weight:700'>R$ {rec_ano:,.2f}</td><td style='text-align:right;color:#e53e3e;font-family:IBM Plex Mono,monospace;font-weight:700'>R$ {des_ano:,.2f}</td><td style='text-align:right;font-family:IBM Plex Mono,monospace;font-weight:700;color:{cor_res}'>R$ {res_ano:,.2f}</td></tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

            csv_ano = df_ano_plot.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar Resumo Anual CSV", csv_ano, f"resumo_{ano_sel}.csv", "text/csv")
        else:
            st.info("Sem dados para o ano selecionado.")


st.markdown("<br><p style='text-align:center;color:#2a2a45;font-size:11px'>Minhas Finanças · Supabase</p>", unsafe_allow_html=True)
