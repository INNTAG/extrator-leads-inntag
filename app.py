from flask import Flask, request, jsonify, render_template, send_file
import pdfplumber
import re
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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
        "consumos": [],
        "arquivo": filename,
        "atualizado_em": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    with pdfplumber.open(filepath) as pdf:
        full_text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        # Nome (LINHA ESPECÍFICA QUE NÃO CONTENHA "NOTA FISCAL")
        nome_match = re.search(r"(?m)^([A-Z\s]+)
R ", full_text)
        if nome_match and "NOTA FISCAL" not in nome_match.group(1):
            data['nome'] = nome_match.group(1).strip().upper()

        # CPF
        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Rua e Número
        rua_match = re.search(r"(?m)^R\s?([A-Z\s]+),\s?(\d+)", full_text)
        if rua_match:
            data['rua'] = "R " + rua_match.group(1).strip().title()
            data['numero'] = rua_match.group(2)

        # Cidade e CEP
        cidade_match = re.search(r"(?m)(\d{5}-\d{3})\s+([A-Z\s]+)\s+-\s+[A-Z]{2}", full_text)
        if cidade_match:
            data['cep'] = cidade_match.group(1)
            data['cidade'] = cidade_match.group(2).title()

        # Consumos dos últimos 12 meses (valores numéricos seguidos de "kWh")
        consumo_matches = re.findall(r'(\d{2,6})\s*kWh', full_text)
        consumos = list(map(int, consumo_matches[-12:])) if len(consumo_matches) >= 2 else []
        data['consumos'] = consumos
        if consumos:
            data['consumo_medio'] = round(sum(consumos) / len(consumos), 2)

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
