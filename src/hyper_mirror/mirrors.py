from .base import BaseMirrorManager
import logging

logger = logging.getLogger(__name__)

# Docker mirrors configuration
DOCKER_MIRRORS = [
    ("https://mirror-docker.runflare.com", "runflare", 0),
    ("https://docker.mirrors.ustc.edu.cn", "ustc", 1),
    ("https://hub-mirror.c.163.com", "netease", 2),
    ("https://mirror.gcr.io", "gcr", 3),
]

# PyPI mirrors configuration
PYPI_MIRRORS = [
    ("https://mirror-pypi.runflare.com/simple", "runflare-pypi", 0),
    ("https://pypi.tuna.tsinghua.edu.cn/simple", "tsinghua", 1),
    ("https://mirrors.aliyun.com/pypi/simple", "aliyun", 2),
]


class MirrorRegistry:
    """Central registry for all mirror managers"""

    def __init__(self):
        self._managers: dict[str, BaseMirrorManager] = {}

    def register(self, name: str, manager: BaseMirrorManager):
        self._managers[name] = manager
        logger.info(f"Registered mirror manager: {name}")

    def get(self, name: str) -> BaseMirrorManager:
        return self._managers[name]

    def list_managers(self) -> dict[str, BaseMirrorManager]:
        return self._managers.copy()

    def get_all_mirrors(self) -> list:
        all_mirrors = []
        for manager in self._managers.values():
            all_mirrors.extend(manager.mirrors)
        return all_mirrors


# Global registry instance
registry = MirrorRegistry()


def init_mirrors():
    """Initialize all mirror managers"""

    # Docker
    docker_mgr = BaseMirrorManager("docker")
    docker_mgr.official_url = "https://registry-1.docker.io"
    for url, name, priority in DOCKER_MIRRORS:
        docker_mgr.add_mirror(url, name, priority)
    registry.register("docker", docker_mgr)

    # PyPI
    pypi_mgr = BaseMirrorManager("pypi")
    pypi_mgr.official_url = "https://pypi.org/simple"
    for url, name, priority in PYPI_MIRRORS:
        pypi_mgr.add_mirror(url, name, priority)
    registry.register("pypi", pypi_mgr)

    return registry
