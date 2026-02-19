from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel  # For POST request body
from src.database import DatabaseManager
from src.predictor import Predictor
from src.rag_agent import RagAgent
import platform, psutil, os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

db = DatabaseManager()
predictor = Predictor()
rag_agent = RagAgent()

# Data shape for the chat request
class ChatReqeust(BaseModel):
    question: str

@app.post("/chat")
def chat_ai(request: ChatReqeust):
    """
    Sends user question + DB context to Gemini
    """
    answer = rag_agent.ask(request.question)
    return {"answer": answer}

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
    Asks the AI to forecast the next CPU and Network load
    """
    predictions, status = predictor.predict_next_minute()

    if predictions is None:
        return {"status": status, "cpu": None, "network": None}

    return {
        "status": status,
        "cpu": predictions['cpu'],
        "network": predictions['network']
    }

@app.get("/system")
def get_system_info():
    """
    Returns static info about host machine
    """
    system_os = platform.system()
    disk_path = '/'

    if system_os == 'Windows':
        disk_path = 'C:\\'
    elif system_os == 'Darwin':
        if os.path.exists('/System/Volumes/Data'):
            disk_path = '/System/Volumes/Data'

    try:
        disk_info = psutil.disk_usage(disk_path)
    except Exception as e:
        print(f"Disk check failed for {disk_path}, falling back to current directory")
        disk_info = psutil.disk_usage('.')

    return{
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_arch": platform.machine(),
        "cpu_cores": psutil.cpu_count(logical=True),
        "ram_total": round(psutil.virtual_memory().total / (1024 ** 3), 2), # Bytes to GB
        "disk_total": round(disk_info.total / (1024 ** 3), 2),
        "disk_used": round(disk_info.used / (1024 ** 3), 2),
        "python_version": platform.python_version()
    }