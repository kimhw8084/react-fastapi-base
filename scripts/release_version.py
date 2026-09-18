"""Shared release-version, artifact-path and candidate-progression contract."""
from __future__ import annotations

import copy
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ is required by the repo.
    tomllib = None  # type: ignore[assignment]


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
    version_projection_only: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "mode": self.mode,
            "base_version": self.base_version,
            "candidate_version": self.candidate_version,
            "source_changed": self.source_changed,
            "version_projection_only": self.version_projection_only,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class VersionProjectionResult:
    """Classification of executable-source changes during stable promotion."""

    allowed: bool
    changed_paths: tuple[str, ...]
    projection_fields: tuple[str, ...]
    forbidden_changes: tuple[str, ...]
    reason: str

    @property
    def version_projection_only(self) -> bool:
        return self.allowed and bool(self.changed_paths)


_JSON_PROJECTION_PATHS = {
    "frontend/package.json": (("version",),),
    "frontend/package-lock.json": (("version",), ("packages", "", "version")),
    "contracts/openapi.json": (("info", "version"),),
}
_TOML_PROJECTION_PATHS = {
    "backend/pyproject.toml": (("project", "version"),),
}
_REQUIRED_PROJECTION_FILES = tuple((*_JSON_PROJECTION_PATHS, *_TOML_PROJECTION_PATHS))


class _ProjectionValidationError(ValueError):
    """A stable version projection is malformed or incomplete."""


def _strict_json(raw: bytes, path: str) -> Any:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise _ProjectionValidationError(f"{path} contains duplicate JSON field {key!r}.")
            result[key] = value
        return result

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _ProjectionValidationError(f"{path} is not valid UTF-8 JSON.") from error


def _strict_toml(raw: bytes, path: str) -> dict[str, Any]:
    if tomllib is None:  # pragma: no cover - guarded by the supported Python range.
        raise _ProjectionValidationError("TOML parsing is unavailable.")
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise _ProjectionValidationError(f"{path} is not valid TOML.") from error
    if not isinstance(document, dict):
        raise _ProjectionValidationError(f"{path} must contain a TOML document.")
    return document


def _remove_path(document: Any, path: tuple[str, ...], label: str) -> Any:
    result = copy.deepcopy(document)
    cursor = result
    for key in path[:-1]:
        if not isinstance(cursor, dict) or key not in cursor:
            raise _ProjectionValidationError(f"{label} is missing expected version field {'.'.join(path)}.")
        cursor = cursor[key]
    if not isinstance(cursor, dict) or path[-1] not in cursor:
        raise _ProjectionValidationError(f"{label} is missing expected version field {'.'.join(path)}.")
    del cursor[path[-1]]
    return result


def _path_value(document: Any, path: tuple[str, ...], label: str) -> Any:
    cursor = document
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            raise _ProjectionValidationError(f"{label} is missing expected version field {'.'.join(path)}.")
        cursor = cursor[key]
    return cursor


def _field_label(path: tuple[str, ...]) -> str:
    return ".".join(f"[{key!r}]" if key == "" else key for key in path).replace(".[", "[")


