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

    def ensure_model(self):
        if not self.model.is_model_trained():
            print("[⚠️] Model belum tersedia, melakukan pelatihan...")
            logging.warning(f"Model untuk {self.pair} belum tersedia. Melakukan pelatihan...")
            self.model.train_model()

    def simulate_trade(self, mode="live"):
        self.ensure_model()

        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        jumlah_crypto = self.modal / harga_beli
        prediksi_harga = self.model.predict_price(harga_beli)
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

        logging.info(f"Prediksi AI untuk {self.pair}: {prediksi_harga} | Harga Saat Ini: {harga_beli}")

        print(f"\nPrediksi AI: Harga akan menjadi {prediksi_harga}")
        if prediksi_harga is None:
            print("[❌] Gagal memprediksi harga. Simulasi dihentikan.")
            return
        elif prediksi_harga < harga_beli:
            print("[❌] AI memprediksi harga akan turun. Simulasi tidak melakukan pembelian.")
            return
        else:
            print("[✅] AI memprediksi harga akan naik. Melanjutkan simulasi trading.")

        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")

        self.collector.log_transaction("SIMULATED_BUY", harga_beli, jumlah_crypto)

        if mode == "historical":
            df = self.collector.get_historical_data()
            if df is None:
                print("[❌] Tidak ada data historis.")
                return
            for _, row in df.iterrows():
                harga_sekarang = row['price']
                print(f"[SIMULASI HISTORIS] Harga Sekarang: {harga_sekarang}")
                if harga_sekarang >= take_profit:
                    self.collector.log_transaction("SIMULATED_SELL", harga_sekarang, jumlah_crypto)
                    print(f"[✅] Take Profit Tercapai dalam simulasi historis di harga {harga_sekarang}!")
                    return
                elif harga_sekarang <= stop_loss:
                    self.collector.log_transaction("SIMULATED_SELL", harga_sekarang, jumlah_crypto)
                    print(f"[❌] Stop Loss Terpenuhi dalam simulasi historis di harga {harga_sekarang}!")
                    return
                time.sleep(0.5)

        else:
            while True:
                harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
                print(f"[SIMULASI LIVE] Harga Sekarang: {harga_sekarang}")

                if harga_sekarang >= take_profit:
                    self.collector.log_transaction("SIMULATED_SELL", harga_sekarang, jumlah_crypto)
                    print(f"[✅] Take Profit Tercapai dalam simulasi live di harga {harga_sekarang}!")
                    break
                elif harga_sekarang <= stop_loss:
                    self.collector.log_transaction("SIMULATED_SELL", harga_sekarang, jumlah_crypto)
                    print(f"[❌] Stop Loss Terpenuhi dalam simulasi live di harga {harga_sekarang}!")
                    break
                time.sleep(1)

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = SimulationBotAI(api)
    bot.simulate_trade(mode="historical")  # Ubah ke "live" untuk simulasi real-time
