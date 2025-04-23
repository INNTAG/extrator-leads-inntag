from flask import Flask, request, jsonify, render_template, send_file
import pdfplumber
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    data = {
        "nome": "",
        "cpf": "",
        "cidade": "",
        "cep": "",
        "rua": "",
        "numero": "",
        "consumo_medio": "",
        "arquivo": filename,
        "consumos": []
    }

    with pdfplumber.open(filepath) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        # Nome do titular
        nome_match = re.search(r'\n([A-ZÁ-Ú ]{3,})\nCPF[:\s]+\d{3}\.\d{3}\.\d{3}-\d{2}', text)
        if nome_match:
            data['nome'] = nome_match.group(1).title().strip()

        # CPF
        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Endereço
        endereco_match = re.search(r'(R\.?|Rua|Av\.?|Avenida)\s+[A-Z0-9 \-]+,\s*(\d+)', text)
        if endereco_match:
            data['rua'] = endereco_match.group(0).split(',')[0].strip()
            data['numero'] = endereco_match.group(2)

        # Cidade e CEP
        cidade_cep_match = re.search(r'(\d{5}-\d{3})\s+(CAMPINAS.*?)\n', text)
        if cidade_cep_match:
            data['cep'] = cidade_cep_match.group(1)
            cidade_limpa = cidade_cep_match.group(2).split("Pág")[0].strip()
            data['cidade'] = cidade_limpa

        # Consumo dos últimos 12 meses (com mês nomeado + valor kWh)
        consumo_match = re.findall(r'(?:JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)[^\d]*(\d{2,4})\s*kWh', text)
        if len(consumo_match) >= 12:
            consumos = [int(c) for c in consumo_match[-12:]]
            data['consumos'] = consumos
            data['consumo_medio'] = round(sum(consumos) / len(consumos), 2)

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "Arquivo não encontrado", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
