import fitz  # PyMuPDF
from flask import Flask, request, jsonify, render_template
import re
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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

    with fitz.open(filepath) as pdf:
        for page in pdf:
            text = page.get_text("text")

            # CPF
            cpf_match = re.search(r'(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
            if cpf_match:
                data['cpf'] = cpf_match.group(1)

            # Extrai bloco "DADOS DA UNIDADE CONSUMIDORA"
            if "DADOS DA UNIDADE CONSUMIDORA" in text:
                lines = text.splitlines()
                start_index = None
                for i, line in enumerate(lines):
                    if "DADOS DA UNIDADE CONSUMIDORA" in line:
                        start_index = i + 1
                        break
                if start_index:
                    bloco = lines[start_index:start_index+4]
                    if len(bloco) >= 4:
                        data['nome'] = bloco[0].strip()
                        data['rua'] = bloco[1].strip()
                        bairro_linha = bloco[2].strip()
                        cidade_cep_uf = bloco[3].strip()

                        # Número (últimos dígitos na linha da rua)
                        numero_match = re.search(r'(\d+)', data['rua'])
                        if numero_match:
                            data['numero'] = numero_match.group(1)

                        # Cidade, CEP e UF
                        cep_cidade_match = re.search(r'(\d{5}-\d{3})\s+(.*?)\s*-\s*([A-Z]{2})', cidade_cep_uf)
                        if cep_cidade_match:
                            data['cep'] = cep_cidade_match.group(1)
                            data['cidade'] = cep_cidade_match.group(2).strip()

            # Consumos (gráfico inferior)
            blocos = page.search_for("HISTÓRICO DE CONSUMO")
            if blocos:
                bbox = fitz.Rect(0, blocos[0].y1 + 5, page.rect.width, page.rect.height)
                historico = page.get_text("text", clip=bbox)
                matches = re.findall(r'(\d{2,4})\s*$', historico, re.MULTILINE)
                valores = [int(v) for v in matches if 100 <= int(v) <= 9999]
                if len(valores) >= 6:
                    data['consumos'] = valores[-12:]
                    data['consumo_medio'] = round(sum(data['consumos']) / len(data['consumos']), 2)
            break

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
