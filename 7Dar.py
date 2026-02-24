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

# =====================================================
# 📌 DADOS DO PROJETO
# =====================================================

st.header("📌 Dados do Projeto")

cliente = st.text_input("Cliente")
numero_os = st.text_input("Número da OS")
responsavel = st.text_input("Responsável Técnico")
modelo = st.text_input("Modelo da Máquina")

# =====================================================
# ⚙ CONFIGURAÇÃO DE MOTORES
# =====================================================

st.header("⚙ Configuração de Motores")

num_motores = st.number_input("Quantidade de Motores", 0, 10, 1)

correntes_motores = []

for i in range(num_motores):
    cv = st.number_input(f"Motor {i+1} - Potência (CV)", 0.0, 200.0, 5.0)
    corrente = round((cv * 736) / (math.sqrt(3) * 380 * 0.85), 2)
    correntes_motores.append(corrente)
    st.write(f"Corrente estimada Motor {i+1}: {corrente} A")

corrente_total_motores = sum(correntes_motores)

# =====================================================
# 🔥 RESISTÊNCIA
# =====================================================

st.header("🔥 Resistência Trifásica")

res_kw = st.number_input("Potência Total Resistência (kW)", 0.0, 500.0, 0.0)

if res_kw > 0:
    corrente_res = round((res_kw * 1000) / (math.sqrt(3) * 380), 2)
else:
    corrente_res = 0

st.write(f"Corrente Resistência: {corrente_res} A")

# =====================================================
# 📐 CABEAMENTO INTERNO
# =====================================================

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

# =====================================================
# 🔧 PARÂMETROS TÉCNICOS (NBR 5410)
# =====================================================

st.header("🔧 Parâmetros Técnicos")

metodo_instalacao = st.selectbox(
    "Método de Instalação",
    ["B1 - Eletroduto Embutido", "C - Bandeja Perfurada", "E - Ao Ar Livre"]
)

temperatura = st.number_input("Temperatura Ambiente (°C)", 10, 60, 30)
fator_agrupamento = st.number_input("Fator de Agrupamento", 0.5, 1.0, 1.0, step=0.05)
margem_seg = st.number_input("Margem de Segurança (%)", 0, 50, 20)

curva_disjuntor = st.selectbox("Curva do Disjuntor", ["B", "C", "D"])

# =====================================================
# ⚡ CÁLCULO DE CORRENTE AJUSTADA
# =====================================================

corrente_geral = corrente_total_motores + corrente_res

corrente_projeto = corrente_geral * (1 + margem_seg/100)
corrente_ajustada = corrente_projeto / fator_agrupamento

if temperatura > 30:
    fator_temp = 0.94
else:
    fator_temp = 1.0

corrente_ajustada = corrente_ajustada / fator_temp

# =====================================================
# 📊 TABELA NBR 5410 (PVC 70°C – 3 condutores carregados)
# =====================================================

tabela_cabos = {
    "B1 - Eletroduto Embutido": {
        2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 110, 50: 134
    },
    "C - Bandeja Perfurada": {
        2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 151
    },
    "E - Ao Ar Livre": {
        2.5: 27, 4: 36, 6: 46, 10: 63, 16: 85, 25: 112, 35: 138, 50: 168
    }
}

bitola_escolhida = None

for secao, capacidade in tabela_cabos[metodo_instalacao].items():
    if capacidade >= corrente_ajustada:
        bitola_escolhida = secao
        break

if bitola_escolhida is None:
    bitola_escolhida = 50

cable = f"{bitola_escolhida} mm²"

# =====================================================
# 🔌 DISJUNTOR
# =====================================================

if corrente_projeto <= 32:
    breaker = 32
elif corrente_projeto <= 63:
    breaker = 63
elif corrente_projeto <= 100:
    breaker = 100
else:
    breaker = 125

breaker_display = f"{breaker} A - Curva {curva_disjuntor}"

if bitola_escolhida <= 6:
    terminal = "Olhal M6"
elif bitola_escolhida <= 16:
    terminal = "Olhal M8"
else:
    terminal = "Olhal M10"

terminais = num_condutores * 2

# =====================================================
# 📊 RESUMO TÉCNICO
# =====================================================

st.header("📊 Resumo Técnico")

st.write(f"Corrente Total: **{round(corrente_geral,2)} A**")
st.write(f"Corrente Projeto (com margem): **{round(corrente_projeto,2)} A**")
st.write(f"Bitola Selecionada: **{cable}**")
st.write(f"Disjuntor Geral: **{breaker_display}**")

# =====================================================
# 📋 LISTA DE MATERIAIS
# =====================================================

def gerar_lista_materiais():
    materiais = []

    materiais.append(["Disjuntor Geral", breaker_display, 1, "peça"])
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

# =====================================================
# 📊 EXPORTAR EXCEL
# =====================================================

def gerar_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return buffer

st.download_button("📊 Baixar Excel", gerar_excel(df_materiais), "lista_materiais.xlsx")

# =====================================================
# 📄 EXPORTAR PDF
# =====================================================

def gerar_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    style = getSampleStyleSheet()

    elements.append(Paragraph("AirSide PRO - Relatório Técnico", style['Heading1']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Cliente: {cliente}", style['Normal']))
    elements.append(Paragraph(f"OS: {numero_os}", style['Normal']))
    elements.append(Paragraph(f"Responsável: {responsavel}", style['Normal']))
    elements.append(Paragraph(f"Modelo: {modelo}", style['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Bitola: {cable}", style['Normal']))
    elements.append(Paragraph(f"Disjuntor: {breaker_display}", style['Normal']))
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

st.download_button("📄 Baixar PDF", gerar_pdf(df_materiais), "relatorio_tecnico.pdf")
