from flask import Flask, render_template, request, send_file, Response
import json
import pdfplumber
import re
import os
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "resultados"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# --- CONFIGURAÇÕES ---
MAX_RETRIES = 2
REQUEST_TIMEOUT = 60000  # 60 segundos
DELAY_BETWEEN_REQUESTS = 3  # segundos (aumentado para ser mais 'gentil')

# <-- NOVAS CONFIGURAÇÕES DE LOTE -->
BATCH_SIZE = 10
DELAY_AFTER_BATCH = 15 # segundos de pausa após um lote

def extrair_codigos_ean(caminho_pdf):
    # (Função sem alterações)
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

# <-- FUNÇÃO DE BUSCA TOTALMENTE REFEITA PARA MAIOR PRECISÃO -->
def buscar_produto(ean):
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                navegador = p.chromium.launch(headless=True)
                context = navegador.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                pagina = context.new_page()
                
                print(f"🕵️‍♂️ Buscando EAN {ean}...")
                url_busca = f"https://www.drogariasaopaulo.com.br/busca?q={ean}"
                pagina.goto(url_busca, timeout=REQUEST_TIMEOUT, wait_until="domcontentloaded")

                # Seletores para página de produto ou para item na lista de busca
                product_page_selector = "h1.product-name"
                search_result_selector = "a.product-item__container" # Link do produto na lista de busca
                not_found_selector = "div.search-result-message--no-results" # Mensagem de 'não encontrado'

                try:
                    # Espera por qualquer um dos três seletores aparecer
                    pagina.wait_for_selector(
                        f"{product_page_selector}, {search_result_selector}, {not_found_selector}", 
                        timeout=15000
                    )
                except PlaywrightTimeoutError:
                    print(f"EAN {ean}: Timeout. Nenhum seletor de produto ou resultado encontrado.")
                    raise  # Força uma nova tentativa

                # 1. Verifica se caiu na página de busca SEM resultados
                if pagina.locator(not_found_selector).count() > 0:
                    print(f"EAN {ean}: Página de 'Não encontrado' detectada.")
                    status = "Não encontrado"
                    
                # 2. Verifica se caiu na página de resultados da busca
                elif pagina.locator(search_result_selector).count() > 0:
                    print(f"EAN {ean}: Página de busca detectada. Clicando no primeiro item...")
                    pagina.locator(search_result_selector).first.click()
                    pagina.wait_for_load_state('domcontentloaded', timeout=REQUEST_TIMEOUT)
                    # Agora que navegamos, extraímos os dados
                    status = "Encontrado (após clique)"
                
                # 3. Se não for nenhum dos casos acima, já deve estar na página do produto
                else:
                    status = "Encontrado (direto)"

                # Bloco de extração (só roda se um produto foi encontrado)
                nome, preco, promo, link = "", "", "", ""
                if "Não encontrado" not in status:
                    try:
                        nome = pagina.locator("h1.product-name").inner_text(timeout=5000)
                        preco = pagina.locator("span.price-best").first.inner_text(timeout=5000)
                        promo_el = pagina.locator("span.price-original").first
                        promo = promo_el.inner_text(timeout=5000) if promo_el.count() > 0 else ""
                        link = pagina.url
                        print(f"✅ EAN {ean}: {nome} - {preco}")
                    except Exception as e:
                        print(f"❌ Erro ao extrair dados para EAN {ean}: {e}")
                        status = "Erro na extração"

                context.close()
                return {"EAN": ean, "Produto": nome, "Preço": preco, "Promoção": promo, "Link": link, "Status": status, "Tentativas": attempt + 1}

        except Exception as e:
            print(f"❌ Falha na tentativa {attempt + 1} para o EAN {ean}: {e}")
            if attempt == MAX_RETRIES - 1:
                return {"EAN": ean, "Produto": "", "Preço": "", "Promoção": "", "Link": "", "Status": f"Falha final: {type(e).__name__}", "Tentativas": attempt + 1}
            time.sleep(DELAY_BETWEEN_REQUESTS * 2)


@app.route("/", methods=["GET", "POST"])
def index():
    # (Função sem alterações)
    if request.method == "POST":
        if "arquivo" not in request.files:
            return render_template("index.html", error="Nenhum arquivo enviado.")
        arquivo = request.files["arquivo"]
        if arquivo.filename == '' or not arquivo.filename.lower().endswith('.pdf'):
            return render_template("index.html", error="Por favor, envie um arquivo PDF válido.")
        caminho_pdf = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_pdf)
        codigos = extrair_codigos_ean(caminho_pdf)
        if not codigos:
            return render_template("index.html", error="Nenhum código EAN encontrado no PDF.")
        return render_template("processando.html", codigos=codigos)
    return render_template("index.html")

# <-- ROTA DE PROGRESSO ALTERADA PARA INCLUIR LÓGICA DE LOTE -->
@app.route('/progress')
def progress():
    def generate():
        codigos = request.args.getlist('codigos[]')
        total = len(codigos)
        resultados = []
        
        for i, cod in enumerate(codigos, 1):
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
            
            # --- Lógica de pausa por lote ---
            if i % BATCH_SIZE == 0 and i < total:
                msg_pausa = f'Fim do lote {i // BATCH_SIZE}. Pausando por {DELAY_AFTER_BATCH}s...'
                print(f"--- {msg_pausa} ---")
                yield f"data: {json.dumps({'status': msg_pausa})}\n\n"
                time.sleep(DELAY_AFTER_BATCH)
            else:
                time.sleep(DELAY_BETWEEN_REQUESTS)

        # Salva o arquivo CSV com nome único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"resultados_{timestamp}.csv"
        csv_path = os.path.join(RESULTS_FOLDER, csv_filename)
        pd.DataFrame(resultados).to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        yield f"data: {json.dumps({'done': True, 'file': csv_path})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<path:filename>')
def download(filename):
    # (Função sem alterações)
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)