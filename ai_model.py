import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from api_utils import IndodaxAPI
import logging

# Konfigurasi Logging
logging.basicConfig(filename='ai_model_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PricePredictor:
    def __init__(self, api, pair="btcidr"):
        self.api = api
        self.pair = pair
        self.model_file = f"price_predictor_{self.pair}.pkl"
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
        df['target'] = df['price'].shift(-1)
        df.dropna(inplace=True)
        return df

    def train_model(self):
        df = self.get_market_data()
        if df is None or len(df) < 10:
            print(f"[❌] Data pasar tidak cukup untuk melatih model AI ({len(df)} data).")
            return

        X = df[['price', 'RSI', 'SMA', 'BB_Upper', 'BB_Lower']]
        y = df['target']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20, 30]
        }
        grid_search = GridSearchCV(RandomForestRegressor(random_state=42), param_grid, cv=3)
        grid_search.fit(X_train, y_train)

        self.model = grid_search.best_estimator_

        print(f"📊 Model training complete untuk {self.pair}. Score: {self.model.score(X_test, y_test)}")
        logging.info(f"Model AI dilatih untuk {self.pair} dengan score: {self.model.score(X_test, y_test)}")

        joblib.dump(self.model, self.model_file)
        print(f"✅ Model telah disimpan sebagai `{self.model_file}`")

    def predict_price(self, current_price):
        if not self.is_model_trained():
            print(f"[⚠️] Model AI belum tersedia untuk {self.pair}, mencoba melatih model...")
            self.train_model()
            if not self.is_model_trained():
                print(f"[❌] Gagal melatih model AI, tidak bisa melakukan prediksi.")
                return None

        self.model = joblib.load(self.model_file)
        df = pd.DataFrame([[current_price]], columns=["price"])
        return self.model.predict(df)[0]

if __name__ == "__main__":
    api = IndodaxAPI()
    predictor = PricePredictor(api)
    predictor.train_model()
