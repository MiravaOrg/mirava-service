from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
import httpx
import logging

from .mirrors import registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["PyPI"])


@router.get("/simple/{package_name}/")
async def pypi_package_proxy(request: Request, package_name: str):
    """PyPI package proxy with mirror fallback"""
    client = request.app.state.client
    manager = registry.get("pypi")

    for mirror in manager.get_healthy_mirrors():
        target_url = f"{mirror.url}/{package_name}/"
        logger.info(f"[{mirror.name}] PyPI: {package_name}")

        try:
            response = await client.get(target_url, follow_redirects=True)

            if response.status_code == 200:
                logger.info(f"[{mirror.name}] Serving '{package_name}'")
                return StreamingResponse(
                    response.aiter_bytes(),
                    status_code=200,
                    media_type=response.headers.get("content-type", "text/html"),
                    headers={"X-Served-By": mirror.name},
                )
            elif response.status_code >= 500:
                await manager.mark_failure(mirror, f"HTTP {response.status_code}")
                continue

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning(f"[{mirror.name}] Failed: {exc}")
            await manager.mark_failure(mirror, str(exc))
            continue

    raise HTTPException(
        status_code=404, detail=f"Package '{package_name}' not found on any mirrors"
    )
