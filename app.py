
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
        "consumo_medio": "",
        "arquivo": filename,
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    doc = fitz.open(filepath)
    for page in doc:
        blocks = page.get_text("blocks")

        for b in blocks:
            text = b[4]
            # CPF
            cpf_match = re.search(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', text)
            if cpf_match and not data['cpf']:
                data['cpf'] = cpf_match.group()

            # Nome: linha anterior ao endereço (assume que está antes do 'RUA' ou endereço)
            if "R " in text.upper() or "RUA" in text.upper():
                index = blocks.index(b)
                for above in reversed(blocks[:index]):
                    nome_line = above[4].strip()
                    if nome_line and len(nome_line.split()) >= 2:
                        data['nome'] = nome_line.upper()
                        break

            # Endereço e número
            rua_match = re.search(r'(R\.?\s+[A-ZÇa-zçêáéíóúàèãõâôü0-9\s]+)\s+(\d+)', text)
            if rua_match:
                data['rua'] = rua_match.group(1).strip().title()
                data['numero'] = rua_match.group(2)

            # Cidade e CEP
            cep_match = re.search(r'(\d{5}-\d{3})\s+(\w+)', text)
            if cep_match:
                data['cep'] = cep_match.group(1)
                data['cidade'] = cep_match.group(2).title()

        # Consumo histórico gráfico (últimos 12 valores)
        consumo_vals = re.findall(r'\b(\d{2,4})\s?kWh\b', page.get_text())
        valores_filtrados = [int(val) for val in consumo_vals if 100 <= int(val) <= 9999]
        if len(valores_filtrados) >= 12:
            ultimos = valores_filtrados[-12:]
            data['consumos'] = ultimos
            data['consumo_medio'] = round(sum(ultimos) / len(ultimos), 2)

        break  # Só primeira página

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
