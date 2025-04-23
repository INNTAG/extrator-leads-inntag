from flask import Flask, request, jsonify, render_template, send_file
import fitz  # PyMuPDF
import os
import re
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
        "consumo_medio": 0,
        "arquivo": filename,
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    doc = fitz.open(filepath)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # Nome
    nome_match = re.search(r'(LU[IÍ]Z\s+[A-Z\s]+CAMARGO)', full_text)
    if nome_match:
        data['nome'] = nome_match.group(1).strip()

    # CPF
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', full_text)
    if cpf_match:
        data['cpf'] = cpf_match.group(0)

    # Cidade e CEP
    loc_match = re.search(r'(\d{5}-\d{3})\s+([A-Z\s]{3,})', full_text)
    if loc_match:
        data['cep'] = loc_match.group(1)
        data['cidade'] = loc_match.group(2).strip().title()

    # Endereço e número
    rua_match = re.search(r'(R\s+[A-Za-zÀ-ÿ\s]+)\s+(\d{1,4})', full_text)
    if rua_match:
        data['rua'] = rua_match.group(1).strip()
        data['numero'] = rua_match.group(2).strip()

    # Consumo histórico (12 valores)
    historico_match = re.findall(r'\b(\d{3,4})\b\s+(?:\d{1,2})', full_text)
    consumos = [int(v) for v in historico_match if 100 < int(v) < 9999]
    if len(consumos) >= 12:
        data['consumos'] = consumos[-12:]
        data['consumo_medio'] = round(sum(data['consumos']) / 12, 2)

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return 'Arquivo não encontrado', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)