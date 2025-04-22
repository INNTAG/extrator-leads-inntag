from flask import Flask, request, jsonify, render_template
import pdfplumber
import re

app = Flask(__name__)

@app.route('/')
def form():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    data = {
        "nome": "",
        "cpf": "",
        "cidade": "",
        "cep": "",
        "rua": "",
        "numero": "",
        "consumo_medio": ""
    }

    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', text)
        consumo_match = re.findall(r'(\d{3,4})\s+kWh', text)
        endereco_match = re.search(r'(R\. .+?),\s*(\d+)', text)
        cidade_match = re.search(r'(\d{5}-\d{3})\s+(.+?)(?:\n|$)', text)

        if cpf_match:
            data['cpf'] = cpf_match.group(1)
        if consumo_match:
            consumo_list = [int(i) for i in consumo_match[-12:]]
            data['consumo_medio'] = round(sum(consumo_list) / len(consumo_list), 2)
        if endereco_match:
            data['rua'] = endereco_match.group(1)
            data['numero'] = endereco_match.group(2)
        if cidade_match:
            data['cep'] = cidade_match.group(1)
            data['cidade'] = cidade_match.group(2)

    return jsonify(data)

if __name__ == '__main__':
   import os
port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
