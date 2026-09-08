from collections.abc import Callable, Mapping
from app.platform.schemas import WorkspaceDefinition
from app.platform.errors import AppError

class WorkspaceRegistry:
    """Composition root injects factories; the platform never imports application features."""
    def __init__(self, factories: Mapping[str, Callable[[], WorkspaceDefinition]]):
        self._definitions = {key: factory() for key, factory in factories.items()}
        for key, definition in self._definitions.items():
            if key != definition.key:
                raise ValueError('Workspace key/factory mismatch.')
    def get(self, key: str) -> WorkspaceDefinition:
        if key not in self._definitions:
            raise AppError(404, 'workspace_missing', 'Workspace is not registered.')
        return self._definitions[key].model_copy(deep=True)
    def keys(self) -> set[str]:
        return set(self._definitions)
