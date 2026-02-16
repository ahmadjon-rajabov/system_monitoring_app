import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from src.database import DatabaseManager

class Predictor:
    def __init__(self):
        self.db = DatabaseManager()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    def predict_next_minute(self):
        """
        Analyzes recent history to predict next CPU load
        """
        data = self.db.get_recent_metrics(limit=120) # 4 minutes of history

        if len(data) < 20:
            return None, "Gathering more data for AI..."
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # raw value, predict Y (future) based on X (past)
        df['prev_cpu'] = df['cpu'].shift(1)
        
        # smooth out the noise
        df['rolling_avg'] = df['cpu'].rolling(window=5).mean()

        # velocity, is it going up or down
        df['velocity'] = df['cpu'].diff()

        #drop first few rows that have NaN, because of shifting
        df = df.dropna()

        if len(df) < 10:
            return None, "Not enough clean data..."
        
        # We train the model: "Given these stats at time T, what was the CPU at T?"
        # Ideally, for forecasting, we would shift Y, but for this simple 
        # real-time demo, mapping patterns to current state is a good proxy 
        # for the immediate next step trend.

        features = ['prev_cpu', 'rolling_avg', 'velocity']
        X = df[features].values
        y = df['cpu'].values

        self.model.fit(X, y)

        # predict next second (input features), based on latest available data
        last_row = df.iloc[-1]
        next_input = [[
            last_row['cpu'],    # new 'prev_cpu
            last_row['rolling_avg'], # current avg
            last_row['velocity']    # current speed
        ]]
        prediction = self.model.predict(next_input)
        result = max(0, min(100, prediction[0]))

        return round(result, 2), "AI Analysis Successful"