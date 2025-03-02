import time
import logging
from datetime import datetime
import threading
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor
from data_collector import DataCollector

logging.basicConfig(filename='ai_trading_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBotAI:
    def __init__(self, api, pair="btcidr", modal=20000, stop_loss_pct=0.007, take_profit_pct=0.001):
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
        self.running = False

    def get_historical_features(self):
        try:
            df = self.collector.get_historical_data()
            if df is None or len(df) < 30:
                logging.warning("Data historis tidak cukup. Menggunakan nilai default 0 untuk fitur.")
                return 0, 0, 0  # Nilai default jika data tidak mencukupi
            df = df.sort_values(by=['date']).reset_index(drop=True)
            price_change_3d = df['price'].pct_change(periods=3).iloc[-1]
            price_change_7d = df['price'].pct_change(periods=7).iloc[-1]
            price_change_30d = df['price'].pct_change(periods=30).iloc[-1]
            return price_change_3d, price_change_7d, price_change_30d
        except Exception as e:
            logging.error("Error saat mengambil fitur historis: %s", e)
            return 0, 0, 0

    def ensure_model(self):
        if not self.model.is_model_trained():
            logging.warning("Model belum tersedia, melakukan pelatihan...")
            self.model.train_model()

    def execute_trade(self):
        self.ensure_model()
        try:
            analysis = self.analysis.analyze()
        except Exception as e:
            logging.error("Error dalam analisis teknikal: %s", e)
            return

        harga_beli = analysis['price']
        rsi = analysis['RSI']
        sma = analysis['SMA']
        bb_upper = analysis['BB_Upper']
        bb_lower = analysis['BB_Lower']

        price_change_3d, price_change_7d, price_change_30d = self.get_historical_features()
        
        try:
            jumlah_crypto = self.modal / harga_beli
        except ZeroDivisionError:
            logging.error("Harga beli adalah 0, tidak dapat melakukan pembelian.")
            return

        try:
            prediksi_harga = self.model.predict_price(
                harga_beli, rsi, sma, bb_upper, bb_lower, 
                price_change_3d, price_change_7d, price_change_30d
            )
        except Exception as e:
            logging.error("Error saat prediksi harga: %s", e)
            return

        stop_loss = harga_beli * (1 - self.stop_loss_pct)
        take_profit = harga_beli * (1 + self.take_profit_pct)

        logging.info("Prediksi AI: %s | Harga: %s | RSI: %s | SMA: %s | BB Upper: %s | BB Lower: %s", 
                     prediksi_harga, harga_beli, rsi, sma, bb_upper, bb_lower)
        print(f"\nPrediksi AI: Harga akan menjadi {prediksi_harga}")
        print(f"Harga Beli: {harga_beli}")
        print(f"Stop Loss: {stop_loss}")
        print(f"Take Profit: {take_profit}")

        if prediksi_harga is None:
            logging.error("Gagal memprediksi harga. Tidak melakukan trading.")
            print("[❌] Gagal memprediksi harga. Tidak melakukan trading.")
            return
        elif prediksi_harga < harga_beli and rsi < 40:
            logging.info("Prediksi harga turun, tidak melakukan pembelian.")
            print("[❌] AI memprediksi harga akan turun. Tidak melakukan pembelian.")
            return
        elif prediksi_harga > harga_beli and rsi > 50 and sma > harga_beli:
            logging.info("Prediksi harga naik, melanjutkan eksekusi trading.")
            print("[✅] AI memprediksi harga akan naik. Melanjutkan eksekusi trading.")

        self.collector.log_transaction("BUY", harga_beli, jumlah_crypto)

        # Mulai monitoring harga dalam thread terpisah
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_price, args=(stop_loss, take_profit, jumlah_crypto))
        monitor_thread.start()
        monitor_thread.join()

    def monitor_price(self, stop_loss, take_profit, jumlah_crypto):
        try:
            while self.running:
                harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
                self.riwayat_harga.append((datetime.now(), harga_sekarang))
                logging.info("Harga Sekarang: %s | Stop Loss: %s | Take Profit: %s", harga_sekarang, stop_loss, take_profit)
                print(f"\n[EKSEKUSI] Waktu: {datetime.now().strftime('%H:%M:%S')} | Harga Sekarang: {harga_sekarang}")

                if harga_sekarang >= take_profit:
                    self.status = "✅ Take Profit Tercapai"
                    logging.info("Take Profit tercapai pada harga %s. Menjual aset...", harga_sekarang)
                    print(f"[✅] Take Profit Tercapai pada harga {harga_sekarang}! Menjual aset...")
                    self.sell_trade(harga_sekarang, jumlah_crypto)
                    self.running = False
                elif harga_sekarang <= stop_loss:
                    self.status = "❌ Stop Loss Terpenuhi"
                    logging.info("Stop Loss tercapai pada harga %s. Menjual aset...", harga_sekarang)
                    print(f"[❌] Stop Loss Terpenuhi pada harga {harga_sekarang}! Menjual aset...")
                    self.sell_trade(harga_sekarang, jumlah_crypto)
                    self.running = False
                else:
                    print("[⏳] Harga belum mencapai Take Profit atau Stop Loss...")
                time.sleep(2)
        except Exception as e:
            logging.error("Error dalam monitor_price: %s", e)

    def sell_trade(self, harga_jual, jumlah_crypto):
        try:
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
            response = self.api.send_request(order_payload, headers) if hasattr(self.api, "send_request") else None
            if response is None:
                logging.error("Fungsi send_request tidak tersedia di API.")
                print("[❌] Order jual gagal karena fungsi send_request tidak tersedia.")
                return
            result = response.json()
            if result["success"] == 1:
                logging.info("Order jual berhasil pada harga %s.", harga_jual)
                print("[✅] Order jual berhasil! Saldo telah diperbarui.")
            else:
                logging.error("Order jual gagal pada harga %s. Respon: %s", harga_jual, result)
                print("[❌] Order jual gagal! Periksa saldo dan API.")
        except Exception as e:
            logging.error("Error dalam sell_trade: %s", e)
            print("[❌] Terjadi kesalahan saat mencoba menjual aset.")

if __name__ == "__main__":
    api = IndodaxAPI()
    bot = TradingBotAI(api)
    bot.execute_trade()
