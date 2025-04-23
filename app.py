from flask import Flask, request, jsonify, render_template, send_file
import fitz  # PyMuPDF
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
        "consumo_medio": 0,
        "arquivo": filename,
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    with fitz.open(filepath) as pdf:
        text = "\n".join([page.get_text() for page in pdf])

        # Nome: linha acima de RES ZURICH ou acima do endereço
        match_nome = re.search(r"(?<=\n)([A-Z\s]+)(?=\nR\s+BERNARDO|\nRES ZURICH)", text)
        if match_nome:
            data['nome'] = match_nome.group(1).strip()

        # CPF
        match_cpf = re.search(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", text)
        if match_cpf:
            data['cpf'] = match_cpf.group(1)

        # Rua e número
        match_end = re.search(r"(R\.?\s[^\n,]+)\s+(\d+)[^\n]*", text)
        if match_end:
            data['rua'] = match_end.group(1).strip()
            data['numero'] = match_end.group(2)

        # CEP e cidade
        match_cep = re.search(r"(\d{5}-\d{3})\s+(.*?)\s+-\s+[A-Z]{2}", text)
        if match_cep:
            data['cep'] = match_cep.group(1)
            data['cidade'] = match_cep.group(2).strip()

        # Consumos: capturar a tabela final com meses e kWh
        historico = re.findall(r"(\d{3,4})\s+\d{2,3}", text)
        consumos = [int(kwh) for kwh in historico if 100 <= int(kwh) <= 9999]
        if len(consumos) >= 12:
            consumos = consumos[-12:]
            data['consumos'] = consumos
            data['consumo_medio'] = round(sum(consumos)/len(consumos), 2)

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
