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

        # Captura precisa do CPF e nome baseado em linha anterior
        for i, line in enumerate(lines):
            cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', line)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)
                for j in range(i-1, -1, -1):
                    candidate = lines[j].strip()
                    if candidate and re.match(r'^[A-ZÁÉÍÓÚÂÊÎÔÛÇ]{2,}( [A-ZÁÉÍÓÚÂÊÎÔÛÇ]{2,})+$', candidate):
                        data['nome'] = candidate.upper()
                        break
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

        # Extração do histórico de consumo dos últimos 12 meses
        historico_inicio = False
        historico_valores = []
        for line in lines:
            if re.search(r"HISTÓRICO DE CONSUMO", line, re.IGNORECASE):
                historico_inicio = True
                continue
            if historico_inicio:
                matches = re.findall(r'(\d{1,3}[.,]?\d{0,3})\s*kWh', line, re.IGNORECASE)
                for m in matches:
                    try:
                        historico_valores.append(float(m.replace('.', '').replace(',', '.')))
                    except:
                        pass
        historico_valores = historico_valores[-12:]
        if historico_valores:
            data['consumos'] = historico_valores
            data['consumo_medio'] = round(sum(historico_valores) / len(historico_valores), 2)

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
