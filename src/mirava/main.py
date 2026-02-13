from contextlib import asynccontextmanager
import httpx
import logging
from fastapi import FastAPI

try:
    from .mirrors import init_mirrors, registry
    from . import docker, pypi
except ImportError:
    from .mirrors import init_mirrors, registry


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage shared httpx client"""
    app.state.client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
        follow_redirects=True,
        http2=False,
    )
    logger.info("HTTP client initialized")
    init_mirrors()
    yield
    await app.state.client.aclose()
    logger.info("HTTP client closed")


def create_app() -> FastAPI:
    """Application factory"""
    app = FastAPI(
        title="Universal Mirror Proxy",
        description="FastAPI-based proxy for Docker registry, PyPI, and more",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.include_router(docker.router)
    app.include_router(pypi.router)

    @app.get("/")
    async def root():
        managers = registry.list_managers()
        return {
            "service": "Universal Mirror Proxy",
            "version": "2.0.0",
            "mirror_types": list(managers.keys()),
            "total_mirrors": sum(len(m.mirrors) for m in managers.values()),
            "endpoints": {
                "docker_v2": "/v2/",
                "pypi_simple": "/simple/{package}/",
                "docs": "/docs",
                "health": "/health",
            },
        }

    @app.get("/health")
    async def health_check():
        import time

        managers = registry.list_managers()
        result = {"timestamp": time.time()}

        for name, manager in managers.items():
            result[name] = {
                "total": len(manager.mirrors),
                "healthy": len(
                    [m for m in manager.mirrors if m.health.value == "healthy"]
                ),
                "mirrors": [
                    {
                        "name": m.name,
                        "url": m.url,
                        "health": m.health.value,
                        "failures": m.failure_count,
                    }
                    for m in manager.mirrors
                ],
            }
        return result

    @app.post("/mirrors/{mirror_type}")
    async def add_mirror(mirror_type: str, url: str, name: str, priority: int = 50):
        try:
            manager = registry.get(mirror_type)
            manager.add_mirror(url, name, priority)
            return {"status": "added", "type": mirror_type, "name": name, "url": url}
        except KeyError:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Unknown mirror type: {mirror_type}"
            )

    return app


# For direct execution
if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
