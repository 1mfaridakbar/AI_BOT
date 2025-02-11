import pandas as pd
import ta
from api_utils import IndodaxAPI

class TechnicalAnalysis:
    def __init__(self, api, pair="btcidr"):
        self.api = api
        self.pair = pair

    def analyze(self):
        df = self.api.get_ticker(self.pair)
        df = df.sort_values(by=['date']).reset_index(drop=True)
        df['RSI'] = ta.momentum.RSIIndicator(df['price'], window=14).rsi()
        df['SMA'] = ta.trend.SMAIndicator(df['price'], window=20).sma_indicator()
        bb = ta.volatility.BollingerBands(df['price'], window=20)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()
        return df.iloc[-1]
