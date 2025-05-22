import requests
import os
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import JobQueue
from telegram import Update
from datetime import datetime

# --- ESTAS SÃO AS LINHAS QUE VOCÊ DEVE MUDAR/ADICIONAR ---
# Usamos os.getenv() que é uma forma padrão de obter variáveis de ambiente
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# IMPRIMIMOS ESTES VALORES PARA VOCÊ VER NOS LOGS DO RENDER.COM
print(f"--- DEBUG ENVIRONMENT VARIABLES ---")
print(f"BOT_TOKEN (do ambiente): {TOKEN}")
print(f"CHAT_ID (do ambiente): {CHAT_ID}")
print(f"--- FIM DEBUG ---")

# Adicionamos uma validação explícita para evitar o erro do Updater
if not TOKEN:
    print("ERRO CRÍTICO: Variável de ambiente BOT_TOKEN não foi encontrada ou está vazia!")
    exit(1) # Saia do script se o token não estiver presente

if not CHAT_ID:
    print("AVISO: Variável de ambiente CHAT_ID não foi encontrada ou está vazia! Alguns recursos podem não funcionar.")
    # Não saia aqui, mas o JobQueue pode falhar ao enviar mensagens
# --- FIM DAS LINHAS QUE VOCÊ DEVE MUDAR/ADICIONAR ---


# O restante do seu código vem aqui, como já estava.
# A partir daqui, você não precisa mudar nada do que já tem.

def fetch_signal():
    url = "https://api.dexscreener.com/latest/dex/pairs"
    response = requests.get(url)

    if response.status_code != 200:
        return "⚠️ Erro ao buscar sinais."

    data = response.json()["pairs"]
    
    melhores = []
    for par in data:
        try:
            # Certifique-se de que 'priceUsd' e 'priceChange' existem e são válidos
            if "priceUsd" in par and par["priceUsd"] and float(par["priceUsd"]) > 0:
                if "priceChange" in par and "h1" in par["priceChange"] and float(par["priceChange"]["h1"]) > 50:
                    melhores.append(par)
        except (ValueError, KeyError) as e:
            # Captura erros específicos de conversão ou chave ausente
            print(f"Erro ao processar par {par.get('baseToken', {}).get('symbol', 'N/A')}: {e}")
            continue

    if not melhores:
        return "❌ Nenhum sinal underground detectado no momento."

    melhores = sorted(melhores, key=lambda x: float(x["priceChange"]["h1"]), reverse=True)[:1]

    msg = "🚨 NOVO SINAL DETECTADO – AUTO AI\n\n"
    for m in melhores:
        msg += f"""🪙 Token: {m['baseToken']['symbol']}
🔗 Dex: {m['dexId']}
📈 Preço: ${m['priceUsd']}
📊 Variação 1h: {m['priceChange']['h1']}%
🔍 Link: {m['url']}
🕒 Atualizado: {datetime.now().strftime('%d/%m %H:%M')}
"""
    return msg

def sinal(update: Update, context: CallbackContext):
    msg = fetch_signal()
    update.message.reply_text(msg)

def job_send_signal(context: CallbackContext):
    msg = fetch_signal()
    # Usando os.getenv() aqui também para consistência
    target_chat_id = os.getenv("CHAT_ID") 
    if target_chat_id:
        context.bot.send_message(chat_id=target_chat_id, text=msg)
    else:
        print("ERRO: CHAT_ID não está definido para enviar o sinal agendado.")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 CRYPTOPSIA está pronto para te mostrar sinais reais.")
    update.message.reply_text("⏱️ Um novo sinal será enviado automaticamente a cada 30 minutos.")

# A inicialização do Updater só acontece se o TOKEN existir.
# Esta linha agora deve estar segura, pois já verificamos TOKEN acima.
updater = Updater(TOKEN, use_context=True) 
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("sinal", sinal))

job_queue = updater.job_queue
job_queue.run_repeating(job_send_signal, interval=1800, first=10)

updater.start_polling()
updater.idle()