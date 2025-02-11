import requests
import time
import json
import pandas as pd
import ta
from datetime import datetime
from api_utils import get_balance, get_ticker, execute_trade
from analysis import technical_analysis
from simulation import simulate_trade

# Fungsi utama untuk menampilkan saldo dan kontrol trading
def main():
    saldo = get_balance()
    print(f"Saldo IDR: {saldo['idr']}" if saldo else "Gagal mengambil saldo!")
    
    while True:
        print("\n1. Simulasi Trading")
        print("2. Eksekusi Trading dengan Manajemen Risiko")
        print("3. Keluar")
        pilihan = input("Pilih opsi: ")
        
        if pilihan == "1":
            simulate_trade()
        elif pilihan == "2":
            execute_trade()  # Memanggil fungsi eksekusi trading yang telah diperbarui
        elif pilihan == "3":
            break
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()