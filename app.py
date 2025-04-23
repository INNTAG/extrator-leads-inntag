
from flask import Flask, request, jsonify, render_template, send_file
import fitz  # PyMuPDF
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
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
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    # (Exemplos de extração — pode ser ajustado conforme layout real)
    import re
    nome_match = re.search(r"(LUIZ PAULO CAMARGO.*?)\n", full_text)
    if nome_match:
        data["nome"] = nome_match.group(1).strip()

    cpf_match = re.search(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", full_text)
    if cpf_match:
        data["cpf"] = cpf_match.group(1).strip()

    cep_match = re.search(r"(\d{5}-\d{3})", full_text)
    if cep_match:
        data["cep"] = cep_match.group(1).strip()

    cidade_match = re.search(r"\d{5}-\d{3}\s+([A-Z\s]+)", full_text)
    if cidade_match:
        data["cidade"] = cidade_match.group(1).strip().title()

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return 'Arquivo não encontrado', 404

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
