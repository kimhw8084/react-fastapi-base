from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fresh_clone_check', ROOT / 'scripts/fresh_clone_check.py')
FRESH = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FRESH)


def test_fresh_clone_uses_exact_candidate_commit_not_remote_main():
    commands = FRESH.verification_commands(Path('/candidate'), 'abc123')

    assert commands[0] == ['git', 'clone', '--no-local', '/candidate', 'clone']
    assert commands[1] == ['git', 'checkout', '--detach', 'abc123']
    assert all('main' not in part for command in commands[:2] for part in command)


def test_unavailable_macos_qualification_is_blocked_but_portable_candidate_can_pass():
    assert FRESH.platform_qualification(True, 'Linux') == 'BLOCKED'
    assert FRESH.platform_qualification(True, 'Darwin') == 'PASS'
    assert FRESH.platform_qualification(False, 'Linux') == 'FAIL'


def test_ci_creates_and_uses_repository_backend_environment():
    workflow = (ROOT / '.github/workflows/verify.yml').read_text()

    assert 'python -m venv backend/.venv' in workflow
    assert 'backend/.venv/bin/python scripts/verify.py' in workflow
    assert 'backend/.venv/bin/python -m playwright install --with-deps chromium' in workflow
