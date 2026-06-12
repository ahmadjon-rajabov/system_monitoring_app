from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "System Monitor API is Online !!!"}

def test_get_metrics(mocker):
    mocker.patch('src.api.db.get_recent_metrics', return_value=[{"cpu": 50.0, "network": 2.5}])

    response = client.get("/metrics?limit=1")
    assert response.status_code == 200
    assert response.json() == {"count": 1, "data": [{"cpu": 50.0, "network": 2.5}]}

def test_get_prediction(mocker):
    mocker.patch('src.api.predictor.predict_next_minute', return_value=({"cpu": 60.0, "network": 3.0}, "Success"))

    response = client.get("/predict")
    assert response.status_code == 200
    assert response.json() == {"status": "Success", "cpu": 60.0, "network": 3.0}

def test_get_system_info(mocker):
    mocker.patch('src.api.psutil.cpu_count', return_value=8)
    
    response = client.get("/system")
    assert response.status_code == 200
    assert response.json()["cpu_cores"] == 8

def test_chat_ai(mocker):
    mocker.patch('src.api.rag_agent.ask', return_value="Scaling up the cluster.")
    
    response = client.post("/chat", json={"question": "We have high traffic!"})
    assert response.status_code == 200
    assert response.json() == {"answer": "Scaling up the cluster."}

def test_config_mode(mocker):
    mocker.patch('src.api.db.get_config', return_value="manual")
    mocker.patch('src.api.db.set_config')

    res_get = client.get("/config/mode")
    assert res_get.status_code == 200
    assert res_get.json() == {"mode": "manual"}

    res_post = client.post("/config/mode", json={"value": "auto"})
    assert res_post.status_code == 200
    assert res_post.json() == {"status": "updated", "mode": "auto"}

    res_invalid = client.post("/config/mode", json={"value": "broken_mode"})
    assert res_invalid.json() == {"error": "Invalid mode, Use 'auto' or 'manual'"}