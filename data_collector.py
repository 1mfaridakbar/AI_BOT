import pandas as pd
import os
from api_utils import IndodaxAPI

class DataCollector:
    def __init__(self, api, pair="btcidr"):
        self.api = api
        self.pair = pair
        self.filename = f"historical_data_{self.pair}.csv"

    def log_transaction(self, action, price, jumlah_crypto, profit_loss=None, profit_loss_pct=None):
        data = {
            "timestamp": pd.Timestamp.now(),
            "pair": self.pair,
            "action": action,
            "price": price,
            "jumlah_crypto": jumlah_crypto,
            "profit_loss": profit_loss,
            "profit_loss_pct": profit_loss_pct
        }
        
        df = pd.DataFrame([data])
        if not os.path.exists(self.filename):
            df.to_csv(self.filename, index=False)
        else:
            df.to_csv(self.filename, mode='a', header=False, index=False)

        print(f"📌 Data transaksi {action} dicatat dalam {self.filename}")

    def get_historical_data(self):
        if os.path.exists(self.filename):
            return pd.read_csv(self.filename)
        else:
            print(f"[⚠️] Tidak ada data historis untuk {self.pair}.")
            return None
