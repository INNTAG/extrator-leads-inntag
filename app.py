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
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        linhas = full_text.split('\n')

        for i in range(len(linhas) - 3):
            l1, l2, l3, l4 = linhas[i:i+4]
            if (re.match(r'^[A-Z\s]{5,}$', l1)
                and "," in l2
                and re.search(r'\d{5}-\d{3}', l4)):
                data['nome'] = l1.title().strip()
                data['rua'] = l2.split(',')[0].strip().title()
                numero_match = re.search(r',(\s*\d+)', l2)
                if numero_match:
                    data['numero'] = numero_match.group(1).strip()
                cep_match = re.search(r'(\d{5}-\d{3})', l4)
                cidade_match = re.search(r'\d{5}-\d{3}\s+(.+)', l4)
                if cep_match:
                    data['cep'] = cep_match.group(1)
                if cidade_match:
                    data['cidade'] = cidade_match.group(1).strip().title()
                break

        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        consumo_valores = re.findall(r'(\d{2,4})\s*kWh', full_text)
        if len(consumo_valores) >= 12:
            consumos = [int(x) for x in consumo_valores[-12:]]
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
