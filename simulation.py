import time
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from datetime import datetime

class SimulationBot:
    def __init__(self, api, pair="btcidr", modal=20000, stop_loss_pct=0.005, take_profit_pct=0.005):
        self.api = api
        self.pair = pair
        self.modal = modal
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.riwayat_harga = []
        self.status = "Menunggu"
        self.analysis = TechnicalAnalysis(api, pair)

    def simulate_trade(self):
        analysis = self.analysis.analyze()
        harga_beli = analysis['price']
        jumlah_crypto = self.modal / harga_beli
        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

        print(f"\nSimulasi Trading: {self.pair}")
        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")

        while True:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            self.riwayat_harga.append((datetime.now(), harga_sekarang))
            print(f"\n[SIMULASI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

            if harga_sekarang >= take_profit:
                self.status = "✅ Take Profit Tercapai"
                print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang}! Menjual aset dalam simulasi...")
                break
            elif harga_sekarang <= stop_loss:
                self.status = "❌ Stop Loss Terpenuhi"
                print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang}! Menjual aset dalam simulasi...")
                break
            else:
                print("[⏳] Harga belum mencapai Take Profit atau Stop Loss...")
            time.sleep(5)

if __name__ == "__main__":
    from api_utils import IndodaxAPI  # Pastikan API diimpor dengan benar

    API_KEY = "VONQF0DA-CG1USP8W-PYW9NDGK-V2G0PHZ8-VY1E69YA"
    SECRET_KEY = "90245e9ccd31f984bbe5117e4e79d422197c063be44f36b4844f05cd227a52665f83d4f4b11e6267"

    api = IndodaxAPI(API_KEY, SECRET_KEY)  # Buat instance API
    bot = SimulationBot(api=api)  # Pastikan SimulationBot menerima API sebagai parameter
    bot.simulate_trade()
