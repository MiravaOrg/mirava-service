from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import httpx
import logging

logging.basicConfig(level=logging.INFO)

# Configuration: Mirrors prioritized by list order
MIRRORS = [
    {"name": "runflare", "url": "https://mirror-pypi.runflare.com/simple"},
    {"name": "pypi", "url": "https://pypi.org/simple"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=5.0)
    yield
    await app.state.client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/simple/{package_name}/")
async def route_manager(package_name: str):
    client: httpx.AsyncClient = app.state.client

    for mirror in MIRRORS:
        target_url = f"{mirror['url']}/{package_name}/"
        logging.info(f"Trying mirror: {mirror['name']} → {target_url}")

        try:
            response = await client.get(
                target_url,
                follow_redirects=True
            )

            if response.status_code == 200:
                logging.info(
                    f"Serving '{package_name}' from mirror: {mirror['name']}"
                )

                return StreamingResponse(
                    response.aiter_bytes(),
                    status_code=200,
                    media_type=response.headers.get("content-type", "text/html"),
                    headers={
                        "X-Served-By": mirror["name"]
                    }
                )

        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logging.warning(
                f"Mirror failed: {mirror['name']} ({exc})"
            )
            continue

    raise HTTPException(
        status_code=404,
        detail=f"Package '{package_name}' could not be found on any mirrors."
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