def _git_file_at_base(base_sha: str, root: Path, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{base_sha}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise _ProjectionValidationError(f"The exact release base is missing executable source {relative}.")
    return result.stdout


def _current_file(root: Path, relative: str) -> bytes:
    path = root / relative
    try:
        return path.read_bytes()
    except OSError as error:
        raise _ProjectionValidationError(f"The proposed stable candidate is missing executable source {relative}.") from error


def _validate_json_projection(
    *,
    relative: str,
    base_raw: bytes,
    current_raw: bytes,
    fields: tuple[tuple[str, ...], ...],
    previous: ReleaseVersion,
    candidate: ReleaseVersion,
) -> tuple[str, ...]:
    base_document = _strict_json(base_raw, relative)
    current_document = _strict_json(current_raw, relative)
    if not isinstance(base_document, dict) or not isinstance(current_document, dict):
        raise _ProjectionValidationError(f"{relative} must contain a JSON object.")

    for field in fields:
        base_value = _path_value(base_document, field, relative)
        current_value = _path_value(current_document, field, relative)
        expected_base = previous.version
        expected_candidate = candidate.version
        if relative == "backend/pyproject.toml":
            expected_base = previous.pep440
            expected_candidate = candidate.pep440
        if base_value != expected_base or current_value != expected_candidate:
            raise _ProjectionValidationError(
                f"{relative} must project {expected_base!r} to {expected_candidate!r} at {'.'.join(field)}."
            )

    normalized_base = base_document
    normalized_current = current_document
    for field in fields:
        normalized_base = _remove_path(normalized_base, field, relative)
        normalized_current = _remove_path(normalized_current, field, relative)
    if normalized_base != normalized_current:
        raise _ProjectionValidationError(f"{relative} contains non-version metadata changes.")
    return tuple(f"{relative}:{_field_label(field)}" for field in fields)


def _validate_toml_projection(
    *,
    relative: str,
    base_raw: bytes,
    current_raw: bytes,
    previous: ReleaseVersion,
    candidate: ReleaseVersion,
) -> tuple[str, ...]:
    base_document = _strict_toml(base_raw, relative)
    current_document = _strict_toml(current_raw, relative)
    field = ("project", "version")
    if _path_value(base_document, field, relative) != previous.pep440:
        raise _ProjectionValidationError(
            f"{relative} must contain the base PEP 440 version {previous.pep440!r}."
        )
    if _path_value(current_document, field, relative) != candidate.pep440:
        raise _ProjectionValidationError(
            f"{relative} must contain the stable PEP 440 version {candidate.pep440!r}."
        )
    normalized_base = _remove_path(base_document, field, relative)
    normalized_current = _remove_path(current_document, field, relative)
    if normalized_base != normalized_current:
        raise _ProjectionValidationError(f"{relative} contains non-version metadata changes.")
    return (f"{relative}:{_field_label(field)}",)


def compare_stable_version_projection(
    *,
    base_sha: str,
    root: Path,
    previous: ReleaseVersion,
    candidate: ReleaseVersion,
) -> VersionProjectionResult:
    """Prove that a stable candidate differs from its prerelease base only in version metadata.

    This is intentionally a content-aware contract.  A changed path is not
    accepted merely because its filename is known: each supported structured
    file is parsed, its exact version field is validated, and the remainder of
    the normalized document must be identical to the exact base candidate.
    """
    try:
        from scripts.source_manifest import source_hashes
    except ModuleNotFoundError:
        from source_manifest import source_hashes

    changed_paths: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()
    try:
        base_hashes = _source_hashes_at_base(base_sha, root)
        current_hashes = source_hashes(root=root)
        changed_paths = tuple(sorted(
            path for path in set(base_hashes) | set(current_hashes)
            if base_hashes.get(path) != current_hashes.get(path)
        ))
        missing = [path for path in _REQUIRED_PROJECTION_FILES if path not in base_hashes or path not in current_hashes]
        if missing:
            raise _ProjectionValidationError(
                "Stable version projection is incomplete; required metadata is missing: " + ", ".join(missing)
            )
        forbidden = tuple(path for path in changed_paths if path not in _REQUIRED_PROJECTION_FILES)
        if forbidden:
            return VersionProjectionResult(
                False,
                changed_paths,
                (),
                forbidden,
                "Stable promotion rejects executable-source substitution outside version projection metadata: "
                + ", ".join(forbidden),
            )

        projection_fields: list[str] = []
        for relative, fields in _JSON_PROJECTION_PATHS.items():
            projection_fields.extend(_validate_json_projection(
                relative=relative,
                base_raw=_git_file_at_base(base_sha, root, relative),
                current_raw=_current_file(root, relative),
                fields=fields,
                previous=previous,
                candidate=candidate,
            ))
        for relative in _TOML_PROJECTION_PATHS:
            projection_fields.extend(_validate_toml_projection(
                relative=relative,
                base_raw=_git_file_at_base(base_sha, root, relative),
                current_raw=_current_file(root, relative),
                previous=previous,
                candidate=candidate,
            ))
        if not changed_paths:
            raise _ProjectionValidationError(
                "Stable promotion requires a real prerelease-to-stable version projection in executable metadata."
            )
        return VersionProjectionResult(
            True,
            changed_paths,
            tuple(sorted(projection_fields)),
            (),
            "Executable-source changes are limited to the validated stable version projection.",
        )
    except _ProjectionValidationError as error:
        return VersionProjectionResult(False, changed_paths, (), forbidden or changed_paths, str(error))


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
        if candidate_version is not None and read_candidate_version(root) != candidate:
            return ProgressionResult(
                False,
                "stable_promotion",
                previous.version,
                candidate.version,
                source_changed,
                "Candidate version must match the repository VERSION.",
            )
        if not stable_promotion:
            return ProgressionResult(False, "ordinary_build", previous.version, candidate.version, source_changed, "Stable versions require explicit stable promotion mode.")
        if previous.is_stable or candidate.release_train != previous.release_train:
            return ProgressionResult(False, "stable_promotion", previous.version, candidate.version, source_changed, "Stable promotion must promote the same release train from a prerelease candidate.")
        projection = compare_stable_version_projection(
            base_sha=resolved_base,
            root=root,
            previous=previous,
            candidate=candidate,
        )
        if not projection.allowed:
            return ProgressionResult(
                False,
                "stable_promotion",
                previous.version,
                candidate.version,
                source_changed,
                projection.reason,
                projection.version_projection_only,
            )
        return ProgressionResult(
            True,
            "stable_promotion",
            previous.version,
            candidate.version,
            source_changed,
            projection.reason,
            projection.version_projection_only,
        )

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
