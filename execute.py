import time
from datetime import datetime
import joblib
import os
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor
from data_collector import DataCollector

class TradingBotAI:
    def __init__(self, api, pair="btcidr", modal=20000, stop_loss_pct=0.005, take_profit_pct=0.005):
        self.api = api
        self.pair = pair
        self.modal = modal
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.riwayat_harga = []
        self.status = "Menunggu"
        self.analysis = TechnicalAnalysis(api, pair)
        self.model = PricePredictor(api, pair)
        self.collector = DataCollector(api, pair)

    def collect_and_train_data(self):
        print("Mengumpulkan data historis dan melatih model AI...")
        self.collector.log_transaction("DATA_COLLECTION", 0, 0)
        self.model.train_model()
        print("Model AI telah diperbarui dengan data terbaru.")

    def ensure_model(self):
        if not self.model.is_model_trained():
            print("[⚠️] Model belum tersedia, melakukan pelatihan...")
            self.collect_and_train_data()

    def execute_trade(self):
        self.ensure_model()

        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        jumlah_crypto = self.modal / harga_beli
        prediksi_harga = self.model.predict_price(harga_beli)
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

        print(f"\nPrediksi AI: Harga akan menjadi {prediksi_harga}")
        if prediksi_harga < harga_beli:
            print("[❌] AI memprediksi harga akan turun. Tidak melakukan pembelian.")
            return
        else:
            print("[✅] AI memprediksi harga akan naik. Melanjutkan eksekusi trading.")

        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")

        self.collector.log_transaction("BUY", harga_beli, jumlah_crypto)

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.riwayat_harga.append((datetime.now(), harga_sekarang))
            print(f"\n[EKSEKUSI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                self.status = "✅ Take Profit Tercapai"
                print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang}! Menjual aset...")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            elif harga_sekarang <= stop_loss:
                self.status = "❌ Stop Loss Terpenuhi"
                print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang}! Menjual aset...")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            else:
                print("[⏳] Harga belum mencapai Take Profit atau Stop Loss...")
            time.sleep(2)

    def sell_trade(self, harga_jual, jumlah_crypto):
        """Menjual aset di Indodax dan mengembalikan saldo ke dompet"""
        order_payload = {
            "method": "trade",
            "pair": self.pair,
            "type": "sell",
            "price": harga_jual,
            "btc": jumlah_crypto,
            "timestamp": int(time.time() * 1000)
        }
        headers = {
            "Key": self.api.api_key,
            "Sign": self.api.generate_signature(order_payload)
        }
        response = self.api.session.post(self.api.api_url, data=order_payload, headers=headers)
        result = response.json()

        if result["success"] == 1:
            print(f"✅ Order jual berhasil! {jumlah_crypto} {self.pair} dijual dengan harga {harga_jual}")
            self.collector.log_transaction("SELL", harga_jual, jumlah_crypto)
        else:
            print(f"❌ Order jual gagal! Pesan error: {result}")

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = TradingBotAI(api)
    bot.execute_trade()
