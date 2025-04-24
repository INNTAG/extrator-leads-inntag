from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import requests
from werkzeug.utils import secure_filename
from pdf_processor import PDFProcessor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['WEBHOOK_URL'] = 'https://hook.us1.make.com/fg9doeumoj2xcb35tjpog3uvwt4oacqd'

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/extract', methods=['POST'])
def extract_data():
    # Verificar se o arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    
    # Verificar se o nome do arquivo está vazio
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Verificar se o arquivo é um PDF
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato de arquivo não permitido. Apenas PDFs são aceitos.'}), 400
    
    # Salvar o arquivo
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Processar o PDF
    try:
        processor = PDFProcessor(filepath)
        data = processor.extract_data()
        
        # Adicionar o caminho do arquivo para referência
        result = {
            'success': True,
            'data': data,
            'filename': filename,
            'filepath': filepath
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'filename': filename
        }), 500

@app.route('/send-webhook', methods=['POST'])
def send_webhook():
    data = request.json
    
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    try:
        # Enviar dados para o webhook
        response = requests.post(
            app.config['WEBHOOK_URL'],
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Dados enviados com sucesso para o webhook'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Erro ao enviar dados: {response.status_code} - {response.text}'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao enviar dados: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
