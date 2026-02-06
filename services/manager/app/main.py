from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from services.manager.app.routes.health import router as health_router
from services.manager.app.routes.request import router as request_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Manager Service", version="1.0.0", lifespan=lifespan)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(health_router)
app.include_router(request_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
