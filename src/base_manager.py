import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BaseManager:
    """Shared helpers for process/config based managers."""

    def __init__(self, config_path: str, config_key: str, pid_tag: str, log_tag: str):
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / config_path
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        self.config_key = config_key
        self.pid_tag = pid_tag
        self.log_tag = log_tag

        self.config = self._load_config()
        self.cleanup_orphan_files()
        self.cleanup_dead_pids()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_item_config(self, alias: str) -> Optional[Dict[str, Any]]:
        for item in self.config.get(self.config_key, []):
            if item["alias"] == alias:
                return item
        return None

    def _get_pid_file(self, alias: str) -> Path:
        return self.logs_dir / f"{alias}_{self.pid_tag}.pid"

    def _get_log_file(self, alias: str) -> Path:
        return self.logs_dir / f"{alias}_{self.log_tag}.log"

    def _legacy_pid_file(self, alias: str) -> Path:
        return self.logs_dir / f"{alias}.pid"

    def _read_pid(self, alias: str) -> Optional[int]:
        pid_file = self._get_pid_file(alias)
        legacy_pid_file = self._legacy_pid_file(alias)

        candidate = pid_file if pid_file.exists() else legacy_pid_file
        if not candidate.exists():
            return None

        try:
            pid = int(candidate.read_text(encoding="utf-8").strip())
            if candidate == legacy_pid_file and not pid_file.exists():
                pid_file.write_text(str(pid), encoding="utf-8")
                legacy_pid_file.unlink(missing_ok=True)
            return pid
        except ValueError:
            candidate.unlink(missing_ok=True)
            return None

    def _write_pid(self, alias: str, pid: int) -> None:
        self._get_pid_file(alias).write_text(str(pid), encoding="utf-8")

    def _remove_pid(self, alias: str) -> None:
        self._get_pid_file(alias).unlink(missing_ok=True)
        self._legacy_pid_file(alias).unlink(missing_ok=True)

    def _process_exists(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def get_aliases(self) -> List[str]:
        return [item["alias"] for item in self.config.get(self.config_key, [])]

    def cleanup_orphan_files(self, dry_run: bool = False) -> None:
        '''
        if pid/log file exists but the config is gone, then remove the pid/log file.
        '''
        valid_aliases = set(self.get_aliases())
        to_check = [
            (self.logs_dir.glob(f"*_{self.pid_tag}.pid"), f"_{self.pid_tag}.pid"),
            (self.logs_dir.glob(f"*_{self.log_tag}.log"), f"_{self.log_tag}.log"),
        ]

        for file_iter, suffix in to_check:
            for file in file_iter:
                alias = file.name[: -len(suffix)]
                if alias not in valid_aliases:
                    if dry_run:
                        print(f"[DRY-RUN] Would remove orphan file: {file.name}")
                    else:
                        file.unlink(missing_ok=True)

        if self.pid_tag == "server":
            for file in self.logs_dir.glob("*.pid"):
                if file.name.endswith("_server.pid") or file.name.endswith("_tunnel.pid"):
                    continue
                alias = file.stem
                if alias not in valid_aliases:
                    if dry_run:
                        print(f"[DRY-RUN] Would remove legacy orphan file: {file.name}")
                    else:
                        file.unlink(missing_ok=True)

    def cleanup_dead_pids(self) -> None:
        '''
        if process is dead but pid file exists, then remove the pid file.
        '''
        for alias in self.get_aliases():
            self.pid_status(alias)

    def pid_status(self, alias: str) -> Tuple[str, str]:
        pid = self._read_pid(alias)
        if pid is None:
            return "Stopped", "-"

        if self._process_exists(pid):
            return "Running", str(pid)

        self._remove_pid(alias)
        return "Dead", "-"
