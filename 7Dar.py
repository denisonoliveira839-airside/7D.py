import streamlit as st
import pandas as pd
import math
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

st.set_page_config(page_title="AirSide PRO", layout="wide")

st.title("🏭 AirSide PRO – Plataforma de Engenharia HVAC")

# ===============================
# 📌 DADOS DO PROJETO
# ===============================

st.header("📌 Dados do Projeto")

cliente = st.text_input("Cliente")
os = st.text_input("Número da OS")
responsavel = st.text_input("Responsável Técnico")
modelo = st.text_input("Modelo da Máquina")

# ===============================
# ⚙ CONFIGURAÇÃO DE MOTORES
# ===============================

st.header("⚙ Configuração de Motores")

num_motores = st.number_input("Quantidade de Motores", 0, 10, 1)

potencias = []
correntes_motores = []

for i in range(num_motores):
    cv = st.number_input(f"Motor {i+1} - Potência (CV)", 0.0, 200.0, 5.0)
    potencias.append(cv)

    corrente = round((cv * 736) / (math.sqrt(3) * 380 * 0.85), 2)
    correntes_motores.append(corrente)

    st.write(f"Corrente estimada Motor {i+1}: {corrente} A")

corrente_total_motores = sum(correntes_motores)

# ===============================
# 🔥 RESISTÊNCIA
# ===============================

st.header("🔥 Resistência Trifásica")

res_kw = st.number_input("Potência Total Resistência (kW)", 0.0, 500.0, 0.0)

if res_kw > 0:
    corrente_res = round((res_kw * 1000) / (math.sqrt(3) * 380), 2)
else:
    corrente_res = 0

st.write(f"Corrente Resistência: {corrente_res} A")

# ===============================
# 📐 CABEAMENTO INTERNO
# ===============================

st.header("📐 Cabeamento Interno")

col1, col2, col3 = st.columns(3)

altura = col1.number_input("Altura (mm)", 500, 5000, 900)
largura = col2.number_input("Largura (mm)", 500, 5000, 800)
profundidade = col3.number_input("Profundidade (mm)", 300, 3000, 600)

tensao = st.selectbox("Tensão", [220, 380])
rota = st.selectbox("Tipo Roteamento", ["Simples", "Organizado"])

fator = 1.4 if rota == "Simples" else 1.8
percurso_base = (altura + largura) / 1000
metragem_total = round(percurso_base * fator, 2)

num_condutores = 4 if tensao == 380 else 3
metragem_final = round(metragem_total * num_condutores, 2)

# ===============================
# 🔌 DIMENSIONAMENTO GERAL
# ===============================

corrente_geral = corrente_total_motores + corrente_res

if corrente_geral <= 25:
    cable = "4 mm²"
    terminal = "Olhal M6"
    breaker = 32
elif corrente_geral <= 50:
    cable = "10 mm²"
    terminal = "Olhal M8"
    breaker = 63
else:
    cable = "25 mm²"
    terminal = "Olhal M10"
    breaker = 125

terminais = num_condutores * 2

# ===============================
# 📊 RESUMO TÉCNICO
# ===============================

st.header("📊 Resumo Técnico do Projeto")

st.write(f"**Cliente:** {cliente}")
st.write(f"**OS:** {os}")
st.write(f"**Responsável:** {responsavel}")
st.write(f"**Modelo:** {modelo}")
st.write("---")
st.write(f"Corrente Total do Sistema: **{round(corrente_geral,2)} A**")
st.write(f"Disjuntor Geral Sugerido: **{breaker} A**")
st.write(f"Bitola Principal Sugerida: **{cable}**")

# ===============================
# 📋 LISTA DE MATERIAIS
# ===============================

def gerar_lista_materiais():
    materiais = []

    materiais.append(["Disjuntor Geral", f"{breaker} A", 1, "peça"])
    materiais.append(["Cabo Alimentação", cable, metragem_final, "metros"])
    materiais.append(["Barramento de Cobre", "Compatível corrente", 1, "conjunto"])
    materiais.append([f"Terminal {terminal}", terminal, terminais, "peças"])

    for i in range(num_motores):
        materiais.append([f"Contator Motor {i+1}", "Compatível corrente", 1, "peça"])
        materiais.append([f"Relé Térmico Motor {i+1}", "Compatível corrente", 1, "peça"])
        materiais.append([f"Cabo Motor {i+1}", cable, metragem_total, "metros"])
        materiais.append([f"Terminais Motor {i+1}", terminal, 6, "peças"])

    if res_kw > 0:
        materiais.append(["Contator Resistência", "Compatível potência", 1, "peça"])
        materiais.append(["Disjuntor Resistência", "Curva C", 1, "peça"])
        materiais.append(["Cabo Resistência", cable, metragem_total, "metros"])
        materiais.append(["Terminais Resistência", terminal, 6, "peças"])

    return pd.DataFrame(
        materiais,
        columns=["Item", "Especificação", "Quantidade", "Unidade"]
    )

df_materiais = gerar_lista_materiais()

st.subheader("📋 Lista de Materiais")
st.dataframe(df_materiais)

# ===============================
# 📤 EXPORTAR EXCEL
# ===============================

def gerar_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer

excel_file = gerar_excel(df_materiais)

st.download_button(
    "📊 Baixar Excel",
    excel_file,
    file_name="lista_materiais.xlsx"
)

# ===============================
# 📄 EXPORTAR PDF
# ===============================

def gerar_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    style = getSampleStyleSheet()

    elements.append(Paragraph("AirSide PRO - Relatório Técnico", style['Heading1']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Cliente: {cliente}", style['Normal']))
    elements.append(Paragraph(f"OS: {os}", style['Normal']))
    elements.append(Paragraph(f"Responsável: {responsavel}", style['Normal']))
    elements.append(Paragraph(f"Modelo: {modelo}", style['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Corrente Total: {round(corrente_geral,2)} A", style['Normal']))
    elements.append(Paragraph(f"Disjuntor Geral: {breaker} A", style['Normal']))
    elements.append(Paragraph(f"Bitola Principal: {cable}", style['Normal']))
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

pdf_file = gerar_pdf(df_materiais)

st.download_button(
    "📄 Baixar PDF",
    pdf_file,
    file_name="relatorio_tecnico.pdf"
)
