
import requests
import time
import threading
from flask import Flask, request

# === Конфигурация ===
WAX_ACCOUNT = 'bitgetxpr'
TELEGRAM_BOT_TOKEN = '8183156039:AAEm2qKnA5bGQivpEgXa5wjLCd5a6CMZuTw'
TELEGRAM_CHAT_ID = '-1002813651741'
LAST_TX_ID_FILE = 'last_wax_tx.txt'
HYPERION_API = 'https://wax.eosusa.io/v2/history/get_actions'
WAX_API_BALANCE = 'https://chain.wax.io/v1/chain/get_currency_balance'

# === Flask-сервер для Telegram webhook ===
app = Flask(__name__)

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    if 'message' in data:
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')

        if text.strip() == '/start':
            balance = get_balance()
            message = f"👋 Привет! Баланс кошелька <b>{WAX_ACCOUNT}</b>:\n<b>{balance}</b>"
            send_to_telegram(message, chat_id)
    return 'ok', 200

def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    webhook_url = f"https://{REPLIT_DOMAIN}/{TELEGRAM_BOT_TOKEN}"
    requests.post(url, data={"url": webhook_url})

# === Получаем последние действия ===
def get_latest_actions():
    params = {
        'account': WAX_ACCOUNT,
        'limit': 5,
        'sort': 'desc'
    }
    response = requests.get(HYPERION_API, params=params)
    if response.status_code == 200:
        return response.json().get('actions', [])
    return []

# === Получить баланс WAXP ===
def get_balance():
    response = requests.post(WAX_API_BALANCE, json={
        "account": WAX_ACCOUNT,
        "code": "eosio.token",
        "symbol": "WAX"
    })
    if response.status_code == 200:
        balances = response.json()
        return balances[0] if balances else "0.00000000 WAX"
    return "Ошибка получения баланса"

# === Отправка в Telegram ===
def send_to_telegram(message, chat_id=TELEGRAM_CHAT_ID):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    requests.post(url, data=data)

# === Работа с файлом состояния ===
def read_last_tx_id():
    try:
        with open(LAST_TX_ID_FILE, 'r') as file:
            return int(file.read().strip())
    except:
        return 0

def write_last_tx_id(tx_id):
    with open(LAST_TX_ID_FILE, 'w') as file:
        file.write(str(tx_id))

# === Основной цикл логгирования депозитов ===
def monitor_deposits():
    last_seen_id = read_last_tx_id()

    while True:
        actions = get_latest_actions()
        new_actions = []

        for action in reversed(actions):
            tx_id = int(action['global_sequence'])
            act = action['act']

            if tx_id > last_seen_id and act['name'] == 'transfer':
                data = act['data']
                if data.get('to') == WAX_ACCOUNT:
                    new_actions.append((tx_id, data, action['timestamp']))

        for tx_id, data, timestamp in new_actions:
            message = (
                f"💰 <b>Депозит WAXP</b>\n"
                f"<b>От:</b> {data['from']}\n"
                f"<b>Кому:</b> {data['to']}\n"
                f"<b>Сумма:</b> {data['quantity']}\n"
                f"<b>Мемо:</b> {data['memo']}\n"
                f"<b>Время:</b> {timestamp}"
            )
            send_to_telegram(message)
            last_seen_id = tx_id
            write_last_tx_id(tx_id)

        time.sleep(30)

# === Запуск ===



# === Конфигурация TLOS ===
TLOS_ACCOUNT = 'bdhivesteem'
TLOS_HYPERION_API = 'https://telos.caleos.io/v2/history/get_actions'
LAST_TLOS_TX_FILE = 'last_tlos_tx.txt'

def read_last_tlos_tx_id():
    try:
        with open(LAST_TLOS_TX_FILE, 'r') as file:
            return int(file.read().strip())
    except:
        return 0

def write_last_tlos_tx_id(tx_id):
    with open(LAST_TLOS_TX_FILE, 'w') as file:
        file.write(str(tx_id))

# === Логгирование переводов на TLOS ===
def monitor_tlos_deposits():
    last_seen_id = read_last_tlos_tx_id()

    while True:
        params = {
            'account': TLOS_ACCOUNT,
            'limit': 5,
            'sort': 'desc'
        }
        response = requests.get(TLOS_HYPERION_API, params=params)
        if response.status_code != 200:
            time.sleep(10)
            continue

        actions = response.json().get('actions', [])
        new_actions = []

        for action in reversed(actions):
            tx_id = int(action['global_sequence'])
            act = action['act']

            if tx_id > last_seen_id and act['name'] == 'transfer':
                data = act['data']
                if data.get('to') == TLOS_ACCOUNT:
                    new_actions.append((tx_id, data, action['timestamp']))

        for tx_id, data, timestamp in new_actions:
            amount = data.get('quantity', '')
            sender = data.get('from', '')
            memo = data.get('memo', '')
            message = (
                f"📥 <b>Новый депозит TLOS</b>\n"
                f"👤 Отправитель: <code>{sender}</code>\n"
                f"💰 Сумма: <b>{amount}</b>\n"
                f"📝 Memo: <i>{memo}</i>\n"
                f"🕒 Время: {timestamp}"
            )
            send_to_telegram(message)
            write_last_tlos_tx_id(tx_id)

        time.sleep(10)



if __name__ == '__main__':
    threading.Thread(target=monitor_deposits, daemon=True).start()
    threading.Thread(target=monitor_tlos_deposits, daemon=True).start()
    app.run(host='0.0.0.0', port=8080)
