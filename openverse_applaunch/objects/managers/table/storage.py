from typing import Any


class StorageVars(dict):
    """This class needs for dynamic added attributes"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f'Storage Vars object hgas not attribute {name}'
            )

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__class__.__dict__:
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(
                f'Storage Vars objecat hgas not attribute {name}'
            )

    def __repr__(self) -> str:
        items_vars = ', '.join(f"{k}={v!r}" for k, v in self.items())
        return f"StorageVars({items_vars})"