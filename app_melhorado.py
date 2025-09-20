from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import random
import string
import logging
import os

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==== CONFIG ====
API_KEY_TEMPMail = "Bearer tempmail.20250814.mhnfmriw94lkwb5d2o46y46u9kv3bsp5cd09dt2mz0d0g8v6"
BASE_URL = "https://api.tempmail.lol"
HEADERS = {"Authorization": API_KEY_TEMPMail}

# ==== Funções auxiliares ====
def gerar_nome():
    """Gera um nome de usuário aleatório"""
    prefixos = ['user', 'admin', 'guest', 'client', 'member', 'demo', 'test', 'temp']
    sufixo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return random.choice(prefixos) + sufixo

def gerar_senha():
    """Gera uma senha segura aleatória"""
    simbolos = '!@#$%^&*+=_-'
    caracteres = string.ascii_letters + string.digits + simbolos
    return ''.join(random.choices(caracteres, k=random.randint(8, 16)))

def criar_caixa_email():
    """Cria uma nova caixa de email temporária"""
    try:
        url = f"{BASE_URL}/v2/inbox/create"
        response = requests.post(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 201:
            logger.info("Caixa de email criada com sucesso")
            return response.json()
        else:
            logger.error(f"Erro ao criar caixa de email: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão ao criar caixa de email: {str(e)}")
        return None

def buscar_emails(token):
    """Busca emails na caixa de entrada"""
    try:
        url = f"{BASE_URL}/v2/inbox"
        params = {"token": token}
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        
        if response.ok:
            data = response.json()
            logger.info(f"Emails buscados com sucesso. Total: {len(data.get('emails', []))}")
            return data
        else:
            logger.error(f"Erro ao buscar emails: {response.status_code} - {response.text}")
            return {"error": f"Erro ao buscar emails (Status: {response.status_code})"}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão ao buscar emails: {str(e)}")
        return {"error": "Erro de conexão com o servidor de email"}

# ==== Rotas ====
@app.route('/')
def index():
    """Serve a página principal"""
    return send_from_directory('.', 'index_melhorado.html')

@app.route('/gerar_conta', methods=['GET'])
def gerar_conta():
    """Gera uma nova conta com email temporário"""
    try:
        logger.info("Iniciando geração de nova conta")
        
        usuario = gerar_nome()
        senha = gerar_senha()
        inbox = criar_caixa_email()

        if inbox:
            response_data = {
                "usuario": usuario,
                "senha": senha,
                "email": inbox["address"],
                "token": inbox["token"]
            }
            logger.info(f"Conta gerada com sucesso: {inbox['address']}")
            return jsonify(response_data)
        else:
            logger.error("Falha ao criar email temporário")
            return jsonify({
                "error": "Não foi possível criar o email temporário. Tente novamente em alguns instantes."
            }), 500
            
    except Exception as e:
        logger.error(f"Erro inesperado ao gerar conta: {str(e)}")
        return jsonify({
            "error": "Erro interno do servidor. Tente novamente."
        }), 500

@app.route('/verificar_emails/<token>', methods=['GET'])
def verificar_emails(token):
    """Verifica emails na caixa de entrada"""
    try:
        if not token:
            return jsonify({"error": "Token não fornecido"}), 400
            
        logger.info(f"Verificando emails para token: {token[:10]}...")
        data = buscar_emails(token)
        
        # Adicionar informações extras para melhor debugging
        if "emails" in data:
            for email in data["emails"]:
                # Garantir que todos os campos necessários existam
                email.setdefault("from", "Remetente desconhecido")
                email.setdefault("subject", "Sem assunto")
                email.setdefault("body", "")
                email.setdefault("html", "")
                email.setdefault("date", "")
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro inesperado ao verificar emails: {str(e)}")
        return jsonify({
            "error": "Erro ao verificar emails. Tente novamente."
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificação de saúde do serviço"""
    return jsonify({
        "status": "healthy",
        "service": "TempMail Generator",
        "version": "2.0"
    })

@app.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para erros internos do servidor"""
    logger.error(f"Erro interno do servidor: {str(error)}")
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

