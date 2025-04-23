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

    data = {"nome": "", "cpf": "", "cidade": "", "cep": "", "rua": "", "numero": "", "consumo_medio": "", "arquivo": filename, "consumos": [], "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M:%S')}    
    with pdfplumber.open(filepath) as pdf:
        # Tentar extrair bloco dos Dados da Unidade Consumidora pela posição no PDF
        page = pdf.pages[0]
        words = page.extract_words()
        y_header = None
        for w in words:
            if w['text'].upper() == 'CONSUMIDORA':
                y_header = w['top']
                break
        if y_header:
            # recortar área logo abaixo do cabeçalho
            h = page.height
            bbox = (0, y_header, page.width, y_header + 200)
            block = page.within_bbox(bbox).extract_text() or ''
            lines = [ln.strip() for ln in block.split('\n') if ln.strip()]
            # espera: ['DADOS DA UNIDADE CONSUMIDORA', 'LUIS PAULO...', 'R ...', 'RES ...', '13049-346 CAMPINAS - SP']
            # validando pelo comprimento
            if len(lines) >= 5 and 'DADOS DA UNIDADE CONSUMIDORA' in lines[0].upper():
                nome_line = lines[1]
                end_line  = lines[2]
                # bairro_line = lines[3]
                cidade_line = lines[4]
                data['nome'] = nome_line.title()
                # endereço e número
                parts = end_line.split(',')
                data['rua'] = parts[0].title().strip()
                num_match = re.search(r'(\d+)', end_line)
                if num_match:
                    data['numero'] = num_match.group(1)
                # CEP e cidade
                cep_match = re.search(r'(\d{5}-\d{3})', cidade_line)
                city_match = re.search(r'\d{5}-\d{3}\s+(.+)', cidade_line)
                if cep_match:
                    data['cep'] = cep_match.group(1)
                if city_match:
                    data['cidade'] = city_match.group(1).title()
        # CPF via regex
        full_text = "\n".join([p.extract_text() or '' for p in pdf.pages])
        cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
        if cpf_match:
            data['cpf'] = cpf_match.group(1)
        # Consumo dos últimos 12 meses
        vals = re.findall(r'(\d{2,4})\s*kWh', full_text)
        if len(vals) >= 12:
            consumos = [int(x) for x in vals[-12:]]
            data['consumos'] = consumos
            data['consumo_medio'] = round(sum(consumos)/len(consumos), 2)
    return jsonify(data)

@app.route('/pdf/<filename>')
def get_pdf(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        return send_file(path)
    return 'Arquivo não encontrado', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
