import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from api_utils import IndodaxAPI

class PricePredictor:
    def __init__(self, api, pair="btcidr", model_file=None):
        self.api = api
        self.pair = pair
        self.model_file = model_file if model_file else f"price_predictor_{self.pair}.pkl"
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def is_model_trained(self):
        return os.path.exists(self.model_file)

    def get_market_data(self):
        """Mengambil data harga real-time dari Market API"""
        df = self.api.get_ticker(self.pair)
        if df is None or df.empty:
            print(f"[⚠️] Tidak bisa mendapatkan data pasar untuk {self.pair}.")
            return None

        df = df.sort_values(by=['date']).reset_index(drop=True)
        df['target'] = df['price'].shift(-1)  # Prediksi harga berikutnya
        df.dropna(inplace=True)
        return df

    def train_model(self):
        """Melatih model berdasarkan data real-time dari Market API"""
        df = self.get_market_data()
        if df is None or len(df) < 10:
            print(f"[❌] Data pasar tidak cukup untuk melatih model AI ({len(df)} data).")
            return

        X = df[['price']]
        y = df['target']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)

        print(f"📊 Model training complete untuk {self.pair}. Score: {self.model.score(X_test, y_test)}")

        # **Simpan hanya model, tanpa feature_names**
        joblib.dump(self.model, self.model_file)
        print(f"✅ Model telah disimpan sebagai `{self.model_file}`")

    def predict_price(self, current_price):
        """Memastikan model sudah dilatih sebelum prediksi"""
        if not self.is_model_trained():
            print(f"[⚠️] Model AI belum tersedia untuk {self.pair}, mencoba melatih model...")
            self.train_model()
            if not self.is_model_trained():
                print(f"[❌] Gagal melatih model AI, tidak bisa melakukan prediksi.")
                return None

        # **Pastikan hanya memuat model, tidak ada unpacking yang salah**
        self.model = joblib.load(self.model_file)

        # **Gunakan DataFrame agar sesuai dengan fitur yang digunakan**
        df = pd.DataFrame([[current_price]], columns=["price"])
        return self.model.predict(df)[0]

if __name__ == "__main__":
    api = IndodaxAPI()
    predictor = PricePredictor(api)
    predictor.train_model()
