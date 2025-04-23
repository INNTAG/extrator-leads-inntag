from flask import Flask, request, jsonify, render_template
import fitz  # PyMuPDF
import re
import os
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
        "consumo_medio": 0,
        "consumos": [],
        "arquivo": filename,
    }

    with fitz.open(filepath) as doc:
        for page in doc:
            text = page.get_text()

            # CPF
            cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text)
            if cpf_match:
                data["cpf"] = cpf_match.group(0)

            # Bloco de dados da unidade consumidora
            if "DADOS DA UNIDADE CONSUMIDORA" in text:
                bloco = text.split("DADOS DA UNIDADE CONSUMIDORA")[1]
                linhas = bloco.strip().split("\n")[:4]

                if len(linhas) >= 4:
                    data["nome"] = linhas[0].strip()
                    rua_linha = linhas[1]
                    data["rua"] = rua_linha.split(",")[0].strip().title()

                    numero_match = re.search(r',\s*(\d+)', rua_linha)
                    if numero_match:
                        data["numero"] = numero_match.group(1)

                    cidade_linha = linhas[3]
                    cep_match = re.search(r'\d{5}-\d{3}', cidade_linha)
                    if cep_match:
                        data["cep"] = cep_match.group(0)
                        cidade_estado = cidade_linha.split(cep_match.group(0))[-1].strip()
                        if " - " in cidade_estado:
                            cidade = cidade_estado.split(" - ")[0].strip()
                            data["cidade"] = cidade.title()

            # Histórico de consumo (últimos 12 meses com valores reais)
            consumo_matches = re.findall(r'(\d{2,4})\s+kWh', text)
            consumos = [int(v) for v in consumo_matches if 100 <= int(v) <= 9999]
            if len(consumos) >= 2:
                consumos = consumos[-12:]
                data["consumos"] = consumos
                data["consumo_medio"] = round(sum(consumos) / len(consumos), 2)

            break  # processa apenas a primeira página

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
