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
        log = ["Iniciando extração PDF..."]
        text = ""
        try:
            with pdfplumber.open(self.filepath) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            log.append("PDF lido com sucesso.")
        except Exception as e:
            log.append(f"Erro ao ler o PDF: {e}")
            return {"log": log}

        lines = text.splitlines()
        cpf = nome = endereco = cidade = estado = cep = rua = numero = ""
        historico_consumo = []
        media_consumo = 0
        start_idx = 0

        # CPF e Nome
        for i, line in enumerate(lines):
            match = re.search(r"(.*?)CPF:\s*(\d{3}\.\d{3}\.\d{3}-\d{2})", line)
            if match:
                nome = match.group(1).strip()
                cpf = match.group(2)
                log.append(f"CPF encontrado: {cpf}")
                log.append(f"Nome detectado: {nome}")
                start_idx = i
                break
        else:
            log.append("CPF não encontrado. Extração abortada.")
            return {"log": log}

        # Endereço
        if start_idx + 1 < len(lines):
            endereco = lines[start_idx + 1].strip()
            log.append(f"Endereço identificado: {endereco}")
        else:
            log.append("Endereço não encontrado após o CPF.")

        match = re.search(r"(.+?)\s+(\d+.*)", endereco)
        if match:
            rua = match.group(1).strip()
            numero = match.group(2).strip()
            log.append(f"Rua extraída: {rua}")
            log.append(f"Número extraído: {numero}")
        else:
            rua = endereco
            log.append("Não foi possível separar rua e número com regex.")

        # Cidade, Estado, CEP
        if start_idx + 2 < len(lines):
            cidade_line = lines[start_idx + 2].strip()
            cep_match = re.search(r"(\d{5}-\d{3})\s+([A-Z\s]+)\s+([A-Z]{2})", cidade_line)
            if cep_match:
                cep = cep_match.group(1)
                cidade = cep_match.group(2).strip()
                estado = cep_match.group(3).strip()
                log.append(f"CEP: {cep} | Cidade: {cidade} | Estado: {estado}")
            else:
                log.append(f"Não foi possível extrair CEP/Cidade/Estado da linha: '{cidade_line}'")
        else:
            log.append("Linha de CEP/Cidade/Estado ausente.")

        # Histórico de consumo
        try:
            historico_raw = re.findall(r"(\d{3,4})\s+\d{2}", "\n".join(lines[start_idx:]))
            historico_consumo = list(map(int, historico_raw[:12]))
            while len(historico_consumo) < 12:
                historico_consumo.insert(0, 0)
            media_consumo = round(sum(historico_consumo) / 12, 2)
            log.append(f"Histórico: {historico_consumo}")
            log.append(f"Média de consumo: {media_consumo}")
        except Exception as e:
            log.append(f"Erro ao calcular histórico de consumo: {e}")

        return {
            "nome": nome, "cpf": cpf, "cep": cep, "cidade": cidade,
            "estado": estado, "rua": rua, "numero": numero,
            "historico": historico_consumo, "media_consumo": media_consumo,
            "log": log
        }

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Arquivo inválido'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(filepath)

    processor = PDFProcessor(filepath)
    data = processor.extract_data()
    return jsonify(data)

@app.route('/send-webhook', methods=['POST'])
def send_webhook():
    try:
        response = requests.post(app.config['WEBHOOK_URL'], json=request.json)
        return jsonify({'success': response.status_code == 200})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
