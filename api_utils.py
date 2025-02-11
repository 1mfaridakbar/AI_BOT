import requests
import time
import hashlib
import hmac
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

class IndodaxAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.secret_key = SECRET_KEY

    def generate_signature(self, payload):
        query_string = "&".join([f"{key}={value}" for key, value in payload.items()])
        return hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha512).hexdigest()

    def get_balance(self):
        payload = {
            "method": "getInfo",
            "timestamp": int(time.time() * 1000)
        }
        headers = {
            "Key": self.api_key,
            "Sign": self.generate_signature(payload)
        }
        response = requests.post(API_URL, data=payload, headers=headers)
        data = response.json()
        return data["return"]["balance"] if data["success"] == 1 else None

    def get_ticker(self, pair="btcidr"):
        url = f"https://indodax.com/api/trades/{pair}?limit=200"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df['price'] = df['price'].astype(float)
        return df[['price', 'date']]

# Fungsi untuk eksekusi trading
# Fungsi untuk eksekusi trading dengan manajemen risiko
def execute_trade(pair="btcidr", modal=20000, stop_loss_pct=0.02, take_profit_pct=0.05):
    harga_beli = get_ticker(pair)['price'].iloc[-1]  # Ambil harga terakhir
    jumlah_crypto = modal / harga_beli
    stop_loss = harga_beli * (1 - stop_loss_pct)  # Stop Loss 2% di bawah harga beli
    take_profit = harga_beli * (1 + take_profit_pct)  # Take Profit 5% di atas harga beli

    print(f"Harga Beli: {harga_beli}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")

    # Order pembelian
    order_payload = {
        "method": "trade",
        "pair": pair,
        "type": "buy",
        "price": harga_beli,
        "btc": jumlah_crypto,
        "timestamp": int(time.time() * 1000)
    }
    encoded_payload = urllib.parse.urlencode(order_payload)
    headers = {
        "Key": API_KEY,
        "Sign": generate_signature(order_payload, SECRET_KEY)
    }
    response = requests.post(API_URL, data=encoded_payload, headers=headers)
    result = response.json()

    if result["success"] == 1:
        print("Order Berhasil! Menunggu kondisi Take Profit atau Stop Loss...")
        while True:
            harga_sekarang = get_ticker(pair)['price'].iloc[-1]  # Cek harga terbaru
            print(f"Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                print("Take Profit Tercapai! Menjual aset...")
                sell_trade(pair, harga_sekarang, jumlah_crypto)
                break
            elif harga_sekarang <= stop_loss:
                print("Stop Loss Terpenuhi! Menjual aset untuk meminimalkan kerugian...")
                sell_trade(pair, harga_sekarang, jumlah_crypto)
                break
            time.sleep(5)  # Cek harga setiap 5 detik
    else:
        print("Order Gagal!")

# Fungsi untuk menjual aset
def sell_trade(pair, harga_jual, jumlah_crypto):
    order_payload = {
        "method": "trade",
        "pair": pair,
        "type": "sell",
        "price": harga_jual,
        "btc": jumlah_crypto,
        "timestamp": int(time.time() * 1000)
    }
    encoded_payload = urllib.parse.urlencode(order_payload)
    headers = {
        "Key": API_KEY,
        "Sign": generate_signature(order_payload, SECRET_KEY)
    }
    response = requests.post(API_URL, data=encoded_payload, headers=headers)
    result = response.json()
    print("Order Jual Berhasil!" if result["success"] == 1 else "Order Jual Gagal!")



# Fungsi untuk eksekusi trading
# Fungsi untuk eksekusi trading dengan manajemen risiko
def execute_trade(pair="btcidr", modal=20000, stop_loss_pct=0.02, take_profit_pct=0.05):
    harga_beli = get_ticker(pair)['price'].iloc[-1]  # Ambil harga terakhir
    jumlah_crypto = modal / harga_beli
    stop_loss = harga_beli * (1 - stop_loss_pct)  # Stop Loss 2% di bawah harga beli
    take_profit = harga_beli * (1 + take_profit_pct)  # Take Profit 5% di atas harga beli

    print(f"Harga Beli: {harga_beli}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")

    # Order pembelian
    order_payload = {
        "method": "trade",
        "pair": pair,
        "type": "buy",
        "price": harga_beli,
        "btc": jumlah_crypto,
        "timestamp": int(time.time() * 1000)
    }
    encoded_payload = urllib.parse.urlencode(order_payload)
    headers = {
        "Key": API_KEY,
        "Sign": generate_signature(order_payload, SECRET_KEY)
    }
    response = requests.post(API_URL, data=encoded_payload, headers=headers)
    result = response.json()

    if result["success"] == 1:
        print("Order Berhasil! Menunggu kondisi Take Profit atau Stop Loss...")
        while True:
            harga_sekarang = get_ticker(pair)['price'].iloc[-1]  # Cek harga terbaru
            print(f"Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                print("Take Profit Tercapai! Menjual aset...")
                sell_trade(pair, harga_sekarang, jumlah_crypto)
                break
            elif harga_sekarang <= stop_loss:
                print("Stop Loss Terpenuhi! Menjual aset untuk meminimalkan kerugian...")
                sell_trade(pair, harga_sekarang, jumlah_crypto)
                break
            time.sleep(5)  # Cek harga setiap 5 detik
    else:
        print("Order Gagal!")

# Fungsi untuk menjual aset
def sell_trade(pair, harga_jual, jumlah_crypto):
    order_payload = {
        "method": "trade",
        "pair": pair,
        "type": "sell",
        "price": harga_jual,
        "btc": jumlah_crypto,
        "timestamp": int(time.time() * 1000)
    }
    encoded_payload = urllib.parse.urlencode(order_payload)
    headers = {
        "Key": API_KEY,
        "Sign": generate_signature(order_payload, SECRET_KEY)
    }
    response = requests.post(API_URL, data=encoded_payload, headers=headers)
    result = response.json()
    print("Order Jual Berhasil!" if result["success"] == 1 else "Order Jual Gagal!")

