from flask import Flask, request, jsonify, render_template, send_file
import pdfplumber
import re
import os
from datetime import datetime
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
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    with pdfplumber.open(filepath) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # Nome: primeira linha em caixa alta
        nome_match = re.search(r"^([A-ZÁÉÍÓÚÂÊÎÔÛÇ ]{4,})$", full_text, re.MULTILINE)
        if nome_match:
            data['nome'] = nome_match.group(1).title()

        # CPF
        cpf_match = re.search(r"CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})", full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Endereço e número
        end_match = re.search(r"(R\.? [^,]+),\s*(\d+)", full_text)
        if end_match:
            data['rua'] = end_match.group(1).title().strip()
            data['numero'] = end_match.group(2)

        # CEP e Cidade: captura linha "13049-346 CAMPINAS - SP"
        loc_match = re.search(r"(\d{5}-\d{3})\s+([^-\n]+)\s+-\s+([A-Z]{2})", full_text)
        if loc_match:
            data['cep'] = loc_match.group(1)
            city = loc_match.group(2).strip()
            data['cidade'] = re.sub(r"\s+", " ", city).title()

        # Consumo últimos 12 meses
        consumo_vals = re.findall(r"(\d{2,4})\s*kWh", full_text)
        if len(consumo_vals) >= 12:
            vals = [int(x) for x in consumo_vals[-12:]]
            data['consumos'] = vals
            data['consumo_medio'] = round(sum(vals)/len(vals), 2)

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return 'Arquivo não encontrado', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
