"""Safe boundary for tenant-scoped outbound provider integrations.

The platform owns the request/result contract and policy checks. Provider
adapters own only their typed translation to an external API. Callers must
provide a durable idempotency store and secret resolver in production; the
in-memory implementations below are intentionally deterministic test tools.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Any, Callable, Mapping, Protocol, TypeVar
from urllib.parse import urlsplit


class IntegrationError(RuntimeError):
    """Safe, user-facing integration failure without provider internals."""


class IntegrationPolicyError(IntegrationError):
    """The request violates the configured provider boundary."""


class IntegrationTransientError(IntegrationError):
    """The adapter may be retried according to the request policy."""


RequestPayload = TypeVar("RequestPayload")
ResultPayload = TypeVar("ResultPayload")


@dataclass(frozen=True)
class IntegrationRequest:
    tenant_id: str
    provider: str
    operation: str
    payload: Mapping[str, Any]
    idempotency_key: str
    secret_handle: str
    origin: str
    timeout_seconds: float = 10.0
    max_attempts: int = 3

    def fingerprint(self) -> str:
        body = {
            "tenant_id": self.tenant_id,
            "provider": self.provider,
            "operation": self.operation,
            "payload": self.payload,
            "secret_handle": self.secret_handle,
            "origin": self.origin,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class IntegrationResult:
    provider: str
    operation: str
    payload: Mapping[str, Any]
    attempts: int
    redacted: bool = True


class IntegrationProvider(Protocol):
    provider_id: str
    operations: frozenset[str]

    def invoke(self, request: IntegrationRequest, secret: str) -> Mapping[str, Any]: ...


class SecretResolver(Protocol):
    def resolve(self, tenant_id: str, secret_handle: str) -> str: ...


class IdempotencyStore(Protocol):
    def get(self, tenant_id: str, key: str) -> tuple[str, IntegrationResult] | None: ...

    def put(self, tenant_id: str, key: str, fingerprint: str, result: IntegrationResult) -> None: ...


class RateLimiter(Protocol):
    def allow(self, tenant_id: str, provider: str) -> bool: ...


class MemoryIdempotencyStore:
    """Small deterministic store for tests and local development only."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str], tuple[str, IntegrationResult]] = {}

    def get(self, tenant_id: str, key: str) -> tuple[str, IntegrationResult] | None:
        return self._values.get((tenant_id, key))

    def put(self, tenant_id: str, key: str, fingerprint: str, result: IntegrationResult) -> None:
        self._values[(tenant_id, key)] = (fingerprint, result)


class FixedWindowRateLimiter:
    """Bounded process-local limiter; production deployments should replace it."""

    def __init__(self, limit: int = 30, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic) -> None:
        if limit < 1 or window_seconds <= 0:
            raise ValueError("Rate-limit values must be positive.")
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._windows: dict[tuple[str, str], tuple[float, int]] = {}

    def allow(self, tenant_id: str, provider: str) -> bool:
        now = self.clock()
        key = (tenant_id, provider)
        started, count = self._windows.get(key, (now, 0))
        if now - started >= self.window_seconds:
            started, count = now, 0
        if count >= self.limit:
            self._windows[key] = (started, count)
            return False
        self._windows[key] = (started, count + 1)
        return True


class IntegrationPolicy:
    def __init__(self, allowed_origins: Mapping[str, set[str] | frozenset[str]], *, production: bool = False, max_timeout_seconds: float = 30.0) -> None:
        self.allowed_origins = {provider: frozenset(origins) for provider, origins in allowed_origins.items()}
        self.production = production
        self.max_timeout_seconds = max_timeout_seconds

    def validate(self, request: IntegrationRequest, provider: IntegrationProvider) -> None:
        if not request.tenant_id or not request.idempotency_key or not request.secret_handle:
            raise IntegrationPolicyError("Integration requests require tenant, idempotency and secret handles.")
        if provider.provider_id != request.provider or request.provider not in self.allowed_origins:
            raise IntegrationPolicyError("The requested integration provider is not enabled.")
        if request.operation not in provider.operations:
            raise IntegrationPolicyError("The requested integration operation is not supported.")
        if request.origin not in self.allowed_origins[request.provider]:
            raise IntegrationPolicyError("The provider origin is not allowlisted.")
        parsed = urlsplit(request.origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise IntegrationPolicyError("The provider origin must be an absolute HTTP(S) origin.")
        if self.production and parsed.scheme != "https":
            raise IntegrationPolicyError("Production integrations require HTTPS origins.")
        if not 0 < request.timeout_seconds <= self.max_timeout_seconds:
            raise IntegrationPolicyError("Integration timeout is outside the configured limit.")
        if not 1 <= request.max_attempts <= 5:
            raise IntegrationPolicyError("Integration retry attempts must be between 1 and 5.")


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _redact(item) for key, item in value.items() if str(key).lower() not in {"secret", "token", "password", "access_key"}}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return [_redact(item) for item in value]
    return value


class IntegrationExecutor:
    def __init__(self, *, policy: IntegrationPolicy, providers: Mapping[str, IntegrationProvider], secrets: SecretResolver, idempotency: IdempotencyStore, limiter: RateLimiter, sleep: Callable[[float], None] | None = None) -> None:
        self.policy = policy
        self.providers = dict(providers)
        self.secrets = secrets
        self.idempotency = idempotency
        self.limiter = limiter
        self.sleep = sleep or (lambda _seconds: None)

    def execute(self, request: IntegrationRequest) -> IntegrationResult:
        provider = self.providers.get(request.provider)
        if provider is None:
            raise IntegrationPolicyError("The requested integration provider is not enabled.")
        self.policy.validate(request, provider)
        existing = self.idempotency.get(request.tenant_id, request.idempotency_key)
        if existing:
            fingerprint, result = existing
            if fingerprint != request.fingerprint():
                raise IntegrationError("The idempotency key is already bound to a different request.")
            return result
        if not self.limiter.allow(request.tenant_id, request.provider):
            raise IntegrationError("The integration rate limit has been reached; retry later.")
        try:
            secret = self.secrets.resolve(request.tenant_id, request.secret_handle)
        except Exception as error:  # resolver implementations must not leak provider details
            raise IntegrationError("The integration secret is unavailable.") from error
        last_error: IntegrationTransientError | None = None
        for attempt in range(1, request.max_attempts + 1):
            try:
                payload = _redact(provider.invoke(request, secret))
                result = IntegrationResult(request.provider, request.operation, payload, attempt)
                self.idempotency.put(request.tenant_id, request.idempotency_key, request.fingerprint(), result)
                return result
            except IntegrationTransientError as error:
                last_error = error
                if attempt < request.max_attempts:
                    self.sleep(min(2.0, 0.25 * (2 ** (attempt - 1))))
        raise IntegrationError("The integration provider did not complete the request.") from last_error


class DeterministicTestProvider:
    """Provider used by tests and generated proof apps; it performs no network I/O."""

    provider_id = "deterministic"
    operations = frozenset({"echo", "health"})

    def __init__(self, transient_failures: int = 0) -> None:
        self.transient_failures = transient_failures
        self.calls = 0

    def invoke(self, request: IntegrationRequest, secret: str) -> Mapping[str, Any]:
        self.calls += 1
        if self.calls <= self.transient_failures:
            raise IntegrationTransientError("temporary provider failure")
        return {"operation": request.operation, "payload": dict(request.payload), "secret_present": bool(secret)}
