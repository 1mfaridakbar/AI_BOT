import requests
import time
import json
import pandas as pd
import ta
from datetime import datetime
from api_utils import IndodaxAPI
from analysis import TechnicalAnalysis
from simulation import SimulationBotAI
from execute import TradingBot  # Tambahkan impor TradingBot

api = IndodaxAPI()

# Fungsi utama untuk menampilkan saldo dan kontrol trading
def main():
    saldo = api.get_balance()
    print(f"Saldo IDR: {saldo['idr']}" if saldo else "Gagal mengambil saldo!")
    
    while True:
        print("\n1. Simulasi Trading")
        print("2. Eksekusi Trading dengan Manajemen Risiko")
        print("3. Keluar")
        pilihan = input("Pilih opsi: ")
        
        if pilihan == "1":
            bot = SimulationBotAI(api=api)
            bot.simulate_trade()
        elif pilihan == "2":
            trading_bot = TradingBot(api=api)  # Buat instance TradingBot
            trading_bot.execute_trade()  # Jalankan eksekusi trading
        elif pilihan == "3":
            break
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()
