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
        "arquivo": filename
    }

    with pdfplumber.open(filepath) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        bloco_identificacao = re.search(r'((?:[A-ZÁ-Ú ]{3,})\nCPF[:\s]+\d{3}\.\d{3}\.\d{3}-\d{2})', text)
        if bloco_identificacao:
            nome_match = re.search(r'^([A-ZÁ-Ú ]{3,})', bloco_identificacao.group(1))
            if nome_match:
                data['nome'] = nome_match.group(1).strip().title()

        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        endereco_match = re.search(r'(R\.?|Rua|Av\.?|Avenida)\s+[A-Z0-9 \-]+,\s*(\d+)', text)
        if endereco_match:
            data['rua'] = endereco_match.group(0).split(',')[0].strip()
            data['numero'] = endereco_match.group(2)

        cidade_cep_match = re.search(r'(\d{5}-\d{3})\s+(CAMPINAS.*?)\n', text)
        if cidade_cep_match:
            data['cep'] = cidade_cep_match.group(1)
            cidade_limpa = cidade_cep_match.group(2).split("Pág")[0].strip()
            data['cidade'] = cidade_limpa

        consumo_match = re.findall(r'(\d{3,4})\s+kWh', text)
        if consumo_match:
            consumos = [int(val) for val in consumo_match[-12:]]
            if consumos:
                media = round(sum(consumos) / len(consumos), 2)
                data['consumo_medio'] = media

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
