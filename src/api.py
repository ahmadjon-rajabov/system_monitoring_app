from fastapi import FastAPI
from src.database import DatabaseManager
from src.predictor import Predictor

app = FastAPI()
db = DatabaseManager()
predictor = Predictor()

@app.get("/")
def root():
    """
    A simple check to see server status
    """
    return {"message": "System Monitor API is Online !!!"}

@app.get("/metrics")
def get_metrics(limit: int = 10):
    """
    Returns the latest system stats
    """
    data = db.get_recent_metrics(limit=limit)
    return {"count": len(data), "data": data}

@app.get("/predict")
def get_prediction():
    """
    Asks the AI to forecast the next CPU load
    """
    cpu_prediction, status = predictor.predict_next_minute()

    return {
        "status": status,
        "predicted_cpu_load": cpu_prediction
    }