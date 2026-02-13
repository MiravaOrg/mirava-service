 # mirava

 Universal proxy for Docker registry and PyPI mirrors with automatic failover.

 ## Features

 - **Docker Registry Proxy**: Transparent mirror for Docker Hub with fallback
 - **PyPI Proxy**: Python package index mirror with automatic retry
 - **Health Monitoring**: Automatic mirror health checks and degradation
 - **Dynamic Configuration**: Add/remove mirrors via API
 - **Swagger UI**: Built-in API documentation

 ## Installation

 ```bash
 git clone https://github.com/yourusername/mirava.git
 cd mirava
 uv sync
 ```

 ## Quick Start

 ```bash
 # Run with default configuration
 uv run mirava

 # Or run directly
 uv run python -m mirava.main
 ```

 Server starts on `http://localhost:8080`

 ## Configuration

 ### Environment Variables

 | Variable              | Default                        | Description                    |
 | --------------------- | ------------------------------ | ------------------------------ |
 | `HOST`                | `0.0.0.0`                      | Server bind address            |
 | `PORT`                | `8080`                         | Server port                    |
 | `PYPI_OFFICIAL_URL`   | `https://pypi.org/simple`      | Official PyPI index            |
 | `PYPI_MIRRORS`        | (built-in)                     | Comma-separated PyPI mirrors   |
 | `DOCKER_OFFICIAL_URL` | `https://registry-1.docker.io` | Official Docker registry       |
 | `DOCKER_MIRRORS`      | (built-in)                     | Comma-separated Docker mirrors |

 ### Examples

 ```bash
 # Use custom PyPI index
 PYPI_OFFICIAL_URL=https://pypi.company.internal/simple uv run mirava

 # Custom mirrors only
 PYPI_MIRRORS="https://mirror1.com/simple,https://mirror2.com/simple" \
 DOCKER_MIRRORS="https://docker-mirror1.com,https://docker-mirror2.com" \
 uv run mirava
 ```

 ## Docker Setup

 Configure Docker to use the proxy:

 ```bash
 sudo tee /etc/docker/daemon.json <<EOF
 {
   "registry-mirrors": ["http://127.0.0.1:8080"],
   "insecure-registries": ["127.0.0.1:8080"]
 }
 EOF
 sudo systemctl restart docker
 ```

 Now use Docker normally:
 ```bash
 docker pull hello-world
 docker pull nginx
 ```

 ## PyPI Setup

 Configure pip to use the proxy:

 ```bash
 # Global config
 pip config set global.index-url http://127.0.0.1:8080/simple
 pip config set global.trusted-host 127.0.0.1

 # Or per-command
 pip install --index-url http://127.0.0.1:8080/simple --trusted-host 127.0.0.1 requests
 ```

 Or use environment variables:
 ```bash
 export PIP_INDEX_URL=http://127.0.0.1:8080/simple
 export PIP_TRUSTED_HOST=127.0.0.1
 pip install requests
 ```

 ## API Endpoints

 | Endpoint                  | Method        | Description            |
 | ------------------------- | ------------- | ---------------------- |
 | `/`                       | GET           | Service info           |
 | `/docs`                   | GET           | Swagger UI             |
 | `/redoc`                  | GET           | ReDoc documentation    |
 | `/health`                 | GET           | Mirror health status   |
 | `/v2/`                    | GET/HEAD      | Docker registry root   |
 | `/v2/{path}`              | GET/HEAD/POST | Docker registry proxy  |
 | `/simple/{package}/`      | GET           | PyPI package proxy     |
 | `/mirrors/{type}`         | POST          | Add mirror dynamically |
 | `/config/{type}/official` | PUT           | Update official URL    |

 ## API Usage Examples

 ```bash
 # Check health
 curl http://localhost:8080/health

 # Add mirror dynamically
 curl -X POST "http://localhost:8080/mirrors/pypi?url=https://new.mirror.com/simple&name=newmirror&priority=5"

 # Update official PyPI URL
 curl -X PUT "http://localhost:8080/config/pypi/official?url=https://test.pypi.org/simple"
 ```

 ## Project Structure

 ```
 src/mirava/
 ├── __init__.py          # Package init
 ├── main.py              # FastAPI application
 ├── cli.py               # CLI entry point
 ├── config.py            # Configuration management
 ├── base.py              # Base classes and utilities
 ├── mirrors.py           # Mirror registry and initialization
 ├── docker.py            # Docker registry routes
 └── pypi.py              # PyPI proxy routes
 ```

 ## Adding New Mirror Types

 1. Create new file `src/mirava/npm.py`:

 ```python
 from fastapi import APIRouter
 from .mirrors import registry

 router = APIRouter(tags=["NPM"])

 @router.get("/npm/{package}")
 async def npm_proxy(package: str):
     # Implementation
     pass
 ```

 2. Add mirrors to `mirrors.py`:

 ```python
 NPM_MIRRORS = [
     ("https://registry.npmmirror.com", "npmmirror", 0),
 ]
 ```

 3. Register in `init_mirrors()`:

 ```python
 npm_mgr = BaseMirrorManager("npm")
 npm_mgr.official_url = "https://registry.npmjs.org"
 for url, name, priority in NPM_MIRRORS:
     npm_mgr.add_mirror(url, name, priority)
 registry.register("npm", npm_mgr)
 ```

 4. Include router in `main.py`:

 ```python
 from . import npm
 app.include_router(npm.router)
 ```

 ## Development

 ```bash
 # Run in development mode with auto-reload
 uv run --reload mirava

 # Or with Python directly
 cd src
 PYTHONPATH=. uvicorn mirava.main:create_app --factory --reload
 ```

 ## Docker Compose

 ```yaml
 version: '3.8'
 services:
   mirava:
     build: .
     ports:
       - "8080:8080"
     environment:
       - PYPI_OFFICIAL_URL=https://pypi.org/simple
       - PYPI_MIRRORS=https://mirror1.com/simple,https://mirror2.com/simple
     restart: unless-stopped
 ```

 ## License

 MIT License