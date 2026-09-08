from app.platform.integrations import (
    DeterministicTestProvider,
    FixedWindowRateLimiter,
    IntegrationError,
    IntegrationExecutor,
    IntegrationPolicy,
    IntegrationPolicyError,
    IntegrationRequest,
    MemoryIdempotencyStore,
)


class Secrets:
    def resolve(self, tenant_id, secret_handle):
        assert tenant_id == 'tenant-a'
        return 'provider-secret'


def executor(provider=None, **kwargs):
    provider = provider or DeterministicTestProvider()
    return IntegrationExecutor(
        policy=IntegrationPolicy({'deterministic': {'https://provider.example'}}, production=True),
        providers={'deterministic': provider}, secrets=Secrets(),
        idempotency=MemoryIdempotencyStore(), limiter=FixedWindowRateLimiter(limit=10), **kwargs,
    )


def request(**kwargs):
    values = dict(
        tenant_id='tenant-a', provider='deterministic', operation='echo', payload={'message': 'hello', 'token': 'never-return'},
        idempotency_key='key-1', secret_handle='INTEGRATION_TEST', origin='https://provider.example',
    )
    values.update(kwargs)
    return IntegrationRequest(**values)


def test_typed_provider_result_is_redacted_and_idempotent():
    provider = DeterministicTestProvider()
    service = executor(provider)
    first = service.execute(request())
    second = service.execute(request())
    assert first == second
    assert provider.calls == 1
    assert first.payload['payload']['message'] == 'hello'
    assert 'token' not in first.payload['payload']


def test_retry_is_bounded_and_uses_backoff():
    waits = []
    provider = DeterministicTestProvider(transient_failures=2)
    service = executor(provider, sleep=waits.append)
    result = service.execute(request(max_attempts=3))
    assert result.attempts == 3 and provider.calls == 3
    assert waits == [0.25, 0.5]


def test_idempotency_rejects_reused_key_for_different_payload():
    service = executor()
    service.execute(request())
    try:
        service.execute(request(payload={'message': 'different'}))
    except IntegrationError as error:
        assert 'idempotency' in str(error)
    else:
        raise AssertionError('expected idempotency conflict')


def test_production_rejects_http_and_unknown_origin():
    service = executor()
    for origin in ('http://provider.example', 'https://other.example'):
        try:
            service.execute(request(origin=origin))
        except IntegrationPolicyError:
            pass
        else:
            raise AssertionError('expected provider-origin policy failure')


def test_rate_limit_is_tenant_and_provider_scoped():
    provider = DeterministicTestProvider()
    service = IntegrationExecutor(
        policy=IntegrationPolicy({'deterministic': {'https://provider.example'}}, production=True),
        providers={'deterministic': provider}, secrets=Secrets(), idempotency=MemoryIdempotencyStore(),
        limiter=FixedWindowRateLimiter(limit=1),
    )
    service.execute(request())
    try:
        service.execute(request(idempotency_key='key-2'))
    except IntegrationError as error:
        assert 'rate limit' in str(error)
    else:
        raise AssertionError('expected rate-limit failure')
