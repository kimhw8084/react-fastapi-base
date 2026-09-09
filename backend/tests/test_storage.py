from pathlib import Path
import pytest
from app.platform.attachments import DeterministicMalwareScanner
from app.platform.storage import LocalFilesystemStorage, MemoryStorage


@pytest.mark.parametrize('key', ['../escape.txt', '/absolute.txt', 'tenant/../../escape.txt', 'bad\\name.txt'])
def test_storage_rejects_path_traversal(tmp_path: Path, key: str):
    with pytest.raises(ValueError): LocalFilesystemStorage(tmp_path).put('tenant-a',key,b'x','text/plain')


def test_local_storage_is_atomic_mode_limited_and_tenant_scoped(tmp_path: Path):
    storage=LocalFilesystemStorage(tmp_path)
    first=storage.put('tenant-a','attachments/a.txt',b'first','text/plain')
    second=storage.put('tenant-a','attachments/a.txt',b'second','text/plain')
    assert first.size==5 and second.sha256 != first.sha256 and storage.get('tenant-a','attachments/a.txt')==b'second'
    assert storage.exists('tenant-a','attachments/a.txt') and not storage.exists('tenant-b','attachments/a.txt')
    assert (tmp_path/'tenant-a/attachments/a.txt').stat().st_mode & 0o777 == 0o600
    storage.delete('tenant-a','attachments/a.txt');assert not storage.exists('tenant-a','attachments/a.txt')


def test_memory_storage_matches_adapter_contract():
    storage=MemoryStorage();stored=storage.put('tenant-a','exports/result.json',b'{}','application/json')
    assert stored.size==2 and storage.get('tenant-a','exports/result.json')==b'{}'
    with pytest.raises(FileNotFoundError):storage.get('tenant-b','exports/result.json')


def test_deterministic_attachment_scanner_rejects_active_content():
    scanner=DeterministicMalwareScanner()
    assert scanner.scan(b'plain text','text/plain','notes.txt')
    assert not scanner.scan(scanner.EICAR_TOKEN,'text/plain','eicar.txt')
    assert not scanner.scan(b'<svg><script>alert(1)</script></svg>','image/svg+xml','diagram.svg')
