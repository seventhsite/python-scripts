#!/usr/bin/env python3

import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

# Replace <BINANCE_API_KEY> and <BINANCE_API_SECRET> with your own Binance API key and secret
binance_api_key = '<BINANCE_API_KEY>'
binance_api_secret = '<BINANCE_API_SECRET>'

# Replace <TELEGRAM_CHAT_ID> and <TELEGRAM_BOT_TOKEN> with your own Telegram chat ID and bot token
telegram_chat_id = '<TELEGRAM_CHAT_ID>'
telegram_bot_token = '<TELEGRAM_BOT_TOKEN>'

# Set the API endpoint URLs
binance_account_info_url = 'https://api.binance.com/api/v3/account'
binance_open_orders_url = 'https://api.binance.com/api/v3/openOrders'
binance_free_money_url = 'https://api.binance.com/sapi/v1/capital/config/getall'

# Set the current timestamp
timestamp = int(time.time() * 1000)

# Set the request headers
headers = {
    'X-MBX-APIKEY': binance_api_key
}

# Set the request payload for the account info request
payload = {
    'timestamp': timestamp
}

# Generate the signature for the request
signature = hmac.new(binance_api_secret.encode('utf-8'), urlencode(payload).encode('utf-8'), hashlib.sha256).hexdigest()

# Add the signature to the payload
payload['signature'] = signature

# Send the request to the Binance API to get the account info
response = requests.get(binance_account_info_url, headers=headers, params=payload)

# Get the account balances from the response
balances = response.json()['balances']

# Send the request to the Binance API to get the open orders
response = requests.get(binance_open_orders_url, headers=headers, params=payload)

# Parse the response to get the open orders information
open_orders = response.json()
order_amounts = {}
for order in open_orders:
    symbol = order['symbol']
    amount = float(order['origQty'])
    if symbol in order_amounts:
        order_amounts[symbol] += amount
    else:
        order_amounts[symbol] = amount

# Send the request to the Binance API to get the free money amount
response = requests.get(binance_free_money_url, headers=headers, params=payload)

# Parse the response to get the free money amount
free_money_amounts = {}
for asset in response.json():
    symbol = asset['coin']
    if asset['free'] != '0':
        free_money_amounts[symbol] = float(asset['free'])

# Build the message to send to Telegram
message = 'Binance Account Information:\n\n'
message += 'Balances:\n'
for balance in balances:
    if float(balance['free']) > 0:
        message += f"{balance['asset']}: {balance['free']}\n"
message += '\nOpen Orders:\n'
for symbol, amount in order_amounts.items():
    message += f"{symbol}: {amount}\n"
message += '\nFree Money Amounts:\n'
for symbol, amount in free_money_amounts.items():
    message += f"{symbol}: {amount}\n"

# Send the message to Telegram
telegram_send_message_url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
requests.post(telegram_send_message_url, json={'chat_id': telegram_chat_id, 'text': message})
