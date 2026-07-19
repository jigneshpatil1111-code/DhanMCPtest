from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProjectPaths:
    root: Path
    data_dir: Path
    db_path: Path
    config_path: Path


def get_project_paths(root: str | Path | None = None) -> ProjectPaths:
    project_root = Path(root) if root is not None else Path.cwd()
    data_dir = project_root / "work" / "data"
    return ProjectPaths(
        root=project_root,
        data_dir=data_dir,
        db_path=data_dir / "market.db",
        config_path=project_root / "work" / "config.toml",
    )
