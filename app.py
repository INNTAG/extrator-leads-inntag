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
            text = page.get_text("text")

            # CPF
            cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)

            # Nome (linha acima do endereço, ignorando palavras genéricas)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if re.search(r'\d{5}-\d{3}', line):
                    for j in range(i - 4, i):
                        candidate = lines[j].strip()
                        if len(candidate.split()) >= 2 and not any(word in candidate.upper() for word in ["PREZADO", "MANTENHA", "ATUALIZADOS"]):
                            data['nome'] = candidate.upper()
                            break
                    break

            # Endereço completo com número
            end_match = re.search(r'(R\.?\s?[A-Z][^,\n]+)[,\s]+(\d+)', text)
            if end_match:
                data['rua'] = end_match.group(1).strip().title()
                data['numero'] = end_match.group(2)

            # Cidade e CEP
            loc_match = re.search(r'(\d{5}-\d{3})\s+([A-ZÀ-Úa-zà-ú\s]+)', text)
            if loc_match:
                data['cep'] = loc_match.group(1)
                data['cidade'] = loc_match.group(2).strip().title()

            # Consumo histórico (aprimorado)
            historico_matches = re.findall(r'(\d{3,4})\s*kWh', text, re.IGNORECASE)
            consumos = [int(x) for x in historico_matches if 100 <= int(x) <= 9999]
            if len(consumos) >= 2:
                data['consumos'] = consumos[-12:]  # últimos 12
                data['consumo_medio'] = round(sum(data['consumos']) / len(data['consumos']), 2)
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