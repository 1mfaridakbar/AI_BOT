import time
from datetime import datetime
import joblib
import os
import logging
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor
from data_collector import DataCollector

# Konfigurasi Logging
logging.basicConfig(filename='ai_trading_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info(f"Data dan model AI untuk {self.pair} diperbarui.")

    def ensure_model(self):
        if not self.model.is_model_trained():
            print("[⚠️] Model belum tersedia, melakukan pelatihan...")
            logging.warning(f"Model untuk {self.pair} belum tersedia. Melakukan pelatihan...")
            self.collect_and_train_data()

    def execute_trade(self):
        self.ensure_model()

        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        rsi = analysis['RSI']
        sma = analysis['SMA']
        bb_upper = analysis['BB_Upper']
        bb_lower = analysis['BB_Lower']

        jumlah_crypto = self.modal / harga_beli
        prediksi_harga = self.model.predict_price(harga_beli)
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

        logging.info(f"Prediksi AI untuk {self.pair}: {prediksi_harga} | Harga Saat Ini: {harga_beli} | RSI: {rsi} | SMA: {sma} | BB Upper: {bb_upper} | BB Lower: {bb_lower}")

        print(f"\nPrediksi AI: Harga akan menjadi {prediksi_harga}")
        print(f"RSI: {rsi} | SMA: {sma} | BB Upper: {bb_upper} | BB Lower: {bb_lower}")
        if prediksi_harga is None:
            print("[❌] Gagal memprediksi harga. Tidak melakukan trading.")
            logging.error(f"Gagal memprediksi harga untuk {self.pair}. Tidak melakukan trading.")
            return
        elif prediksi_harga < harga_beli:
            print("[❌] AI memprediksi harga akan turun. Tidak melakukan pembelian.")
            logging.info(f"AI memprediksi harga akan turun untuk {self.pair}. Tidak melakukan pembelian.")
            return
        else:
            print("[✅] AI memprediksi harga akan naik. Melanjutkan eksekusi trading.")
            logging.info(f"AI memprediksi harga akan naik untuk {self.pair}. Melanjutkan eksekusi trading.")

        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")

        self.collector.log_transaction("BUY", harga_beli, jumlah_crypto)

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.riwayat_harga.append((datetime.now(), harga_sekarang))
            logging.info(f"Harga Sekarang: {harga_sekarang} | Stop Loss: {stop_loss} | Take Profit: {take_profit}")
            print(f"\n[EKSEKUSI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                self.status = "✅ Take Profit Tercapai"
                print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang}! Menjual aset...")
                logging.info(f"Take Profit tercapai untuk {self.pair} pada harga {harga_sekarang}. Menjual aset...")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            elif harga_sekarang <= stop_loss:
                self.status = "❌ Stop Loss Terpenuhi"
                print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang}! Menjual aset...")
                logging.info(f"Stop Loss tercapai untuk {self.pair} pada harga {harga_sekarang}. Menjual aset...")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            else:
                print("[⏳] Harga belum mencapai Take Profit atau Stop Loss...")
                logging.info(f"Harga belum mencapai Take Profit atau Stop Loss untuk {self.pair}. Menunggu...")
            time.sleep(2)

    def sell_trade(self, harga_jual, jumlah_crypto):
        """Fungsi untuk menjual aset dan mengembalikan saldo ke dompet pengguna"""
        print(f"[SELL] Menjual {jumlah_crypto} unit {self.pair} pada harga {harga_jual}...")
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
        response = self.api.send_request(order_payload, headers)
        result = response.json()

        if result["success"] == 1:
            print("[✅] Order jual berhasil! Saldo telah diperbarui.")
            logging.info(f"Order jual berhasil pada harga {harga_jual}. Saldo diperbarui.")
        else:
            print("[❌] Order jual gagal! Periksa saldo dan API.")
            logging.error(f"Order jual gagal pada harga {harga_jual}. Respon: {result}")

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = TradingBotAI(api)
    bot.execute_trade()
