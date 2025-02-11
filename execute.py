import time
import joblib
import csv
from datetime import datetime
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor

class TradingBot:
    def __init__(self, api, pair="btcidr", modal=20000, stop_loss_pct=0.02, take_profit_pct=0.05, trailing_stop_pct=0.01):
        self.api = api
        self.pair = pair
        self.modal = modal
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.analysis = TechnicalAnalysis(api, pair)
        self.model = joblib.load("price_predictor.pkl")
        self.harga_tertinggi = 0
        self.status = "Menunggu"

    def log_transaction(self, action, price, jumlah_crypto):
        with open("trading_log.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), action, price, jumlah_crypto])

    def execute_trade(self):
        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        jumlah_crypto = self.modal / harga_beli
        prediksi_harga = self.model.predict_price(harga_beli)
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)
        self.harga_tertinggi = harga_beli

        print(f"\nPrediksi AI: Harga akan menjadi {prediksi_harga}")
        if prediksi_harga < harga_beli:
            print("[❌] AI memprediksi harga akan turun. Tidak melakukan pembelian.")
            return
        else:
            print("[✅] AI memprediksi harga akan naik. Melanjutkan eksekusi trading.")

        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")
        
        self.log_transaction("BUY", harga_beli, jumlah_crypto)

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.harga_tertinggi = max(self.harga_tertinggi, harga_sekarang)
            trailing_stop = self.harga_tertinggi * (1 - self.trailing_stop_pct)

            print(f"\n[EKSEKUSI] Harga Sekarang: {harga_sekarang} | Trailing Stop: {trailing_stop}")

            if harga_sekarang >= take_profit:
                print("[✅] Take Profit Tercapai! Menjual aset...")
                break
            elif harga_sekarang <= stop_loss or harga_sekarang <= trailing_stop:
                print("[❌] Stop Loss atau Trailing Stop Tercapai! Menjual aset...")
                break
            time.sleep(2)

    def sell_trade(self, harga_jual, jumlah_crypto):
        print(f"Menjual {jumlah_crypto} unit pada harga {harga_jual}")
        self.log_transaction("SELL", harga_jual, jumlah_crypto)
