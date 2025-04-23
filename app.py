from flask import Flask, request, jsonify, render_template, send_file
import pdfplumber
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
    # Recebe e salva o arquivo
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

    # Abre e extrai texto do PDF
    with pdfplumber.open(filepath) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        # Nome: primeira linha em caixa alta com 2+ palavras (regex corrigido)
        nome_match = re.search(r"^([A-ZÁÉÍÓÚÂÊÎÔÛÇ]+(?: [A-ZÁÉÍÓÚÂÊÎÔÛÇ]+)+)", full_text, re.MULTILINE)
        if nome_match:
            data['nome'] = nome_match.group(1).strip().upper()

        # CPF
        cpf_match = re.search(r"CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})", full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Endereço e número
        end_match = re.search(r"(R\.? [^,]+),\s*(\d+)", full_text)
        if end_match:
            data['rua'] = end_match.group(1).strip().title()
            data['numero'] = end_match.group(2)

        # CEP e cidade
        loc_match = re.search(r"(\d{5}-\d{3})\s+([^\-\n]+?)\s+-\s+[A-Z]{2}", full_text)
        if loc_match:
            data['cep'] = loc_match.group(1)
            data['cidade'] = loc_match.group(2).strip().title()

        # Consumo: últimos 12 valores de kWh (captura com vírgula ou ponto)
        consumo_vals = re.findall(r"(\d+(?:[.,]\d+)?)\s*kWh", full_text, re.IGNORECASE)
        if consumo_vals:
            ultimos = consumo_vals[-12:]
            numericos = []
            for val in ultimos:
                num = val.replace('.', '').replace(',', '.')
                try:
                    numericos.append(float(num))
                except:
                    pass
            if numericos:
                data['consumos'] = numericos
                data['consumo_medio'] = round(sum(numericos) / len(numericos), 2)

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
