from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.transactions import router as transaction_router
from backend.app.api.routes.investigations import router as investigation_router
from backend.app.api.routes.customers import router as customer_router
from backend.app.api.routes.merchants import router as merchant_router
from backend.app.api.routes.evaluations import router as evaluation_router
from backend.app.api.routes.demo import router as demo_router

app = FastAPI(
    title="RakshaAI",
    description="AI-powered fraud investigation and risk analysis API",
    version="0.1.0",
)

# Allow CORS for React/Vite frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "RakshaAI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(transaction_router)
app.include_router(investigation_router)
app.include_router(customer_router)
app.include_router(merchant_router)
app.include_router(evaluation_router)
app.include_router(demo_router)