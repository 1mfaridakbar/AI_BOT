import pandas as pd
import os
from api_utils import IndodaxAPI
import sqlite3

class DataCollector:
    def __init__(self, api, pair="btcidr"):
        self.api = api
        self.pair = pair
        self.db_file = f"historical_data_{self.pair}.db"

    def log_transaction(self, action, price, jumlah_crypto, profit_loss=None, profit_loss_pct=None):
        # Simpan transaksi ke dalam database SQLite untuk pencatatan riwayat
        data = {
            "timestamp": pd.Timestamp.now(),
            "pair": self.pair,
            "action": action,
            "price": price,
            "jumlah_crypto": jumlah_crypto,
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct
        }

        conn = sqlite3.connect(self.db_file)
        df = pd.DataFrame([data])
        df.to_sql('transactions', conn, if_exists='append', index=False)
        conn.close()

        print(f"📌 Data transaksi {action} dicatat dalam database.")

    def get_historical_data(self):
        conn = sqlite3.connect(self.db_file)
        df = pd.read_sql('SELECT * FROM transactions', conn)
        conn.close()

        if df is None or len(df) == 0:
            print(f"[⚠️] Tidak ada data historis untuk {self.pair}.")
            return None

        return df
