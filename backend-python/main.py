from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Python Microservice API")

# Configurar CORS para permitir que el frontend se comunique con este servicio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Microservice"}

@app.get("/api/ai/status")
def read_status():
    return {
        "service": "FastAPI ML Service",
        "status": "online",
        "models_loaded": 3
    }
