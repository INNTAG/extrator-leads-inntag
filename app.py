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
        "arquivo": filename,
        "consumos": []
    }

    with pdfplumber.open(filepath) as pdf:
        if not pdf.pages:
            return jsonify(data)

        page = pdf.pages[0]
        crop = page.within_bbox((0, 320, page.width, 480))  # Área da tarja verde
        text = crop.extract_text() if crop else page.extract_text()

        if text:
            linhas = text.split('\n')
            # Nome é a primeira linha em caixa alta
            if len(linhas) > 0 and linhas[0].isupper():
                data['nome'] = linhas[0].title()

            # Rua e número
            for linha in linhas:
                rua_match = re.search(r'R\s?[A-Z ]+,?\s?(\d+)', linha)
                if rua_match:
                    data['rua'] = linha.split(',')[0].strip().title()
                    data['numero'] = rua_match.group(1)
                    break

            # Cidade e CEP
            for linha in linhas:
                cep_match = re.search(r'(\d{5}-\d{3})\s+([A-Z\- ]+)', linha)
                if cep_match:
                    data['cep'] = cep_match.group(1)
                    data['cidade'] = cep_match.group(2).title()
                    break

            # CPF
            cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)

        # Consumos (kWh): encontrar todos na fatura
        full_text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
        consumo_linhas = re.findall(r'(\d{2,4})\s*kWh', full_text)
        if len(consumo_linhas) >= 12:
            consumos = [int(x) for x in consumo_linhas[-12:]]
            data['consumos'] = consumos
            data['consumo_medio'] = round(sum(consumos) / len(consumos), 2)

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
