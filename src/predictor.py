import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from src.database import DatabaseManager

class Predictor:
    def __init__(self):
        self.db = DatabaseManager()
        self.models = {
            "Linear": LinearRegression(),
            "RandomForest": RandomForestRegressor(n_estimators=50, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(n_estimators=50, random_state=42)
        }
    
    def train_predict(self, df, target_col):
        """
        Helper function: Trains all 3 models on a specific target (cpu or network)
        and returns their predictions
        """
        # Feature engineering, the "Context"
        df['prev'] = df[target_col].shift(1)
        df['rolling'] = df[target_col].rolling(window=5).mean()
        df['velocity'] = df[target_col].diff()

        df = df.dropna() # Remove empty rows created by shifting

        if len(df) < 10:
            return None
        
        # Preparetion X (features), y (target)
        X = df[['prev', 'rolling', 'velocity']].values
        y = df[target_col].values

        predictions = {}
        
        # Train and predict for each model
        last_row = df.iloc[-1]
        next_input = [[
            last_row[target_col],   # current val becomes 'prev'
            last_row['rolling'],    # current rolling
            last_row['velocity']    # current velocity
        ]]

        for name, model in self.models.items():
            try:
                model.fit(X,y)
                pred = model.predict(next_input)[0]
                # Cap results, cpu 0-100, network 0-infinit
                if target_col == 'cpu':
                    pred = max(0, min(100, pred))
                else:
                    pred = max(0, pred)
                
                predictions[name] = round(pred, 2)
            except Exception as e:
                predictions[name] = 0.0
                print(f"Error in {name}: {e}")
        return predictions

    def predict_next_minute(self):
        """
        Orchestrator: Gets data and runs predictions for both CPU and Network.
        """
        data = self.db.get_recent_metrics(limit=120) # 4 minutes of history

        if len(data) < 20:
            return None, "Gathering more data for AI models..."
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        cpu_preds = self.train_predict(df, 'cpu')
        net_preds = self.train_predict(df, 'network')

        if not cpu_preds or not net_preds:
            return None, "Insufficient Data to make Predictions"
        
        return {
            "cpu": cpu_preds,
            "network": net_preds
        }, "Prediction Successful"