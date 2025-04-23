
from flask import Flask, request, render_template
import fitz  # PyMuPDF
import re
import io
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def upload():
    full_text = ""
    consumo_data = {}

    if request.method == "POST":
        file = request.files["pdf"]
        if file.filename.endswith(".pdf"):
            pdf_bytes = file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page in doc:
                full_text += page.get_text()

            # Simples log
            print("Texto extraído com sucesso.")

    return render_template("index.html", full_text=full_text)

if __name__ == "__main__":
    app.run(debug=True)
