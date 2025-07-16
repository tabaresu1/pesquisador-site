from flask import Flask, render_template, request, send_file, Response, session, jsonify
import json
import pdfplumber
import re
import os
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'dcd8df3c4cb2cbc80c742263ad63e548cc9e2477e7229c8d'
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "resultados"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Configurações
MAX_RETRIES = 2
REQUEST_TIMEOUT = 60000
DELAY_BETWEEN_REQUESTS = 3
BATCH_SIZE = 10
DELAY_AFTER_BATCH = 15

def extrair_codigos_ean(caminho_pdf):
    codigos = set()
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                texto = pagina.extract_text()
                if texto:
                    encontrados = re.findall(r"\b\d{8,14}\b", texto)
                    codigos.update(encontrados)
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
    return list(codigos)

def buscar_produto(ean):
    print(f"\n🔍 Buscando EAN: {ean}")
    url_busca = f"https://www.drogariasaopaulo.com.br/pesquisa?q={ean}"

    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=True)
            context = navegador.new_context()
            page = context.new_page()

            page.goto(url_busca, timeout=60000)
            print(f"🌐 Página acessada: {page.url}")

            if page.locator("h1.h2").count():
                h1_text = page.locator("h1.h2").first.inner_text()
                if "Nenhum Resultado Encontrado!" in h1_text:
                    print("❌ Nenhum resultado encontrado.")
                    return {"EAN": ean, "Produto": "", "Preço": "", "Promoção": "", "Link": "", "Status": "Não encontrado"}

            if page.locator("a.collection-link[href*='/p']").count() > 0:
                print("🧭 Resultados de busca encontrados, clicando no primeiro...")
                page.locator("a.collection-link[href*='/p']").first.click(timeout=15000)
                page.wait_for_selector("div.productName", timeout=15000)

            if page.locator("div.productName").count() > 0:
                nome = page.locator("div.productName").first.inner_text()
                preco = page.locator("strong.skuListPrice").first.inner_text() if page.locator("strong.skuListPrice").count() else ""
                promo = page.locator("strong.skuBestPrice").first.inner_text() if page.locator("strong.skuBestPrice").count() else ""
                link = page.url

                print(f"✅ Produto encontrado: {nome}")
                print(f"💰 Preço: {preco}  | Promoção: {promo}")

                return {
                    "EAN": ean,
                    "Produto": nome,
                    "Preço": preco,
                    "Promoção": promo,
                    "Link": link,
                    "Status": "Encontrado"
                }

            print("❌ Produto não identificado na página.")
            return {"EAN": ean, "Produto": "", "Preço": "", "Promoção": "", "Link": "", "Status": "Erro: Produto não encontrado"}

    except Exception as e:
        print(f"🚨 Erro ao buscar EAN {ean}: {type(e).__name__} - {e}")
        return {"EAN": ean, "Produto": "", "Preço": "", "Promoção": "", "Link": "", "Status": f"Erro: {type(e).__name__}"}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "arquivo" not in request.files:
            return render_template("index.html", error="Nenhum arquivo enviado.")
        
        arquivo = request.files["arquivo"]
        if arquivo.filename == '' or not arquivo.filename.lower().endswith('.pdf'):
            return render_template("index.html", error="Por favor, envie um arquivo PDF válido.")
        
        caminho_pdf = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_pdf)
        
        codigos = extrair_codigos_ean(caminho_pdf)
        print(f"--- DEBUG: Códigos EAN extraídos do PDF: {codigos} ---")
        
        if not codigos:
            return render_template("index.html", error="Nenhum código EAN encontrado no PDF.")
        
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

        json_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(codigos, f)

        return render_template("processando.html", session_id=session_id)
    
    return render_template("index.html")

@app.route('/start_processing/<session_id>', methods=['GET'])  # Corrigido para GET (SSE)
def start_processing(session_id):
    json_path = os.path.join(UPLOAD_FOLDER, f"{session_id}.json")

    if not os.path.exists(json_path):
        return jsonify({"error": "Sessão inválida ou expirada."}), 400

    with open(json_path, "r", encoding="utf-8") as f:
        codigos_do_request = json.load(f)

    total_codigos = len(codigos_do_request)

    def generate(codigos_list, total):
        resultados = []
        for i, cod in enumerate(codigos_list, 1):
            produto = buscar_produto(cod)
            resultados.append(produto)
            
            progresso = {
                'current': i,
                'total': total,
                'percentage': int((i / total) * 100),
                'ean': cod,
                'status': produto['Status']
            }
            yield f"data: {json.dumps(progresso)}\n\n"

            if i % BATCH_SIZE == 0 and i < total:
                yield f"data: {json.dumps({'status': f'Pausa de {DELAY_AFTER_BATCH}s após lote'})}\n\n"
                time.sleep(DELAY_AFTER_BATCH)
            else:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"resultados_{timestamp}.csv"
        csv_path = os.path.join(RESULTS_FOLDER, csv_filename)
        pd.DataFrame(resultados).to_csv(csv_path, index=False, encoding='utf-8-sig', sep=';')
        
        yield f"data: {json.dumps({'done': True, 'file': csv_filename})}\n\n"

    return Response(generate(codigos_do_request, total_codigos), mimetype='text/event-stream')

@app.route('/download/<path:filename>')
def download(filename):
    return send_file(os.path.join(RESULTS_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
