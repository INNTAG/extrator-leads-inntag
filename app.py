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
        text_pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
        full_text = "\n".join(text_pages)
        
        # Nome: primeira linha em caixa alta da primeira página
        if text_pages:
            first_page_lines = text_pages[0].split("\n")
            for line in first_page_lines:
                if line.isupper() and len(line.strip()) > 5 and not any(word in line for word in ["CPFL", "NOTA FISCAL", "ENERGIA"]):
                    data['nome'] = line.strip().title()
                    break

        # CPF
        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Endereço
        endereco_match = re.search(r'(R\.?|Rua|Av\.?|Avenida)\s+[A-Z0-9 \-]+,?\s*(\d+)', full_text)
        if endereco_match:
            data['rua'] = endereco_match.group(0).split(',')[0].strip()
            data['numero'] = endereco_match.group(2)

        # Cidade e CEP
        cidade_cep_match = re.search(r'(\d{5}-\d{3})\s+(CAMPINAS.*?)\n', full_text)
        if cidade_cep_match:
            data['cep'] = cidade_cep_match.group(1)
            cidade_limpa = cidade_cep_match.group(2).split("Pág")[0].strip()
            data['cidade'] = cidade_limpa

        # Consumos (captura linhas com vários números + kWh)
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
