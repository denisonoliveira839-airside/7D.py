import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="AirSide PRO",
    layout="centered"
)

st.title("🏭 AirSide PRO")
st.caption("Plataforma Profissional de Dimensionamento Elétrico HVAC")

st.divider()

# =========================
# ABAS PRINCIPAIS
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 Projeto",
    "⚙ Engenharia",
    "📊 Resultados",
    "📋 Materiais",
    "📄 Exportação"
])

# =========================
# ABA 1 – PROJETO
# =========================
with tab1:
    st.subheader("Dados do Projeto")
    cliente = st.text_input("Cliente")
    numero_os = st.text_input("Número da OS")
    responsavel = st.text_input("Responsável Técnico")
    modelo = st.text_input("Modelo da Máquina")

# =========================
# ABA 2 – ENGENHARIA
# =========================
with tab2:
    st.subheader("Configuração de Motores")

    num_motores = st.number_input("Quantidade de Motores", 0, 10, 1)
    correntes_motores = []

    for i in range(num_motores):
        cv = st.number_input(f"Motor {i+1} - Potência (CV)", 0.0, 200.0, 5.0)
        corrente = round((cv * 736) / (math.sqrt(3) * 380 * 0.85), 2)
        correntes_motores.append(corrente)
        st.write(f"Corrente estimada: {corrente} A")

    corrente_total_motores = sum(correntes_motores)

    st.subheader("Resistência Trifásica")
    res_kw = st.number_input("Potência Total (kW)", 0.0, 500.0, 0.0)

    if res_kw > 0:
        corrente_res = round((res_kw * 1000) / (math.sqrt(3) * 380), 2)
    else:
        corrente_res = 0

    st.write(f"Corrente Resistência: {corrente_res} A")

    st.subheader("Parâmetros Técnicos")

    metodo_instalacao = st.selectbox(
        "Método de Instalação",
        ["B1 - Eletroduto Embutido", "C - Bandeja Perfurada", "E - Ao Ar Livre"]
    )

    temperatura = st.number_input("Temperatura Ambiente (°C)", 10, 60, 30)
    fator_agrupamento = st.number_input("Fator de Agrupamento", 0.5, 1.0, 1.0, step=0.05)
    margem_seg = st.number_input("Margem de Segurança (%)", 0, 50, 20)
    curva_disjuntor = st.selectbox("Curva do Disjuntor", ["B", "C", "D"])

# =========================
# CÁLCULOS
# =========================

corrente_geral = corrente_total_motores + corrente_res
corrente_projeto = corrente_geral * (1 + margem_seg/100)
corrente_ajustada = corrente_projeto / fator_agrupamento

if temperatura > 30:
    fator_temp = 0.94
else:
    fator_temp = 1.0

corrente_ajustada = corrente_ajustada / fator_temp

tabela_cabos = {
    "B1 - Eletroduto Embutido": {2.5:21,4:28,6:36,10:50,16:68,25:89,35:110,50:134},
    "C - Bandeja Perfurada": {2.5:24,4:32,6:41,10:57,16:76,25:101,35:125,50:151},
    "E - Ao Ar Livre": {2.5:27,4:36,6:46,10:63,16:85,25:112,35:138,50:168}
}

bitola_escolhida = None
for secao, capacidade in tabela_cabos[metodo_instalacao].items():
    if capacidade >= corrente_ajustada:
        bitola_escolhida = secao
        break

if bitola_escolhida is None:
    bitola_escolhida = 50

cable = f"{bitola_escolhida} mm²"

if corrente_projeto <= 32:
    breaker = 32
elif corrente_projeto <= 63:
    breaker = 63
elif corrente_projeto <= 100:
    breaker = 100
else:
    breaker = 125

breaker_display = f"{breaker} A - Curva {curva_disjuntor}"

# =========================
# ABA 3 – RESULTADOS
# =========================
with tab3:
    st.subheader("Resumo Técnico")

    col1, col2 = st.columns(2)
    col1.metric("Corrente Total", f"{round(corrente_geral,2)} A")
    col2.metric("Corrente Projeto", f"{round(corrente_projeto,2)} A")

    col3, col4 = st.columns(2)
    col3.metric("Bitola Selecionada", cable)
    col4.metric("Disjuntor Geral", breaker_display)

# =========================
# ABA 4 – MATERIAIS
# =========================
with tab4:

    def gerar_lista():
        materiais = [
            ["Disjuntor Geral", breaker_display, 1, "peça"],
            ["Cabo Alimentação", cable, 10, "metros"],
            ["Barramento", "Compatível corrente", 1, "conjunto"]
        ]
        return pd.DataFrame(materiais, columns=["Item","Especificação","Qtd","Unidade"])

    df = gerar_lista()
    st.dataframe(df)

# =========================
# ABA 5 – EXPORTAÇÃO
# =========================
with tab5:

    def gerar_excel(df):
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        return buffer

    def gerar_pdf(df):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        style = getSampleStyleSheet()

        elements.append(Paragraph("AirSide PRO - Relatório Técnico", style['Heading1']))
        elements.append(Spacer(1, 20))

        data = [df.columns.tolist()] + df.values.tolist()
        table = Table(data)
        table.setStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ])

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    st.download_button("📊 Baixar Excel", gerar_excel(df), "materiais.xlsx")
    st.download_button("📄 Baixar PDF", gerar_pdf(df), "relatorio.pdf")
