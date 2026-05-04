import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json, os, calendar

# ── Página ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="💰 Finanças", page_icon="💰", layout="wide",
                   initial_sidebar_state="collapsed")

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
h1,h2,h3{font-family:'Syne',sans-serif;}
.stApp{background-color:#0d0d14;color:#e8e8f0;}
section[data-testid="stSidebar"]{background:#13131e;border-right:1px solid #252535;}
.card{background:linear-gradient(135deg,#16161f,#1e1e2e);border:1px solid #252535;
      border-radius:16px;padding:20px 22px;margin-bottom:8px;}
.metric-label{font-size:11px;color:#6666a0;letter-spacing:1.2px;text-transform:uppercase;}
.metric-value{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;margin-top:2px;}
.green{color:#4ade80;} .red{color:#f87171;} .blue{color:#60a5fa;}
.yellow{color:#fbbf24;} .purple{color:#a78bfa;}
.tag{padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700;}
.tag-r{background:#14532d;color:#4ade80;} .tag-d{background:#7f1d1d;color:#f87171;}
.tag-c{background:#1e3a5f;color:#60a5fa;} .tag-f{background:#3b1f6e;color:#a78bfa;}
.stButton>button{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;
  border:none;border-radius:10px;font-family:'Syne',sans-serif;font-weight:700;
  padding:9px 22px;transition:opacity .2s;}
.stButton>button:hover{opacity:.82;}
.stTabs [data-baseweb="tab-list"]{background:#13131e;border-radius:12px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{border-radius:10px;color:#7878a0;font-family:'Syne',sans-serif;
  font-weight:700;padding:8px 20px;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:#fff!important;}
.alert-warn{background:#2d2000;border:1px solid #d97706;border-radius:12px;
  padding:12px 18px;margin:6px 0;color:#fbbf24;}
.alert-danger{background:#2d0000;border:1px solid #dc2626;border-radius:12px;
  padding:12px 18px;margin:6px 0;color:#f87171;}
.alert-ok{background:#002d10;border:1px solid #16a34a;border-radius:12px;
  padding:12px 18px;margin:6px 0;color:#4ade80;}
table{width:100%;border-collapse:collapse;}
th{background:#1c1c2e;color:#7878a0;font-size:11px;letter-spacing:.8px;
   text-transform:uppercase;padding:10px 14px;text-align:left;}
td{padding:10px 14px;border-bottom:1px solid #1c1c2e;font-size:13px;}
tr:hover td{background:#16161f;}
input,select{background:#16161f!important;border:1px solid #252535!important;
  color:#e8e8f0!important;border-radius:10px!important;}
.prog-bg{background:#1e1e2e;border-radius:8px;height:10px;margin-top:6px;}
.prog-fill{height:10px;border-radius:8px;}
</style>
""", unsafe_allow_html=True)

# ── Dados ────────────────────────────────────────────────────────────────────
DATA_FILE = "financas_v2.json"

def load():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            d = json.load(f)
    else:
        d = {}
    d.setdefault("transacoes", [])
    d.setdefault("contas_fixas", [])
    d.setdefault("cartoes", [])
    d.setdefault("faturas", [])       # gastos no cartão
    d.setdefault("metas", {})
    d.setdefault("next_id", 1)
    return d

def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def new_id(d):
    i = d["next_id"]; d["next_id"] += 1; return i

if "d" not in st.session_state:
    st.session_state.d = load()
D = st.session_state.d

# ── Helpers ──────────────────────────────────────────────────────────────────
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
    m,y = s.split("/"); return date(int(y),int(m),1)

def gerar_meses(n=12):
    hoje = date.today()
    return [mes_label(hoje + relativedelta(months=i)) for i in range(-3, n)]

def transacoes_df():
    rows = []
    # lançamentos manuais
    for t in D["transacoes"]:
        rows.append({**t, "origem":"manual"})
    # contas fixas expandidas
    for cf in D["contas_fixas"]:
        inicio = mes_from_label(cf["mes_inicio"])
        for i in range(cf["meses"]):
            mes = inicio + relativedelta(months=i)
            dia = min(cf["dia_venc"], calendar.monthrange(mes.year, mes.month)[1])
            dt  = date(mes.year, mes.month, dia)
            rows.append({
                "id": f"cf_{cf['id']}_{i}", "tipo":"Despesa",
                "descricao": cf["descricao"], "valor": cf["valor"],
                "categoria": cf["categoria"], "data": str(dt),
                "origem":"fixa", "cf_id": cf["id"]
            })
    # faturas de cartão
    for fat in D["faturas"]:
        if fat.get("parcelas",1) == 1:
            rows.append({**fat, "tipo":"Despesa", "origem":"cartao"})
        else:
            for p in range(fat["parcelas"]):
                mes_p = mes_from_label(fat["mes_inicio"]) + relativedelta(months=p)
                dia   = min(fat["dia_venc"], calendar.monthrange(mes_p.year, mes_p.month)[1])
                dt    = date(mes_p.year, mes_p.month, dia)
                rows.append({
                    "id": f"fat_{fat['id']}_{p}", "tipo":"Despesa",
                    "descricao": f"{fat['descricao']} ({p+1}/{fat['parcelas']})",
                    "valor": round(fat["valor"]/fat["parcelas"],2),
                    "categoria": fat.get("categoria","💳 Cartão"),
                    "data": str(dt), "origem":"cartao",
                    "cartao": fat.get("cartao","")
                })
    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["id","tipo","descricao","valor","categoria","data","origem"])
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
        df["mes"]  = df["data"].dt.strftime("%m/%Y")
    return df

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-family:Syne;font-size:2rem;margin-bottom:0'>💰 Minhas Finanças</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:#6666a0;margin-top:0'>{datetime.now().strftime('%A, %d/%m/%Y')}</p>", unsafe_allow_html=True)

df_all = transacoes_df()
hoje   = date.today()

# ── Alertas rápidos ──────────────────────────────────────────────────────────
alertas = []
for cf in D["contas_fixas"]:
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

for fat in D["faturas"]:
    cartao = next((c for c in D["cartoes"] if c["id"]==fat.get("cartao_id")), None)
    if cartao:
        mes_fat = mes_from_label(fat["mes_inicio"])
        dia     = min(cartao["dia_venc"], calendar.monthrange(mes_fat.year, mes_fat.month)[1])
        dt_fat  = date(mes_fat.year, mes_fat.month, dia)
        diff    = (dt_fat - hoje).days
        if 0 <= diff <= 5:
            alertas.append(("warn", f"💳 Fatura {cartao['nome']} vence em {diff} dia(s)"))

if alertas:
    with st.expander(f"🔔 {len(alertas)} alerta(s) — clique para ver", expanded=True):
        for tipo_a, msg in alertas:
            css = "alert-warn" if tipo_a=="warn" else "alert-danger"
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

    df_m = df_all[df_all["mes"]==mes_sel] if not df_all.empty else pd.DataFrame()
    rec  = df_m[df_m["tipo"]=="Receita"]["valor"].sum() if not df_m.empty else 0
    desp = df_m[df_m["tipo"]=="Despesa"]["valor"].sum() if not df_m.empty else 0
    saldo= rec - desp
    meta = D["metas"].get(mes_sel, 0)
    pct  = (desp/meta*100) if meta>0 else 0

    c1,c2,c3,c4 = st.columns(4)
    def mcard(col, label, val, cls, extra=""):
        col.markdown(f'<div class="card"><div class="metric-label">{label}</div>'
                     f'<div class="metric-value {cls}">R$ {val:,.2f}</div>{extra}</div>', unsafe_allow_html=True)

    mcard(c1,"Saldo do mês", saldo, "green" if saldo>=0 else "red")
    mcard(c2,"Receitas", rec, "green")
    mcard(c3,"Despesas", desp, "red")
    cor_m = "#4ade80" if pct<=80 else "#fbbf24" if pct<=100 else "#f87171"
    c4.markdown(f'<div class="card"><div class="metric-label">Meta de gastos</div>'
                f'<div class="metric-value" style="color:{cor_m}">{pct:.0f}%</div>'
                f'<div style="font-size:12px;color:#6666a0">R$ {desp:,.2f} / R$ {meta:,.2f}</div>'
                f'<div class="prog-bg"><div class="prog-fill" style="width:{min(pct,100):.0f}%;background:{cor_m}"></div></div>'
                f'</div>', unsafe_allow_html=True)

    with st.expander("🎯 Definir meta mensal"):
        m_val = st.number_input("Limite (R$)", 0.0, step=50.0, format="%.2f", key="meta_val")
        if st.button("Salvar meta"):
            D["metas"][mes_sel] = m_val; save(D); st.success("Salvo!"); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if not df_m.empty:
        g1,g2 = st.columns(2)
        with g1:
            st.markdown("### Despesas por Categoria")
            dc = df_m[df_m["tipo"]=="Despesa"].groupby("categoria")["valor"].sum().reset_index()
            if not dc.empty:
                fig = px.pie(dc,values="valor",names="categoria",hole=.45,
                             color_discrete_sequence=px.colors.sequential.Plasma_r)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",font_color="#e8e8f0",
                                  margin=dict(t=10,b=10,l=10,r=10))
                st.plotly_chart(fig,use_container_width=True)
        with g2:
            st.markdown("### Receitas vs Despesas")
            res = df_all.groupby(["mes","tipo"])["valor"].sum().reset_index()
            fig2= px.bar(res,x="mes",y="valor",color="tipo",barmode="group",
                         color_discrete_map={"Receita":"#4ade80","Despesa":"#f87171"})
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",font_color="#e8e8f0",
                               plot_bgcolor="rgba(0,0,0,0)",xaxis=dict(gridcolor="#1e1e2e"),
                               yaxis=dict(gridcolor="#1e1e2e"),legend_title="",
                               margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig2,use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 2 — LANÇAMENTOS MANUAIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.markdown("### ➕ Novo Lançamento")
    c1,c2,c3 = st.columns(3)
    tipo_l = c1.selectbox("Tipo",["Despesa","Receita"],key="tipo_l")
    desc_l = c2.text_input("Descrição",key="desc_l")
    val_l  = c3.number_input("Valor (R$)",0.01,step=0.01,format="%.2f",key="val_l")
    c4,c5  = st.columns(2)
    cats   = CATS_D if tipo_l=="Despesa" else CATS_R
    cat_l  = c4.selectbox("Categoria",cats,key="cat_l")
    data_l = c5.date_input("Data",date.today(),key="data_l")
    if st.button("💾 Salvar Lançamento"):
        if desc_l:
            D["transacoes"].append({"id":new_id(D),"tipo":tipo_l,"descricao":desc_l,
                "valor":val_l,"categoria":cat_l,"data":str(data_l)})
            save(D); st.success("Salvo!"); st.rerun()
        else: st.error("Preencha a descrição.")

    st.markdown("---")
    st.markdown("### 📋 Lançamentos Manuais")
    manual = [t for t in D["transacoes"]]
    if manual:
        df_man = pd.DataFrame(manual).sort_values("data",ascending=False)
        df_man["Data"]   = pd.to_datetime(df_man["data"]).dt.strftime("%d/%m/%Y")
        df_man["Tipo"]   = df_man["tipo"].apply(lambda x:
            f'<span class="tag tag-r">Receita</span>' if x=="Receita"
            else f'<span class="tag tag-d">Despesa</span>')
        df_man["Valor"]  = df_man["valor"].apply(lambda v: f"R$ {v:,.2f}")
        df_man = df_man.rename(columns={"descricao":"Descrição","categoria":"Categoria"})
        st.write(df_man[["Data","Tipo","Descrição","Categoria","Valor"]].to_html(
            escape=False,index=False,border=0),unsafe_allow_html=True)
        with st.expander("🗑️ Excluir lançamento"):
            ids_m = [t["id"] for t in D["transacoes"]]
            descs = [f'{t["id"]} — {t["descricao"]} ({t["data"]})' for t in D["transacoes"]]
            sel   = st.selectbox("Lançamento",descs,key="del_man") if descs else None
            if sel and st.button("Excluir",key="btn_del_man"):
                idx = descs.index(sel); del_id = ids_m[idx]
                D["transacoes"] = [t for t in D["transacoes"] if t["id"]!=del_id]
                save(D); st.success("Excluído!"); st.rerun()
    else:
        st.info("Nenhum lançamento ainda.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 3 — CONTAS FIXAS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown("### 📌 Cadastrar Conta Fixa / Recorrente")
    c1,c2,c3 = st.columns(3)
    desc_f = c1.text_input("Descrição",key="desc_f")
    val_f  = c2.number_input("Valor (R$)",0.01,step=0.01,format="%.2f",key="val_f")
    cat_f  = c3.selectbox("Categoria",CATS_D,key="cat_f")
    c4,c5,c6 = st.columns(3)
    dia_f  = c4.number_input("Dia de vencimento",1,31,step=1,key="dia_f")
    meses_opts = gerar_meses(24)
    mes_ini_f = c5.selectbox("Mês início",meses_opts,
                             index=meses_opts.index(mes_label(date.today())),key="mes_ini_f")
    rep_f  = c6.number_input("Repetir por quantos meses",1,120,step=1,key="rep_f")

    if st.button("💾 Salvar Conta Fixa"):
        if desc_f:
            D["contas_fixas"].append({"id":new_id(D),"descricao":desc_f,"valor":val_f,
                "categoria":cat_f,"dia_venc":int(dia_f),"mes_inicio":mes_ini_f,"meses":int(rep_f)})
            save(D); st.success("Salvo!"); st.rerun()
        else: st.error("Preencha a descrição.")

    st.markdown("---")
    st.markdown("### 📋 Contas Fixas Cadastradas")
    if D["contas_fixas"]:
        rows = []
        for cf in D["contas_fixas"]:
            fim = mes_label(mes_from_label(cf["mes_inicio"]) + relativedelta(months=cf["meses"]-1))
            rows.append({"ID":cf["id"],"Descrição":cf["descricao"],"Valor":f'R$ {cf["valor"]:,.2f}',
                         "Categoria":cf["categoria"],"Venc.":f'Dia {cf["dia_venc"]}',
                         "Período":f'{cf["mes_inicio"]} → {fim}',"Meses":cf["meses"]})
        st.write(pd.DataFrame(rows).to_html(index=False,border=0),unsafe_allow_html=True)
        with st.expander("🗑️ Excluir conta fixa"):
            descs_f = [f'{cf["id"]} — {cf["descricao"]}' for cf in D["contas_fixas"]]
            sel_f   = st.selectbox("Conta",descs_f,key="del_cf") if descs_f else None
            if sel_f and st.button("Excluir",key="btn_del_cf"):
                del_id  = int(sel_f.split(" — ")[0])
                D["contas_fixas"] = [cf for cf in D["contas_fixas"] if cf["id"]!=del_id]
                save(D); st.success("Excluído!"); st.rerun()
    else:
        st.info("Nenhuma conta fixa cadastrada.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 4 — CARTÕES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 💳 Cadastrar Cartão")
        nome_c  = st.text_input("Nome do cartão (ex: Nubank)",key="nome_c")
        lim_c   = st.number_input("Limite (R$)",0.0,step=50.0,format="%.2f",key="lim_c")
        fech_c  = st.number_input("Dia de fechamento",1,28,step=1,key="fech_c")
        venc_c  = st.number_input("Dia de vencimento",1,31,step=1,key="venc_c")
        if st.button("💾 Salvar Cartão"):
            if nome_c:
                D["cartoes"].append({"id":new_id(D),"nome":nome_c,"limite":lim_c,
                    "dia_fech":int(fech_c),"dia_venc":int(venc_c)})
                save(D); st.success("Cartão salvo!"); st.rerun()
            else: st.error("Informe o nome.")

    with col_b:
        st.markdown("### 💳 Cartões cadastrados")
        if D["cartoes"]:
            for c in D["cartoes"]:
                # gastos do cartão no mês atual
                gastos = sum(f["valor"] for f in D["faturas"]
                             if f.get("cartao_id")==c["id"] and
                             mes_from_label(f["mes_inicio"]).month==hoje.month and
                             mes_from_label(f["mes_inicio"]).year==hoje.year
                             and f.get("parcelas",1)==1)
                uso = (gastos/c["limite"]*100) if c["limite"]>0 else 0
                cor_u = "#4ade80" if uso<=70 else "#fbbf24" if uso<=90 else "#f87171"
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
    if D["cartoes"]:
        c1,c2,c3 = st.columns(3)
        cart_opts = {c["nome"]:c["id"] for c in D["cartoes"]}
        cart_sel  = c1.selectbox("Cartão",list(cart_opts.keys()),key="cart_sel")
        desc_fat  = c2.text_input("Descrição",key="desc_fat")
        val_fat   = c3.number_input("Valor total (R$)",0.01,step=0.01,format="%.2f",key="val_fat")
        c4,c5,c6  = st.columns(3)
        parc_fat  = c4.number_input("Parcelas",1,48,step=1,key="parc_fat")
        cat_fat   = c5.selectbox("Categoria",CATS_D,key="cat_fat")
        meses_opts2 = gerar_meses(24)
        mes_fat_ini = c6.selectbox("Mês 1ª parcela",meses_opts2,
                                   index=meses_opts2.index(mes_label(date.today())),key="mes_fat_ini")
        cartao_obj = next(c for c in D["cartoes"] if c["nome"]==cart_sel)
        if st.button("💾 Salvar Gasto"):
            if desc_fat:
                D["faturas"].append({"id":new_id(D),"cartao_id":cart_opts[cart_sel],
                    "cartao":cart_sel,"descricao":desc_fat,"valor":val_fat,
                    "parcelas":int(parc_fat),"categoria":cat_fat,
                    "mes_inicio":mes_fat_ini,"dia_venc":cartao_obj["dia_venc"]})
                save(D); st.success("Salvo!"); st.rerun()
            else: st.error("Preencha a descrição.")

        st.markdown("### 📋 Gastos no Cartão")
        if D["faturas"]:
            rows_f = []
            for f in D["faturas"]:
                fim_f = mes_label(mes_from_label(f["mes_inicio"]) + relativedelta(months=f["parcelas"]-1))
                rows_f.append({"Cartão":f.get("cartao",""),"Descrição":f["descricao"],
                    "Valor Total":f'R$ {f["valor"]:,.2f}',
                    "Parc.":f'{f["parcelas"]}x R$ {f["valor"]/f["parcelas"]:,.2f}',
                    "Período":f'{f["mes_inicio"]} → {fim_f}'})
            st.write(pd.DataFrame(rows_f).to_html(index=False,border=0),unsafe_allow_html=True)
            with st.expander("🗑️ Excluir gasto"):
                descs_fat = [f'{f["id"]} — {f["descricao"]} ({f.get("cartao","")})' for f in D["faturas"]]
                sel_fat   = st.selectbox("Gasto",descs_fat,key="del_fat") if descs_fat else None
                if sel_fat and st.button("Excluir",key="btn_del_fat"):
                    del_id = int(sel_fat.split(" — ")[0])
                    D["faturas"] = [f for f in D["faturas"] if f["id"]!=del_id]
                    save(D); st.success("Excluído!"); st.rerun()
    else:
        st.warning("Cadastre um cartão primeiro.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 5 — CALENDÁRIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab5:
    st.markdown("### 📅 Contas a Pagar — Calendário")
    meses_cal = gerar_meses(6)
    mes_cal   = st.selectbox("Mês",meses_cal,index=3,key="mes_cal")

    df_cal = df_all[(df_all["mes"]==mes_cal) & (df_all["tipo"]=="Despesa")] if not df_all.empty else pd.DataFrame()

    if not df_cal.empty:
        df_cal_s = df_cal.sort_values("data")
        mes_obj  = mes_from_label(mes_cal)
        primeiro, ultimo = mes_obj, mes_obj + relativedelta(months=1) - timedelta(days=1)

        # grid semanal
        semanas = calendar.monthcalendar(mes_obj.year, mes_obj.month)
        dias_semana = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]

        html = '<table style="width:100%;table-layout:fixed">'
        html += '<tr>' + ''.join(f'<th style="text-align:center">{d}</th>' for d in dias_semana) + '</tr>'
        for sem in semanas:
            html += '<tr>'
            for dia in sem:
                if dia == 0:
                    html += '<td style="height:80px;vertical-align:top;background:#0d0d14"></td>'
                else:
                    dt_dia = date(mes_obj.year, mes_obj.month, dia)
                    contas_dia = df_cal_s[df_cal_s["data"].dt.date == dt_dia]
                    bg = "#16161f" if dt_dia != hoje else "#1e1e35"
                    brd = "2px solid #6366f1" if dt_dia == hoje else "1px solid #252535"
                    cell = f'<div style="font-size:12px;color:#7878a0;font-weight:700">{dia}</div>'
                    for _,row in contas_dia.iterrows():
                        cor_tag = "#60a5fa" if row.get("origem")=="cartao" else "#a78bfa" if row.get("origem")=="fixa" else "#f87171"
                        cell += f'<div style="background:{cor_tag}22;color:{cor_tag};font-size:10px;border-radius:6px;padding:2px 5px;margin-top:2px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis">{row["descricao"][:16]} R${row["valor"]:,.0f}</div>'
                    html += f'<td style="height:90px;vertical-align:top;padding:6px;background:{bg};border:{brd};border-radius:8px">{cell}</td>'
            html += '</tr>'
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Legenda:** <span style='color:#a78bfa'>■ Conta fixa</span> &nbsp; <span style='color:#60a5fa'>■ Cartão</span> &nbsp; <span style='color:#f87171'>■ Manual</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Lista do mês")
        df_cal_s["Data"]  = df_cal_s["data"].dt.strftime("%d/%m")
        df_cal_s["Valor"] = df_cal_s["valor"].apply(lambda v: f"R$ {v:,.2f}")
        def origem_tag(o):
            if o=="fixa":   return '<span class="tag tag-f">Fixa</span>'
            if o=="cartao": return '<span class="tag tag-c">Cartão</span>'
            return '<span class="tag tag-d">Manual</span>'
        df_cal_s["Origem"] = df_cal_s["origem"].apply(origem_tag)
        st.write(df_cal_s[["Data","descricao","categoria","Valor","Origem"]].rename(
            columns={"descricao":"Descrição","categoria":"Categoria"}).to_html(
            escape=False,index=False,border=0),unsafe_allow_html=True)
    else:
        st.info("Nenhuma despesa neste mês.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ABA 6 — PROJEÇÃO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab6:
    st.markdown("### 📈 Projeção de Saldo — Próximos 12 Meses")
    meses_proj = [mes_label(date.today() + relativedelta(months=i)) for i in range(13)]

    rows_proj = []
    saldo_acum = 0
    for mes_p in meses_proj:
        df_p = df_all[df_all["mes"]==mes_p] if not df_all.empty else pd.DataFrame()
        rec_p  = df_p[df_p["tipo"]=="Receita"]["valor"].sum() if not df_p.empty else 0
        desp_p = df_p[df_p["tipo"]=="Despesa"]["valor"].sum() if not df_p.empty else 0
        saldo_mes = rec_p - desp_p
        saldo_acum += saldo_mes
        rows_proj.append({"Mês":mes_p,"Receitas":rec_p,"Despesas":desp_p,
                          "Resultado":saldo_mes,"Saldo Acumulado":saldo_acum})

    df_proj = pd.DataFrame(rows_proj)

    # Gráfico área
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(x=df_proj["Mês"], y=df_proj["Saldo Acumulado"],
        mode="lines+markers", name="Saldo Acumulado",
        line=dict(color="#6366f1",width=3), fill="tozeroy",
        fillcolor="rgba(99,102,241,0.12)", marker=dict(size=7)))
    fig_proj.add_trace(go.Bar(x=df_proj["Mês"], y=df_proj["Receitas"],
        name="Receitas", marker_color="rgba(74,222,128,0.33)", yaxis="y"))
    fig_proj.add_trace(go.Bar(x=df_proj["Mês"], y=[-v for v in df_proj["Despesas"]],
        name="Despesas", marker_color="rgba(248,113,113,0.33)", yaxis="y"))
    fig_proj.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e8e8f0", xaxis=dict(gridcolor="#1e1e2e"),
        yaxis=dict(gridcolor="#1e1e2e"), barmode="relative",
        legend=dict(orientation="h",y=1.1), margin=dict(t=20,b=10,l=10,r=10))
    st.plotly_chart(fig_proj, use_container_width=True)

    # Tabela resumo
    st.markdown("### Tabela de Projeção")
    df_show = df_proj.copy()
    def fmt(v,positivo=True):
        cor = "#4ade80" if v>=0 else "#f87171"
        return f'<span style="color:{cor}">R$ {v:,.2f}</span>'
    df_show["Receitas"]        = df_show["Receitas"].apply(lambda v: f"R$ {v:,.2f}")
    df_show["Despesas"]        = df_show["Despesas"].apply(lambda v: f"R$ {v:,.2f}")
    df_show["Resultado"]       = df_show["Resultado"].apply(fmt)
    df_show["Saldo Acumulado"] = df_show["Saldo Acumulado"].apply(fmt)
    st.write(df_show.to_html(escape=False,index=False,border=0), unsafe_allow_html=True)

    # Alertas projeção
    st.markdown("---")
    st.markdown("### 🔍 Análise")
    meses_neg = [r["Mês"] for r in rows_proj if r["Resultado"] < 0]
    if meses_neg:
        st.markdown(f'<div class="alert-warn">⚠️ Meses com resultado negativo projetado: {", ".join(meses_neg)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-ok">✅ Todos os meses projetados com resultado positivo!</div>', unsafe_allow_html=True)

    melhor = df_proj.loc[df_proj["Resultado"].idxmax()]["Mês"]
    pior   = df_proj.loc[df_proj["Resultado"].idxmin()]["Mês"]
    st.markdown(f'<div class="card" style="margin-top:12px">🏆 <b>Melhor mês projetado:</b> {melhor} &nbsp;&nbsp; 📉 <b>Pior mês:</b> {pior}</div>', unsafe_allow_html=True)

st.markdown("<br><p style='text-align:center;color:#2a2a45;font-size:11px'>Minhas Finanças v2 · dados em financas_v2.json</p>", unsafe_allow_html=True)
