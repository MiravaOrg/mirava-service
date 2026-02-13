from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, AsyncGenerator
import logging
import time

logger = logging.getLogger(__name__)


class MirrorHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass
class Mirror:
    url: str
    name: str
    mirror_type: str = "generic"
    priority: int = 0
    health: MirrorHealth = field(default=MirrorHealth.HEALTHY)
    failure_count: int = 0
    last_error: Optional[str] = None
    last_check: float = field(default_factory=time.time)


class BaseMirrorManager:
    """Base class for mirror managers"""

    def __init__(self, mirror_type: str, max_failures: int = 3):
        self.mirror_type = mirror_type
        self.mirrors: List[Mirror] = []
        self.max_failures = max_failures
        self.official_url: Optional[str] = None

    def add_mirror(self, url: str, name: str, priority: int = 0):
        url = url.strip().rstrip("/")
        mirror = Mirror(
            url=url, name=name, mirror_type=self.mirror_type, priority=priority
        )
        self.mirrors.append(mirror)
        self.mirrors.sort(key=lambda x: x.priority)
        logger.info(
            f"Added {self.mirror_type} mirror: {name} ({url}) priority={priority}"
        )

    def get_healthy_mirrors(self) -> List[Mirror]:
        healthy = [m for m in self.mirrors if m.health != MirrorHealth.DOWN]

        # Add official fallback if configured and not present
        if self.official_url and not any(m.url == self.official_url for m in healthy):
            healthy.append(
                Mirror(
                    url=self.official_url,
                    name=f"{self.mirror_type}-official",
                    mirror_type=self.mirror_type,
                    priority=999,
                )
            )

        return sorted(healthy, key=lambda x: (x.health.value, x.priority))

    async def mark_failure(self, mirror: Mirror, error: str):
        mirror.failure_count += 1
        mirror.last_error = error[:100]
        if mirror.failure_count >= self.max_failures:
            mirror.health = MirrorHealth.DOWN
            logger.warning(f"Mirror {mirror.name} marked DOWN")

    def reset_mirror(self, name: str) -> bool:
        for m in self.mirrors:
            if m.name == name:
                m.failure_count = 0
                m.health = MirrorHealth.HEALTHY
                m.last_error = None
                return True
        return False


async def stream_bytes(content: bytes) -> AsyncGenerator[bytes, None]:
    """Yield content as async generator"""
    yield content


def clean_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Remove hop-by-hop headers"""
    return {
        k: v
        for k, v in headers.items()
        if k.lower() not in ["host", "content-length", "connection", "accept-encoding"]
    }
