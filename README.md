# 🧪 EAN Price Scanner – Consulta de Preços Drogaria São Paulo

Ferramenta web que permite fazer o upload de um PDF contendo códigos EAN (códigos de barras) e consulta automaticamente os preços dos produtos no site da [Drogaria São Paulo](https://www.drogariasaopaulo.com.br).

---

## 📦 Funcionalidades

- Extração automática de códigos EAN de arquivos PDF
- Consulta dos produtos no site da Drogaria São Paulo
- Retorno de informações:
  - Nome do produto
  - Preço promocional (por)
  - Preço original (de)
  - Link do produto
  - Status da busca
- Interface web moderna com barra de progresso em tempo real
- Geração de arquivo CSV com os resultados

---

## 🧰 Tecnologias Utilizadas

- Python 3
- Flask
- Playwright (com Chromium headless)
- pdfplumber
- pandas
- Tailwind CSS (frontend)
- SSE (Server-Sent Events) para progresso em tempo real

---

## 🚀 Como rodar localmente

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/ean-price-scanner.git
cd ean-price-scanner
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
# Ative o ambiente:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
playwright install
```

### 4. Rode o app

```bash
flask run
```

Acesse no navegador:  
👉 `http://127.0.0.1:5000`

---

## 📁 Estrutura do Projeto

```
├── app.py                  # Backend Flask + scraping
├── templates/
│   ├── index.html          # Tela inicial (upload)
│   └── processando.html    # Tela de progresso
├── uploads/                # PDFs e arquivos temporários
├── resultados/             # CSVs gerados
├── requirements.txt
└── README.md
```

---

## ⚠️ Observações importantes

- **O site da Drogaria São Paulo carrega dados via JavaScript.**  
  Por isso é necessário usar **Playwright com Chromium** para simular um navegador real.

- Os dados de sessão são armazenados em arquivos `.json` temporários para evitar estourar o limite de cookies.

- Produtos não encontrados também são incluídos no CSV final com status `Não encontrado`.

---

## 📤 Futuras melhorias sugeridas

- Exportar para Excel (XLSX)
- Deploy online via VPS com Docker
- Painel de histórico de consultas
- Filtro para exibir apenas encontrados

---

## 🐍 Desenvolvido com ❤️ em Python