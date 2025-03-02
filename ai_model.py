import pandas as pd
import numpy as np
import joblib
import os
import sqlite3
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
import logging
import ta

# Konfigurasi Logging
logging.basicConfig(filename='ai_model_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PricePredictor:
    def __init__(self, api, pair="btcidr"):
        self.api = api
        self.pair = pair
        self.model_file = f"price_predictor_{self.pair}.pkl"
        self.db_file = "historical_data.db"
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.feature_names = ["price", "RSI", "SMA", "BB_Upper", "BB_Lower", "price_change_3d", "price_change_7d", "price_change_30d"]

    def is_model_trained(self):
        return os.path.exists(self.model_file)

    def save_to_db(self, df):
        conn = sqlite3.connect(self.db_file)
        df.to_sql('historical_data', conn, if_exists='append', index=False)
        conn.close()

    def update_historical_data(self):
        """Mengupdate data historis dengan harga terbaru dan indikator teknikal"""
        df_new = self.api.get_ticker(self.pair)
        if df_new is None or df_new.empty:
            print(f"[⚠️] Tidak bisa mendapatkan data pasar untuk {self.pair}.")
            return

        df_new = df_new.sort_values(by=['date']).reset_index(drop=True)
        df_new = self.calculate_indicators(df_new)
        self.save_to_db(df_new)
        print(f"[📊] Data historis untuk {self.pair} diperbarui.")

    def calculate_indicators(self, df):
        """Menghitung indikator teknikal seperti RSI, SMA, dan Bollinger Bands"""
        df['RSI'] = ta.momentum.RSIIndicator(df['price'], window=14).rsi()
        df['SMA'] = ta.trend.SMAIndicator(df['price'], window=20).sma_indicator()
        df['BB_Upper'] = ta.volatility.BollingerBands(df['price'], window=20).bollinger_hband()
        df['BB_Lower'] = ta.volatility.BollingerBands(df['price'], window=20).bollinger_lband()

        # Tambahkan indikator perubahan harga
        df['price_change_3d'] = df['price'].pct_change(periods=3)
        df['price_change_7d'] = df['price'].pct_change(periods=7)
        df['price_change_30d'] = df['price'].pct_change(periods=30)

        df.dropna(inplace=True)  # Hapus baris dengan nilai NaN akibat perhitungan indikator
        return df

    def get_market_data(self):
        """Menggunakan data historis untuk pelatihan AI"""
        conn = sqlite3.connect(self.db_file)
        df = pd.read_sql('SELECT * FROM historical_data', conn)
        conn.close()

        if df is None or len(df) < 50:
            print(f"[❌] Data pasar tidak cukup untuk melatih model AI ({len(df)} data).")
            return None

        df = df.sort_values(by=['date']).reset_index(drop=True)
        df['target'] = df['price'].shift(-1)

        df = self.calculate_indicators(df)  # Pastikan indikator teknikal sudah dihitung
        return df

    def train_model(self):
        df = self.get_market_data()
        if df is None:
            return

        X = df[self.feature_names]  # Pastikan hanya menggunakan fitur yang sesuai
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

        # Simpan model bersama dengan feature names yang digunakan
        joblib.dump((self.model, self.feature_names), self.model_file)
        print(f"✅ Model telah disimpan sebagai `{self.model_file}`")

    def predict_price(self, current_price, rsi, sma, bb_upper, bb_lower, change_3d, change_7d, change_30d):
        if not self.is_model_trained():
            self.train_model()
            if not self.is_model_trained():
                return None

        # Load model beserta feature names yang digunakan
        self.model, self.feature_names = joblib.load(self.model_file)

        # Pastikan hanya menggunakan fitur yang sesuai dengan model
        df = pd.DataFrame([[current_price, rsi, sma, bb_upper, bb_lower, change_3d, change_7d, change_30d]],
                          columns=self.feature_names)
        
        return self.model.predict(df)[0]

if __name__ == "__main__":
    api = IndodaxAPI()
    predictor = PricePredictor(api)
    predictor.update_historical_data()
    predictor.train_model()
