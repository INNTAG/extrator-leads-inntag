from flask import Flask, request, jsonify, send_from_directory
import os
import re
import requests
import pdfplumber
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['WEBHOOK_URL'] = 'https://hook.us1.make.com/fg9doeumoj2xcb35tjpog3uvwt4oacqd'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

class PDFProcessor:
    def __init__(self, filepath):
        self.filepath = filepath

    def extract_data(self):
        text = ""
        with pdfplumber.open(self.filepath) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        nome = ""
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if "DADOS DA UNIDADE CONSUMIDORA" in line.upper():
                for j in range(i+1, len(lines)):
                    possible_name = lines[j].strip()
                    if possible_name:
                        nome = possible_name
                        break
                break

        endereco_match = re.search(r"(R(?:ua)?|AV(?:enida)?)[^\n]+", text)
        endereco = endereco_match.group(0).strip() if endereco_match else ""
        rua = endereco
        numero = ""
        if "," in endereco:
            rua, numero = [x.strip() for x in endereco.split(",", 1)]

        cep_cidade_estado_match = re.search(r"(\d{5}-\d{3})\s+([A-Za-z\s]+)\s*-\s*([A-Z]{2})", text)
        cep = cep_cidade_estado_match.group(1) if cep_cidade_estado_match else ""
        cidade = cep_cidade_estado_match.group(2).strip() if cep_cidade_estado_match else ""
        estado = cep_cidade_estado_match.group(3) if cep_cidade_estado_match else ""

        cpf_match = re.search(r"CPF:\s*(\d{3}\.\d{3}\.\d{3}-\d{2})", text)
        cpf = cpf_match.group(1) if cpf_match else ""

        historico_raw = re.findall(r"(\d{3,4})\s+\d{2}", text)
        historico_consumo = list(map(int, historico_raw[:12]))
        while len(historico_consumo) < 12:
            historico_consumo.insert(0, 0)
        media_consumo = round(sum(historico_consumo) / 12, 2)

        return {
            "nome": nome,
            "cpf": cpf,
            "cep": cep,
            "cidade": cidade,
            "estado": estado,
            "rua": rua,
            "numero": numero,
            "historico": historico_consumo,
            "media_consumo": media_consumo
        }

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Arquivo inválido'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        processor = PDFProcessor(filepath)
        data = processor.extract_data()
        return jsonify({
            "nome": data.get("nome", ""),
            "cpf": data.get("cpf", ""),
            "cidade": data.get("cidade", ""),
            "cep": data.get("cep", ""),
            "rua": data.get("rua", ""),
            "numero": data.get("numero", ""),
            "consumo_medio": data.get("media_consumo", 0),
            "consumos": data.get("historico", [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send-webhook', methods=['POST'])
def send_webhook():
    try:
        response = requests.post(app.config['WEBHOOK_URL'], json=request.json)
        if response.status_code == 200:
            return jsonify({'success': True})
        return jsonify({'success': False, 'status': response.status_code}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
