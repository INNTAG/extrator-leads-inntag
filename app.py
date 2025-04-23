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

    with pdfplumber.open(filepath) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())

        # Busca o CPF e captura o nome a partir da linha anterior
        for i, line in enumerate(lines):
            if re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', line):
                cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', line)
                if cpf_match:
                    data['cpf'] = cpf_match.group(1)
                if i > 0:
                    possible_name = lines[i-1].strip()
                    if (
                        re.match(r'^[A-ZÁÉÍÓÚÂÊÎÔÛÇ]{2,}( [A-ZÁÉÍÓÚÂÊÎÔÛÇ]{2,})+$', possible_name)
                        and "NOTA FISCAL" not in possible_name
                    ):
                        data['nome'] = possible_name.upper()
                break

        full_text = "\n".join(lines)

        end_match = re.search(r"(R\.? [^,]+),\s*(\d+)", full_text)
        if end_match:
            data['rua'] = end_match.group(1).strip().title()
            data['numero'] = end_match.group(2)

        loc_match = re.search(r"(\d{5}-\d{3})\s+([^\-\n]+?)\s+-\s+[A-Z]{2}", full_text)
        if loc_match:
            data['cep'] = loc_match.group(1)
            data['cidade'] = loc_match.group(2).strip().title()

        # Extração do histórico de consumo dos últimos 12 meses com base nas barras inferiores
        historico_linhas = [l for l in lines if re.search(r'\d{4}\s+[A-Z]{3}\s+\d+[.,]?\d*\s*kWh', l)]
        valores_consumo = []
        for linha in historico_linhas:
            partes = linha.strip().split()
            for i in range(len(partes)):
                if re.match(r'\d+[.,]?\d*', partes[i]) and i+1 < len(partes) and partes[i+1].lower() == 'kwh':
                    try:
                        val = float(partes[i].replace('.', '').replace(',', '.'))
                        valores_consumo.append(val)
                    except:
                        continue
        valores_consumo = valores_consumo[-12:]
        if valores_consumo:
            data['consumos'] = valores_consumo
            data['consumo_medio'] = round(sum(valores_consumo) / len(valores_consumo), 2)

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
