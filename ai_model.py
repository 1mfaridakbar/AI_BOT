import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

class PricePredictor:
    def __init__(self, pair="btcidr", model_file=None):
        self.pair = pair
        self.filename = f"historical_data_{self.pair}.csv"
        self.model_file = model_file if model_file else f"price_predictor_{self.pair}.pkl"
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def is_model_trained(self):
        return os.path.exists(self.model_file)

    def load_data(self):
        if not os.path.exists(self.filename):
            print(f"[⚠️] Data historis tidak ditemukan untuk {self.pair}.")
            return None
        df = pd.read_csv(self.filename)

        # **Pastikan data tidak kosong**
        if df.empty or len(df) < 10:
            print(f"[⚠️] Data historis terlalu sedikit ({len(df)} data), tidak bisa melatih model AI.")
            return None

        df['target'] = df['price'].shift(-1)  # Prediksi harga berikutnya
        df.dropna(inplace=True)
        return df

    def train_model(self):
        df = self.load_data()
        if df is None:
            print(f"[❌] Tidak ada data yang cukup untuk melatih model AI pada {self.pair}.")
            return
        
        X = df[['price']]
        y = df['target']

        # **Cegah error jika data terlalu sedikit**
        if len(X) < 10:
            print(f"[⚠️] Jumlah data terlalu sedikit ({len(X)} sampel), tidak cukup untuk melatih model.")
            return

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model.fit(X_train, y_train)
        print(f"📊 Model training complete untuk {self.pair}. Score: {self.model.score(X_test, y_test)}")

        joblib.dump(self.model, self.model_file)
        print(f"✅ Model telah disimpan sebagai `{self.model_file}`")

    def predict_price(self, current_price):
        if not self.is_model_trained():
            print(f"[⚠️] Model AI belum tersedia untuk {self.pair}, mencoba melatih model...")
            self.train_model()
            if not self.is_model_trained():  # Jika tetap gagal, hentikan prediksi
                print(f"[❌] Gagal melatih model AI, tidak bisa melakukan prediksi.")
                return None
        self.model = joblib.load(self.model_file)
        return self.model.predict([[current_price]])[0]
