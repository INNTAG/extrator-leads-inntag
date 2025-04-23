
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

    with fitz.open(filepath) as doc:
        for page in doc:
            text = page.get_text()

            cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)

            blocks = page.get_text("dict")['blocks']
            cpf_block = None
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if data['cpf'] in span['text']:
                            cpf_block = span
                            break
            if cpf_block:
                y_cpf = cpf_block['bbox'][1]
                nome_candidato = ""
                for block in blocks:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if y_cpf - 100 < span['bbox'][1] < y_cpf - 5:
                                nome_candidato += span['text'] + " "
                nome = " ".join(nome_candidato.strip().split())
                if len(nome.split()) >= 2:
                    data['nome'] = nome.upper()

            endereco_match = re.search(r'(R\.\s?[^,\n]+),\s*(\d+)', text)
            if endereco_match:
                data['rua'] = endereco_match.group(1).strip()
                data['numero'] = endereco_match.group(2).strip()

            loc_match = re.search(r'(\d{5}-\d{3})\s+([A-Z\s]+)', text)
            if loc_match:
                data['cep'] = loc_match.group(1)
                data['cidade'] = loc_match.group(2).title()

            blocks_baixos = [b for b in blocks if b['bbox'][1] > page.rect.height - 300]
            consumos = []
            for block in blocks_baixos:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        nums = re.findall(r'\b\d{3,4}\b', span['text'])
                        for n in nums:
                            val = int(n)
                            if 100 <= val <= 9999:
                                consumos.append(val)
            if len(consumos) >= 6:
                ultimos = consumos[-12:]
                data['consumos'] = ultimos
                data['consumo_medio'] = round(sum(ultimos) / len(ultimos), 2)
            break

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
