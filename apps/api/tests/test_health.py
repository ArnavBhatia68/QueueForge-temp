from fastapi.testclient import TestClient
import main as main_module


class DummySession:
    async def execute(self, _query):
        return None


class DummySessionContext:
    async def __aenter__(self):
        return DummySession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyRedis:
    async def ping(self):
        return True

    async def aclose(self):
        return None


def dummy_session_local_ok():
    return DummySessionContext()


async def dummy_redis_from_url_ok(*args, **kwargs):  # noqa: ARG001
    return DummyRedis()


def test_health_liveness_endpoint_returns_ok():
    client = TestClient(main_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_deep_ok(monkeypatch):
    monkeypatch.setattr(main_module, "SessionLocal", dummy_session_local_ok)
    monkeypatch.setattr(main_module.aioredis, "from_url", dummy_redis_from_url_ok)

    client = TestClient(main_module.app)
    response = client.get("/health/deep")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dependencies"]["postgres"] == "ok"
    assert body["dependencies"]["redis"] == "ok"


def test_health_deep_degraded_when_dependencies_fail(monkeypatch):
    class FailingSession:
        async def execute(self, _query):
            raise RuntimeError("db down")

    class FailingSessionContext:
        async def __aenter__(self):
            return FailingSession()

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def redis_down(*args, **kwargs):  # noqa: ARG001
        raise RuntimeError("redis down")

    monkeypatch.setattr(main_module, "SessionLocal", lambda: FailingSessionContext())
    monkeypatch.setattr(main_module.aioredis, "from_url", redis_down)

    client = TestClient(main_module.app)
    response = client.get("/health/deep")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["dependencies"]["postgres"] == "down"
    assert body["dependencies"]["redis"] == "down"
