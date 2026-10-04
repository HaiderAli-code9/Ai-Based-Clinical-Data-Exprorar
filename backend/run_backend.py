import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(backend_dir, "app")
sys.path.insert(0, app_dir)
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    from app import app

    print("[INFO] Starting ClinData Explorer FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
