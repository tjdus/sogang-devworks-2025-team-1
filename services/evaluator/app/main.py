from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from services.evaluator.app.routes.health import router as health_router
from services.evaluator.app.routes.evaluate import router as evaluate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Evaluator Service", version="1.0.0", lifespan=lifespan)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(health_router)
app.include_router(evaluate_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
