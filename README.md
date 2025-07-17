
# 🧪 EAN Price Scanner
[![Python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33.svg?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Pandas](https://img.shields.io/badge/Pandas-150458.svg?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

Ferramenta web que permite fazer o upload de um PDF contendo códigos EAN (códigos de barras) e consulta automaticamente os preços dos produtos no site que você desejar.

---

## 📦 Funcionalidades

- Extração automática de códigos EAN de arquivos PDF
- Consulta dos produtos no site desejado
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
git clone https://github.com/tabaresu1/pesquisador-site.git
cd pesquisador-site
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

- **O site desejado carrega dados via JavaScript.**  
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

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.
