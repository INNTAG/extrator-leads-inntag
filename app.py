data = {
    "nome": "",
    "cpf": "",
    "cidade": "",
    "cep": "",
    "rua": "",
    "numero": "",
    "consumo_medio": "",
    "consumos": [],
    "arquivo": filename,
    "atualizado_em": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
}

with pdfplumber.open(filepath) as pdf:
    full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    nome_match = re.search(r"(?m)^([A-Z\s]+)\nR ", full_text)
    if nome_match and "NOTA FISCAL" not in nome_match.group(1):
        data['nome'] = nome_match.group(1).strip().upper()

    cpf_match = re.search(r'CPF[:\s]+(\d{3}\.\d{3}\.\d{3}-\d{2})', full_text)
    if cpf_match:
        data['cpf'] = cpf_match.group(1)

    rua_match = re.search(r"(?m)^R\.? ([^,\n]+),\s?(\d+)", full_text)
    if rua_match:
        data['rua'] = "R. " + rua_match.group(1).strip().title()
        data['numero'] = rua_match.group(2)

    cidade_match = re.search(r"(?m)(\d{5}-\d{3})\s+([A-Z\s]+?)\s+-\s+[A-Z]{2}", full_text)
    if cidade_match:
        data['cep'] = cidade_match.group(1)
        data['cidade'] = cidade_match.group(2).title()

    # Correção: buscar linhas com ano e mês explícitos (histórico de consumo)
    historico = []
    for line in full_text.splitlines():
        if re.match(r'^\d{4}\s+[A-Z]{3}\s+\d+[.,]?\d*\s+kWh', line):
            partes = line.split()
            if len(partes) >= 3:
                try:
                    consumo_val = float(partes[2].replace('.', '').replace(',', '.'))
                    historico.append((partes[1], consumo_val))
                except:
                    continue
    # Pegar os últimos 12 valores
    historico = historico[-12:]
    data['consumos'] = [v for _, v in historico]
    if historico:
        data['consumo_medio'] = round(sum(v for _, v in historico) / len(historico), 2)

return jsonify(data)