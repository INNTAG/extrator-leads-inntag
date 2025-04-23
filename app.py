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
        "consumos": [],
        "consumo_medio": "",
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        "arquivo": filename
    }

    with pdfplumber.open(filepath) as pdf:
        # Captura do nome: primeira linha não vazia da primeira página
        first_page = pdf.pages[0]
        lines0 = first_page.extract_text().splitlines()
        for l in lines0:
            if l.strip():
                data['nome'] = l.strip().upper()
                break

        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        # CPF
        m = re.search(r"CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})", full_text)
        if m: data['cpf'] = m.group(1)

        # Endereço e número
        m = re.search(r"(R\.? [^,]+),\s*(\d+)", full_text)
        if m:
            data['rua'] = m.group(1).title()
            data['numero'] = m.group(2)

        # CEP e cidade (até antes de ' - SP' ou similar)
        m = re.search(r"(\d{5}-\d{3})\s+(.+?)\s+-\s+[A-Z]{2}", full_text)
        if m:
            data['cep'] = m.group(1)
            data['cidade'] = m.group(2).strip().title()

        # Extrair histórico dos últimos 12 meses
        hist = []
        for line in full_text.splitlines():
            parts = line.strip().split()
            if len(parts) >= 4 and re.match(r"^\d{4}", parts[0]):
                mes = parts[1]
                raw = parts[2].replace('.', '').replace(',', '.')
                try:
                    val = float(raw)
                    hist.append((mes, val))
                except:
                    pass
        hist = hist[:12]
        if hist:
            data['consumos'] = [v for (_, v) in hist]
            data['consumo_medio'] = round(sum(v for (_, v) in hist)/len(hist), 2)

    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(path) if os.path.exists(path) else ('Arquivo não encontrado', 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
