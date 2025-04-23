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
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            for line in block.get("lines", []):
                line_text = " ".join([span['text'] for span in line['spans']]).strip()
                if re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', line_text):
                    data['cpf'] = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', line_text).group(1)
                    index = blocks.index(block)
                    if index > 0:
                        for l in blocks[index - 1].get("lines", []):
                            nome_line = " ".join([span['text'] for span in l['spans']]).strip()
                            if len(nome_line.split()) >= 2:
                                data['nome'] = nome_line.upper()
                                break
                    break

        full_text = page.get_text()
        loc_match = re.search(r'(\d{5}-\d{3})\s+([^\-\n]+?)\s+-\s+[A-Z]{2}', full_text)
        if loc_match:
            data['cep'] = loc_match.group(1)
            data['cidade'] = loc_match.group(2).strip().title()

        rua_match = re.search(r'(R\.?\s+[^,\n]+)[,\s]+(\d+)', full_text)
        if rua_match:
            data['rua'] = rua_match.group(1).strip().title()
            data['numero'] = rua_match.group(2)

        # Consumo
        consumo_match = re.findall(r'(\d{3,4})\s+kWh', full_text)
        if consumo_match:
            consumos = [float(c) for c in consumo_match[-12:]]
            if consumos:
                data['consumos'] = consumos
                data['consumo_medio'] = round(sum(consumos) / len(consumos), 2)
        break  # primeira página

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