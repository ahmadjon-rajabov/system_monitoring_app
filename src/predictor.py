import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from src.database import DatabaseManager

class Predictor:
    def __init__(self):
        self.db = DatabaseManager()
    
    def predict_next_minute(self):
        """
        Analyzes recent history to predict next CPU load
        """
        data = self.db.get_recent_metrics(limit=60)

        if len(data) < 10:
            return None, "Note enough data to predict (Need at least 10 points)"
        
        df = pd.DataFrame(data)
        # Index (0, 1, 2...) as our "Time" variable (X axis)
        # CPU usage as target (Y axis)
        df = df.iloc[::-1].reset_index(drop=True)
        x = df.index.values.reshape(-1, 1) # Time steps [[0], [1], [2]...]
        y = df['cpu'].values

        model = LinearRegression()
        model.fit(x, y)

        next_step = np.array([[len(df)]]) # Next number in the sequence
        prediction = model.predict(next_step)

        return round(prediction[0], 2), "Prediction Successful"