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

def extract_info_from_pdf(filepath):
    data = {
        "nome": "",
        "cpf": "",
        "cidade": "",
        "cep": "",
        "rua": "",
        "numero": "",
        "consumo_medio": 0,
        "arquivo": os.path.basename(filepath),
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    with fitz.open(filepath) as doc:
        for page in doc:
            text = page.get_text()

            # Extrair CPF
            cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)

            # Extrair bloco "DADOS DA UNIDADE CONSUMIDORA"
            if "DADOS DA UNIDADE CONSUMIDORA" in text:
                lines = text.splitlines()
                idx = [i for i, l in enumerate(lines) if "DADOS DA UNIDADE CONSUMIDORA" in l]
                if idx:
                    start = idx[0] + 1
                    bloco = lines[start:start+4]
                    if len(bloco) >= 4:
                        data['nome'] = bloco[0].strip().title()
                        rua_num = bloco[1].strip().title()
                        bairro = bloco[2].strip().title()
                        cep_cidade_uf = bloco[3].strip()

                        data['rua'] = re.sub(r'[\d].*', '', rua_num).strip()
                        num_match = re.search(r'(\d+)', rua_num)
                        if num_match:
                            data['numero'] = num_match.group(1)

                        cep_match = re.search(r'(\d{5}-\d{3})', cep_cidade_uf)
                        if cep_match:
                            data['cep'] = cep_match.group(1)
                            cidade_uf = cep_cidade_uf.split(cep_match.group(1))[-1].strip()
                            if '-' in cidade_uf:
                                data['cidade'] = cidade_uf.split('-')[0].strip().title()

            # Extrair histórico de consumo (valores numéricos repetidos ao fim do texto)
            matches = re.findall(r'(\d{3,4})\s+kWh', text)
            historico = [int(x) for x in matches if 100 <= int(x) <= 9999]
            if historico:
                data['consumos'] = historico[-12:]  # últimos 12 meses
                data['consumo_medio'] = round(sum(data['consumos']) / len(data['consumos']), 2)

            break  # considera apenas a primeira página com dados principais

    return data

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    extracted_data = extract_info_from_pdf(filepath)
    return jsonify(extracted_data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return 'Arquivo não encontrado', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
