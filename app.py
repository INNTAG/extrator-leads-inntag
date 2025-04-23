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
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        linhas = full_text.split('\n')

        # Nome (primeira linha com tudo em maiúsculo e mais de 3 palavras)
        for i, linha in enumerate(linhas):
            if linha.isupper() and len(linha.split()) >= 2:
                data['nome'] = linha.title()
                # Endereço: assume próxima linha
                if i + 1 < len(linhas):
                    endereco = linhas[i + 1].strip().title()
                    num_match = re.search(r'(\d+)', endereco)
                    if num_match:
                        data['rua'] = endereco.split(',')[0].strip()
                        data['numero'] = num_match.group(1)
                # Cidade e CEP: assume linha seguinte
                if i + 2 < len(linhas):
                    cidade_cep_match = re.search(r'(\d{5}-\d{3})\s+(.+)', linhas[i + 2])
                    if cidade_cep_match:
                        data['cep'] = cidade_cep_match.group(1)
                        data['cidade'] = cidade_cep_match.group(2).title()
                break

        # CPF
        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)

        # Consumo: buscar 12 valores em kWh da seção de histórico
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
