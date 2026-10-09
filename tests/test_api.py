import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home():
	response = client.get("/")
	assert response.status_code == 200

def test_health():
	response = client.get("/health")
	assert response.status_code == 200
	assert "status" in response.json()

def test_system_metrics():
	response = client.get("/api/v1/system")
	assert response.status_code == 200
	assert isinstance(response.json(), dict)

def test_prometheus_metrics():
	response = client.get("/metrics")
	assert response.status_code == 200
	assert "platform_cpu_usage_percent" in response.text


