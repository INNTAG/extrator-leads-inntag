import streamlit as st
import fitz  # PyMuPDF
import tempfile
import re
import base64
import requests
import io

# 🌞 Paleta Inntag (tom de laranja, cinza claro, verde claro)
INNTAG_PRIMARY = "#FF8200"
INNTAG_SECONDARY = "#E9ECEF"
INNTAG_ACCENT = "#7DBE31"

st.set_page_config(page_title="Extração de Conta - Inntag Energia Solar", layout="centered")

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {INNTAG_SECONDARY};
        }}
        .title {{
            color: {INNTAG_PRIMARY};
            text-align: center;
        }}
        .stTextInput > div > label {{
            font-weight: bold;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"<h1 class='title'>📄 Extração de Conta de Energia - Inntag</h1>", unsafe_allow_html=True)

# Upload de PDF
uploaded_file = st.file_uploader("📤 Envie ou arraste aqui sua conta de energia (PDF)", type=["pdf"])

def extract_text_from_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_data(text: str):
    # Nome, endereço, cidade, estado, CEP
    nome_match = re.search(r"([A-Z\s]+)\nR ", text)
    endereco_match = re.search(r"R (.+)\n", text)
    cep_cidade_estado_match = re.search(r"(\d{5}-\d{3}) (.+?) - ([A-Z]{2})", text)

    # Histórico de consumo
    historico = re.findall(r"202\d\s[A-Z]{3}.*?(\d{3,4})\s+\d{2}", text)
    historico_consumo = list(map(int, historico[:12]))
    media_consumo = sum(historico_consumo) / len(historico_consumo) if historico_consumo else 0

    return {
        "nome": nome_match.group(1).strip() if nome_match else "",
        "endereco": f"R {endereco_match.group(1).strip()}" if endereco_match else "",
        "cep": cep_cidade_estado_match.group(1) if cep_cidade_estado_match else "",
        "cidade": cep_cidade_estado_match.group(2) if cep_cidade_estado_match else "",
        "estado": cep_cidade_estado_match.group(3) if cep_cidade_estado_match else "",
        "historico": historico_consumo,
        "media_consumo": round(media_consumo, 2),
    }

if uploaded_file:
    st.success("✅ Arquivo carregado com sucesso!")

    with st.expander("📄 Visualizar arquivo"):
        st.download_button("📥 Baixar PDF", data=uploaded_file.getvalue(), file_name=uploaded_file.name)
        base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500"></iframe>', unsafe_allow_html=True)

    text = extract_text_from_pdf(uploaded_file)
    data = extract_data(text)

    # Formulário de edição
    with st.form("formulario_dados"):
        st.subheader("✏️ Editar ou preencher dados")
        nome = st.text_input("Nome", value=data['nome'])
        endereco = st.text_input("Endereço", value=data['endereco'])
        cep = st.text_input("CEP", value=data['cep'])
        cidade = st.text_input("Cidade", value=data['cidade'])
        estado = st.text_input("Estado", value=data['estado'])
        email = st.text_input("Email")
        telefone = st.text_input("Telefone")

        st.markdown("📊 Consumo (últimos 12 meses)")
        cols = st.columns(4)
        consumos = []
        for i, v in enumerate(data['historico']):
            with cols[i % 4]:
                c = st.number_input(f"Mês {i+1}", min_value=0, value=v)
                consumos.append(c)
        media = round(sum(consumos) / len(consumos), 2)
        st.text(f"Média de consumo: {media} kWh")

        submitted = st.form_submit_button("🚀 Enviar via Webhook")
        if submitted:
            payload = {
                "nome": nome,
                "endereco": endereco,
                "cep": cep,
                "cidade": cidade,
                "estado": estado,
                "email": email,
                "telefone": telefone,
                "consumo_mensal": consumos,
                "media_consumo": media
            }
            response = requests.post("https://hook.us1.make.com/fg9doeumoj2xcb35tjpog3uvwt4oacqd", json=payload)
            if response.status_code == 200:
                st.success("✅ Dados enviados com sucesso!")
            else:
                st.error("❌ Erro ao enviar os dados.")
