"""Shared release-version, artifact-path and candidate-progression contract."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-(?P<channel>alpha|beta|rc)\.(?P<ordinal>[1-9][0-9]*))?$"
)
FULL_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


class ReleaseVersionError(ValueError):
    """A candidate version or release path is invalid."""


class ReleaseProgressionError(ValueError):
    """A candidate does not satisfy the exact-base progression policy."""


@dataclass(frozen=True)
class ReleaseVersion:
    major: int
    minor: int
    patch: int
    channel: str | None = None
    ordinal: int | None = None

    @property
    def is_stable(self) -> bool:
        return self.channel is None

    @property
    def version(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        return base if self.is_stable else f"{base}-{self.channel}.{self.ordinal}"

    @property
    def release_train(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    @property
    def artifact_label(self) -> str:
        if self.is_stable:
            return f"stable-{self.version}"
        return f"{self.channel}{self.ordinal}"

    @property
    def pep440(self) -> str:
        if self.is_stable:
            return self.version
        suffix = {"alpha": "a", "beta": "b", "rc": "rc"}[self.channel or ""]
        return f"{self.major}.{self.minor}.{self.patch}{suffix}{self.ordinal}"


@dataclass(frozen=True)
class ReleasePaths:
    version: ReleaseVersion
    identity: Path
    readiness_matrix: Path
    manifest: Path
    evidence_binding: Path


@dataclass(frozen=True)
class ProgressionResult:
    allowed: bool
    mode: str
    base_version: str
    candidate_version: str
    source_changed: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "mode": self.mode,
            "base_version": self.base_version,
            "candidate_version": self.candidate_version,
            "source_changed": self.source_changed,
            "reason": self.reason,
        }


def parse_candidate_version(value: str) -> ReleaseVersion:
    if not isinstance(value, str):
        raise ReleaseVersionError("Candidate version must be a string.")
    match = VERSION_PATTERN.fullmatch(value.strip())
    if not match:
        raise ReleaseVersionError(
            f"Unsupported release version: {value!r}; expected X.Y.Z, "
            "X.Y.Z-alpha.N, X.Y.Z-beta.N or X.Y.Z-rc.N."
        )
    groups = match.groupdict()
    return ReleaseVersion(
        major=int(groups["major"]),
        minor=int(groups["minor"]),
        patch=int(groups["patch"]),
        channel=groups["channel"],
        ordinal=int(groups["ordinal"]) if groups["ordinal"] else None,
    )


def read_candidate_version(root: Path) -> ReleaseVersion:
    try:
        value = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ReleaseVersionError("VERSION is unavailable.") from error
    return parse_candidate_version(value)


def release_paths(version: str | ReleaseVersion, root: Path) -> ReleasePaths:
    parsed = parse_candidate_version(version) if isinstance(version, str) else version
    label = parsed.artifact_label
    release_dir = root / "evidence/current/release"
    return ReleasePaths(
        version=parsed,
        identity=root / f"deploy/{label}-release-identity.json",
        readiness_matrix=release_dir / f"{label}-readiness-matrix.json",
        manifest=release_dir / f"{label}-manifest.json",
        evidence_binding=release_dir / f"{label}-evidence-binding.json",
    )


def current_release_paths(root: Path) -> ReleasePaths:
    return release_paths(read_candidate_version(root), root)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ReleaseProgressionError(result.stderr.strip() or "Git resolution failed.")
    return result.stdout.strip()


def exact_base_sha(base_sha: str, root: Path) -> str:
    if not isinstance(base_sha, str) or not FULL_SHA_PATTERN.fullmatch(base_sha):
        raise ReleaseProgressionError("Release base must be an exact full commit SHA.")
    resolved = _git(root, "rev-parse", "--verify", f"{base_sha}^{{commit}}")
    if resolved.lower() != base_sha.lower():
        raise ReleaseProgressionError("Release base SHA must not be abbreviated or ambiguous.")
    return resolved.lower()


def base_version(base_sha: str, root: Path) -> ReleaseVersion:
    resolved = exact_base_sha(base_sha, root)
    try:
        value = _git(root, "show", f"{resolved}:VERSION")
    except ReleaseProgressionError as error:
        raise ReleaseProgressionError("The exact release base does not contain VERSION.") from error
    try:
        return parse_candidate_version(value)
    except ReleaseVersionError as error:
        raise ReleaseProgressionError(f"The exact release base has an invalid VERSION: {error}") from error


def _source_hashes_at_base(base_sha: str, root: Path) -> dict[str, str]:
    # Import lazily so the shared version/path contract remains usable by the
    # backend without importing the tooling module during normal startup.
    try:
        from scripts.source_manifest import source_hashes_at_git
    except ModuleNotFoundError:
        from source_manifest import source_hashes_at_git

    return source_hashes_at_git(base_sha, root=root)


def check_candidate_progression(
    *,
    base_sha: str,
    root: Path,
    candidate_version: str | None = None,
    stable_promotion: bool = False,
) -> ProgressionResult:
    candidate = parse_candidate_version(candidate_version) if candidate_version is not None else read_candidate_version(root)
    resolved_base = exact_base_sha(base_sha, root)
    previous = base_version(resolved_base, root)

    try:
        from scripts.source_manifest import source_hashes
    except ModuleNotFoundError:
        from source_manifest import source_hashes

    source_changed = source_hashes(root=root) != _source_hashes_at_base(resolved_base, root)
    if candidate.is_stable:
        if not stable_promotion:
            return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, "Stable versions require explicit stable promotion mode.")
        if previous.is_stable or candidate.release_train != previous.release_train:
            return ProgressionResult(False, "stable_promotion", previous.version, candidate.version, source_changed, "Stable promotion must promote the same release train from a prerelease candidate.")
        if source_changed:
            return ProgressionResult(False, "stable_promotion", previous.version, candidate.version, source_changed, "Stable promotion rejects executable-source substitution.")
        return ProgressionResult(True, "stable_promotion", previous.version, candidate.version, source_changed, "Explicit stable promotion preserves the exact established executable source.")

    if stable_promotion:
        return ProgressionResult(False, "stable_promotion", previous.version, candidate.version, source_changed, "Stable promotion mode requires a stable VERSION.")
    if candidate.release_train != previous.release_train:
        return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, "Candidate must remain in the exact release train of the review base.")
    if candidate.version == previous.version:
        if source_changed:
            return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, "Executable source changed while reusing the review-base candidate version.")
        return ProgressionResult(True, "evidence_only", previous.version, candidate.version, source_changed, "Evidence-only or binding commits may retain the established candidate version.")
    if previous.is_stable:
        return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, "A stable base cannot be rolled back or reused as a prerelease candidate.")
    expected = ReleaseVersion(previous.major, previous.minor, previous.patch, previous.channel, (previous.ordinal or 0) + 1)
    if candidate != expected:
        return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, f"Ordinary prerelease progression must advance exactly to {expected.version}.")
    return ProgressionResult(True, "ordinary_build", previous.version, candidate.version, source_changed, f"Candidate advances exactly from {previous.version} to {candidate.version}.")


def assert_candidate_progression(**kwargs: Any) -> ProgressionResult:
    result = check_candidate_progression(**kwargs)
    if not result.allowed:
        raise ReleaseProgressionError(result.reason)
    return result
