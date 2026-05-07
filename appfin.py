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
    "📺 Assinaturas","🛒 Supermercado","🧴 Cuidados Pessoais","💳 Fatura",
    "📋 Impostos e Taxas","🐾 Pets","✈️ Viagem","🌐 Internet","💧 Água",
    "💡 Luz","📱 Telefonia","🏠 Moradia","🚗 Transporte","🚗 Seguro","⛽ Combustível",
    "🏷️ IPTU","🚘 IPVA","📄 Licenciamento","🎮 Jogos","🎁 Presentes",
    "💊 Saúde","🎓 Educação","🍔 Alimentação","👕 Vestuário","📦 Outros",
]
CATS_R = ["💼 Salário","💰 Freelance","💼 Vale","📈 Investimentos","💼 13º","🎁 Presente","📦 Outros","💼 Férias"]

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
    for fat in faturas:
        parc = fat.get("parcelas", 1)
        for p in range(parc):
            mes_p = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
            dia   = min(fat["dia_venc"], calendar.monthrange(mes_p.year, mes_p.month)[1])
            dt    = date(mes_p.year, mes_p.month, dia)
            desc  = fat["descricao"] if parc == 1 else f"{fat['descricao']} ({p+1}/{parc})"
            rows.append({
                "id": f"fat_{fat['id']}_{p}", "tipo": "Despesa",
                "descricao": desc,
                "valor": round(fat["valor"] / parc, 2),
                "categoria": fat.get("categoria", "💳 Cartão"),
                "data": str(dt), "origem": "cartao",
                "cartao": fat.get("cartao", "")
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
for cf in contas_fixas:
    inicio = mes_from_label(cf["mes_inicio"])
    for i in range(cf["meses"]):
        mes_v = inicio + relativedelta(months=i)
        dia   = min(cf["dia_venc"], calendar.monthrange(mes_v.year, mes_v.month)[1])
        dt    = date(mes_v.year, mes_v.month, dia)
        diff  = (dt - hoje).days
        if 0 <= diff <= 5:
            alertas.append(("warn", f"⚠️ {cf['descricao']} vence em {diff} dia(s) — R$ {cf['valor']:,.2f}"))
        elif -3 <= diff < 0:
            alertas.append(("danger", f"🔴 {cf['descricao']} venceu há {-diff} dia(s) — R$ {cf['valor']:,.2f}"))

for fat in faturas:
    cartao_obj = next((c for c in cartoes if c["id"] == fat.get("cartao_id")), None)
    if cartao_obj:
        mes_fat = mes_from_label(fat["mes_inicio"])
        dia     = min(cartao_obj["dia_venc"], calendar.monthrange(mes_fat.year, mes_fat.month)[1])
        dt_fat  = date(mes_fat.year, mes_fat.month, dia)
        diff    = (dt_fat - hoje).days
        if 0 <= diff <= 5:
            alertas.append(("warn", f"💳 Fatura {cartao_obj['nome']} vence em {diff} dia(s)"))

if alertas:
    with st.expander(f"🔔 {len(alertas)} alerta(s) — clique para ver", expanded=True):
        for tipo_a, msg in alertas:
            css = "alert-warn" if tipo_a == "warn" else "alert-danger"
            st.markdown(f'<div class="{css}">{msg}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# ABAS
# ════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
    "🏠 Resumo","📝 Lançamentos","📌 Contas Fixas","💳 Cartões","📅 Calendário","📈 Projeção"])

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
                gastos = sum(f["valor"] for f in faturas
                             if f.get("cartao_id") == c["id"]
                             and mes_from_label(f["mes_inicio"]).month == hoje.month
                             and mes_from_label(f["mes_inicio"]).year == hoje.year
                             and f.get("parcelas", 1) == 1)
                uso = (gastos / c["limite"] * 100) if c["limite"] > 0 else 0
                cor_u = "#4ade80" if uso <= 70 else "#fbbf24" if uso <= 90 else "#f87171"
                st.markdown(f"""<div class="card">
                    <b style="font-family:Syne">{c['nome']}</b><br>
                    <span class="metric-label">Limite: R$ {c['limite']:,.2f} &nbsp;|&nbsp;
                    Fecha dia {c['dia_fech']} &nbsp;|&nbsp; Vence dia {c['dia_venc']}</span>
                    <div style="margin-top:8px;font-size:13px;color:{cor_u}">
                    Uso este mês: R$ {gastos:,.2f} ({uso:.0f}%)</div>
                    <div class="prog-bg"><div class="prog-fill"
                    style="width:{min(uso,100):.0f}%;background:{cor_u}"></div></div>
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

st.markdown("<br><p style='text-align:center;color:#2a2a45;font-size:11px'>Minhas Finanças · Supabase</p>", unsafe_allow_html=True)
