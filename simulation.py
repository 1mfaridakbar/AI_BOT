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
logging.basicConfig(filename='simulation_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class SimulationBotAI:
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
        print("Mengumpulkan data historis dan melatih model AI untuk simulasi...")
        self.collector.log_transaction("SIMULATION_DATA_COLLECTION", 0, 0)
        self.model.train_model()
        print("Model AI telah diperbarui dengan data terbaru.")
        logging.info(f"Data dan model AI untuk simulasi {self.pair} diperbarui.")

    def ensure_model(self):
        if not self.model.is_model_trained():
            print("[⚠️] Model belum tersedia, melakukan pelatihan untuk simulasi...")
            logging.warning(f"Model untuk {self.pair} belum tersedia dalam simulasi. Melakukan pelatihan...")
            self.collect_and_train_data()

    def simulate_trade(self):
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
            print("[❌] Gagal memprediksi harga. Simulasi dihentikan.")
            logging.error(f"Gagal memprediksi harga untuk {self.pair} dalam simulasi.")
            return
        elif prediksi_harga < harga_beli:
            print("[❌] AI memprediksi harga akan turun. Simulasi tidak melakukan pembelian.")
            logging.info(f"AI memprediksi harga akan turun dalam simulasi untuk {self.pair}. Tidak melakukan pembelian.")
            return
        else:
            print("[✅] AI memprediksi harga akan naik. Melanjutkan simulasi trading.")
            logging.info(f"AI memprediksi harga akan naik dalam simulasi untuk {self.pair}. Melanjutkan trading.")

        print(f"Harga Beli (Simulasi): {harga_beli}")
        print(f"Stop Loss (Simulasi): {stop_loss}")
        print(f"Take Profit (Simulasi): {take_profit}")

        self.collector.log_transaction("SIMULATED_BUY", harga_beli, jumlah_crypto)

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.riwayat_harga.append((datetime.now(), harga_sekarang))
            logging.info(f"Harga Sekarang (Simulasi): {harga_sekarang} | Stop Loss: {stop_loss} | Take Profit: {take_profit}")
            print(f"\n[SIMULASI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                self.status = "✅ Take Profit Tercapai (Simulasi)"
                print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang} dalam simulasi! Menjual aset...")
                logging.info(f"Take Profit tercapai dalam simulasi untuk {self.pair} pada harga {harga_sekarang}.")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            elif harga_sekarang <= stop_loss:
                self.status = "❌ Stop Loss Terpenuhi (Simulasi)"
                print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang} dalam simulasi! Menjual aset...")
                logging.info(f"Stop Loss tercapai dalam simulasi untuk {self.pair} pada harga {harga_sekarang}.")
                self.sell_trade(harga_sekarang, jumlah_crypto)
                break
            else:
                print("[⏳] Harga belum mencapai Take Profit atau Stop Loss dalam simulasi...")
                logging.info(f"Harga belum mencapai Take Profit atau Stop Loss dalam simulasi untuk {self.pair}. Menunggu...")
            time.sleep(2)

    def sell_trade(self, harga_jual, jumlah_crypto):
        """Fungsi simulasi untuk mencatat transaksi jual tanpa benar-benar mengeksekusi order"""
        print(f"[SIMULATED SELL] Menjual {jumlah_crypto} unit {self.pair} pada harga {harga_jual} dalam simulasi...")
        self.collector.log_transaction("SIMULATED_SELL", harga_jual, jumlah_crypto)
        logging.info(f"Simulasi penjualan selesai: {jumlah_crypto} {self.pair} pada harga {harga_jual}.")

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = SimulationBotAI(api)
    bot.simulate_trade()
