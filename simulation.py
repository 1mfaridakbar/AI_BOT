import time
from datetime import datetime
import joblib
import os
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor

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

    def ensure_model(self):
        """Pastikan model AI sudah siap sebelum simulasi"""
        if not self.model.is_model_trained():
            print("[⚠️] Model belum tersedia, melakukan pelatihan...")
            self.model.train_model()

    def simulate_trade(self):
        self.ensure_model()

        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        jumlah_crypto = self.modal / harga_beli
        prediksi_harga = self.model.predict_price(harga_beli)
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

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

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.riwayat_harga.append((datetime.now(), harga_sekarang))
            print(f"\n[SIMULASI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                self.status = "✅ Take Profit Tercapai"
                print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang}! Simulasi menjual aset...")
                break
            elif harga_sekarang <= stop_loss:
                self.status = "❌ Stop Loss Terpenuhi"
                print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang}! Simulasi menjual aset...")
                break
            else:
                print("[⏳] Harga belum mencapai Take Profit atau Stop Loss...")
            time.sleep(2)

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = SimulationBotAI(api)
    bot.simulate_trade()
