from flask import Flask, jsonify
from ai_model import PricePredictor
from api_utils import IndodaxAPI
from data_collector import DataCollector
import os
import ta
import sqlite3

app = Flask(__name__)

# Izinkan akses dari frontend React
from flask_cors import CORS
CORS(app)

# Inisialisasi API, PricePredictor, dan DataCollector
api = IndodaxAPI()
predictor = PricePredictor(api)
collector = DataCollector(api)

# Fungsi untuk membuat tabel historical_data jika belum ada
def create_historical_data_table():
    conn = sqlite3.connect('historical_data.db')  # Nama file database
    c = conn.cursor()
    
    # Membuat tabel jika belum ada
    c.execute('''
        CREATE TABLE IF NOT EXISTS historical_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            price REAL
        )
    ''')
    conn.commit()
    conn.close()

# Panggil fungsi untuk membuat tabel
create_historical_data_table()

@app.route('/api/saldo', methods=['GET'])
def get_saldo():
    saldo = api.get_balance()
    if saldo:
        return jsonify(saldo)
    return jsonify({'error': 'Gagal mengambil saldo!'})

@app.route('/api/predict_price', methods=['GET'])
def predict_price():
    current_price = 400000  # contoh nilai harga
    rsi = 60
    sma = 350000
    bb_upper = 420000
    bb_lower = 380000
    change_3d = 0.05
    change_7d = 0.07
    change_30d = 0.10

    predicted_price = predictor.predict_price(current_price, rsi, sma, bb_upper, bb_lower, change_3d, change_7d, change_30d)

    return jsonify({
        'predicted_price': predicted_price,
        'current_price': current_price
    })

@app.route('/api/transaction_history', methods=['GET'])
def get_transaction_history():
    history = collector.get_historical_data()
    if history is not None:
        return jsonify(history.to_dict(orient="records"))
    return jsonify({'error': 'Tidak ada riwayat transaksi.'})

@app.route('/api/technical_indicators', methods=['GET'])
def get_technical_indicators():
    df = collector.get_historical_data()  # Mengambil data historis untuk perhitungan indikator
    if df is None or len(df) == 0:
        return jsonify({'error': 'Data historis tidak cukup untuk menghitung indikator!'}), 404

    df['RSI'] = ta.momentum.RSIIndicator(df['price'], window=14).rsi()
    df['SMA'] = ta.trend.SMAIndicator(df['price'], window=20).sma_indicator()
    bb = ta.volatility.BollingerBands(df['price'], window=20)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Lower'] = bb.bollinger_lband()

    latest_data = df.iloc[-1]  # Ambil data terbaru untuk indikator
    return jsonify({
        'RSI': latest_data['RSI'],
        'SMA': latest_data['SMA'],
        'BB_Upper': latest_data['BB_Upper'],
        'BB_Lower': latest_data['BB_Lower']
    })

@app.route('/api/historical_prices', methods=['GET'])
def get_historical_prices():
    df = collector.get_historical_data()
    if df is None or len(df) == 0:
        return jsonify({'error': 'Tidak ada data historis!'}), 404  # Mengembalikan status 404 jika tidak ada data

    # Kembalikan data harga untuk visualisasi
    historical_prices = df[['date', 'price']].to_dict(orient='records')
    return jsonify(historical_prices)

if __name__ == '__main__':
    app.run(debug=True)
