import time
import logging
from datetime import datetime
import threading
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from ai_model import PricePredictor
from data_collector import DataCollector
from ta.volatility import AverageTrueRange

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

    def calculate_atr(self):
        # Menghitung ATR untuk pengaturan Stop Loss dan Take Profit dinamis
        df = self.api.get_ticker(self.pair)
        atr_indicator = AverageTrueRange(df['high'], df['low'], df['close'], window=14)
        return atr_indicator.average_true_range()[-1]

    def execute_trade(self):
        self.ensure_model()
        analysis = self.analysis.analyze()
        harga_beli = analysis['price']

        atr_value = self.calculate_atr()
        stop_loss = harga_beli - (atr_value * self.stop_loss_pct)
        take_profit = harga_beli + (atr_value * self.take_profit_pct)

        print(f"Stop Loss: {stop_loss} | Take Profit: {take_profit}")
        
        # Implementasi trailing stop
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_price, args=(stop_loss, take_profit))
        monitor_thread.start()
        monitor_thread.join()

    def monitor_price(self, stop_loss, take_profit):
        while self.running:
            harga_sekarang = self.api.get_ticker(self.pair)['price'].iloc[-1]
            if harga_sekarang >= take_profit:
                print(f"[✅] Take Profit Tercapai di harga {harga_sekarang}!")
                self.running = False
            elif harga_sekarang <= stop_loss:
                print(f"[❌] Stop Loss Terpenuhi di harga {harga_sekarang}!")
                self.running = False
            time.sleep(2)
