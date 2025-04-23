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
        "consumo_medio": 0,
        "arquivo": filename,
        "consumos": [],
        "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    }

    doc = fitz.open(filepath)
    page = doc[0]
    words = page.get_text("words")  # list of [x0, y0, x1, y1, word, block_no, line_no, word_no]
    words_sorted = sorted(words, key=lambda w: (w[1], w[0]))

    full_text = "\n".join([w[4] for w in words_sorted])

    for i, w in enumerate(words_sorted):
        if re.match(r'\d{3}\.\d{3}\.\d{3}-\d{2}', w[4]):
            data['cpf'] = w[4]
            y_cpf = w[1]
            nome_line = [t[4] for t in words_sorted if y_cpf - 70 < t[1] < y_cpf - 10]
            nome = " ".join(nome_line).strip()
            nome = re.sub(r'[^A-Z\s]', '', nome.upper())
            data['nome'] = nome
            break

    cep_cidade = re.search(r'(\d{5}-\d{3})\s+([A-ZÁÉÍÓÚÃÕÇ\s]+)', full_text)
    if cep_cidade:
        data['cep'] = cep_cidade.group(1)
        data['cidade'] = cep_cidade.group(2).strip().title()

    endereco_match = re.search(r'(R\.?\s[^,\n]+)[,\s]+(\d+)', full_text)
    if endereco_match:
        data['rua'] = endereco_match.group(1).strip().title()
        data['numero'] = endereco_match.group(2)

    # Extração do histórico de consumo por área inferior da página
    consumo_vals = []
    for page in doc:
        text = page.get_text("text")
        historico = re.findall(r'(\d{3,4})\s*kWh', text, re.IGNORECASE)
        consumo_vals.extend([float(c.replace(',', '.')) for c in historico])

    if consumo_vals:
        ultimos = consumo_vals[-12:]
        data['consumos'] = ultimos
        data['consumo_medio'] = round(sum(ultimos) / len(ultimos), 2)

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
