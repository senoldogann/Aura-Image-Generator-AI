import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add backend to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_engine, GPU_SEMAPHORE
from sd_engine import StableDiffusionEngine

# Mock Semaphore globally and cleaner task
mock_cleaner = AsyncMock()
app.dependency_overrides[get_engine] = lambda: MockEngine()

# We need to ensure startup logic doesn't start the real cleaner or hangs
# We can patch the function in main module BEFORE client usage if possible, 
# but client might have already imported app.
# Better to patch it inside the test or use a fixture for client.

@pytest.fixture
def client_fixture():
     # Patch the background task to do nothing
     with patch("main.ephemeral_cleaner_task", new_callable=AsyncMock) as mock_clean:
         with TestClient(app) as c:
             yield c

client = TestClient(app) # Fallback for existing tests, but let's update them to use fixture if possible.
# Actually, let's just patch it at module level if we can, or just update the tests.


# Mock Engine
class MockEngine:
    def __init__(self):
        self.device = "cpu"
        self.total_steps = 0
        self.current_step = 0
    
    def generate_and_save(self, **kwargs):
        print(f"Mock Generate called with: {kwargs}")
        return True
    
    def upscale_image(self, image_path, prompt):
        print(f"Mock Upscale called for: {image_path}")
        return image_path.replace(".png", "_upscaled.png")

    def add_watermark(self, image_path, text):
        return image_path.replace(".png", "_watermarked.png")

@pytest.fixture
def mock_engine():
    engine = MockEngine()
    # verify generate_and_save is called
    engine.generate_and_save = MagicMock(return_value=True)
    engine.upscale_image = MagicMock(return_value="path/to/upscaled.png")
    return engine

@pytest.fixture
def override_get_engine(mock_engine):
    app.dependency_overrides[get_engine] = lambda: mock_engine
    yield
    app.dependency_overrides = {}

@pytest.fixture
def test_client():
    # Patch the background task to do nothing
    with patch("main.ephemeral_cleaner_task", new_callable=AsyncMock):
        with TestClient(app) as c:
             yield c

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_flow(test_client, override_get_engine, mock_engine):
    payload = {
        "prompt": "a test prompt",
        "model_key": "realistic",
        "aspect_ratio": "1:1"
    }
    
    # Patching os.path.exists to True so main.py thinks saving worked
    # AND Patching GPU_SEMAPHORE to avoid async loop issues in TestClient
    mock_sem = AsyncMock()
    mock_sem.__aenter__.return_value = None
    mock_sem.__aexit__.return_value = None
    
    with patch("main.GPU_SEMAPHORE", mock_sem), \
         patch("os.path.exists", return_value=True):
        response = test_client.post("/generate", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "generated_" in data["image_url"]
    
    # Verify engine call
    mock_engine.generate_and_save.assert_called_once()
    args = mock_engine.generate_and_save.call_args[1]
    assert "test prompt" in args["prompt"]

def test_auto_upscale_flow(test_client, override_get_engine, mock_engine):
    payload = {
        "prompt": "a test prompt",
        "model_key": "realistic",
        "auto_upscale": True
    }
    
    mock_sem = AsyncMock()
    mock_sem.__aenter__.return_value = None
    mock_sem.__aexit__.return_value = None
    
    # Patching os.path.exists ensures logic proceeds to upscale
    with patch("main.GPU_SEMAPHORE", mock_sem), \
         patch("os.path.exists", return_value=True):
        response = test_client.post("/generate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify upscale was called
    mock_engine.upscale_image.assert_called_once()

def test_get_images_empty(test_client):
    # Mock os.listdir to return empty
    with patch("os.listdir", return_value=[]):
        response = test_client.get("/images")
        assert response.status_code == 200
        assert response.json()["images"] == []
