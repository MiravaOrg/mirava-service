from fastapi import Request, Response, APIRouter
from fastapi.responses import StreamingResponse
import httpx
import logging

from .base import stream_bytes, clean_headers
from .mirrors import registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Docker Registry"])


async def proxy_docker_request(
    client: httpx.AsyncClient, method: str, path: str, headers: dict, body: bytes = None
):
    """Proxy Docker request through mirrors"""

    manager = registry.get("docker")

    for mirror in manager.get_healthy_mirrors():
        url = f"{mirror.url}{path}"
        request_headers = clean_headers(headers)

        try:
            logger.info(f"[{mirror.name}] {method} {path}")

            if method == "HEAD":
                response = await client.head(url, headers=request_headers)
            elif method == "GET":
                response = await client.get(url, headers=request_headers)
            elif method == "POST":
                response = await client.post(url, headers=request_headers, content=body)
            else:
                continue

            if response.status_code == 401:
                logger.info(f"[{mirror.name}] Auth required")
            elif response.status_code >= 500:
                logger.warning(f"[{mirror.name}] Server error: {response.status_code}")
                await manager.mark_failure(mirror, f"HTTP {response.status_code}")
                continue
            elif response.status_code >= 400:
                pass  # Client errors are valid
            else:
                mirror.failure_count = 0

            # Clean response headers
            response_headers = {
                k: v
                for k, v in response.headers.items()
                if k.lower()
                not in ["transfer-encoding", "content-encoding", "connection"]
            }

            logger.info(f"[{mirror.name}] Success: {response.status_code}")

            if method == "HEAD":
                return Response(
                    content=b"",
                    status_code=response.status_code,
                    headers=response_headers,
                )

            return StreamingResponse(
                content=stream_bytes(response.content),
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type"),
            )

        except Exception as e:
            logger.warning(f"[{mirror.name}] Error: {str(e)[:100]}")
            await manager.mark_failure(mirror, str(e))
            continue

    from fastapi import HTTPException

    raise HTTPException(status_code=502, detail="All Docker mirrors failed")


@router.api_route("/v2/", methods=["GET", "HEAD"])
async def docker_v2_root(request: Request):
    """Docker v2 API root"""
    client = request.app.state.client
    headers = dict(request.headers)
    headers.pop("host", None)
    return await proxy_docker_request(client, request.method, "/v2/", headers)


@router.api_route("/v2/{path:path}", methods=["GET", "HEAD", "POST"])
async def docker_v2_proxy(request: Request, path: str):
    """Docker v2 API proxy"""
    client = request.app.state.client
    method = request.method
    headers = dict(request.headers)
    body = await request.body() if method in ["POST", "PUT"] else None
    headers.pop("host", None)
    return await proxy_docker_request(client, method, f"/v2/{path}", headers, body)
