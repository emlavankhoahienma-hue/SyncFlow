import os
import mimetypes
import hashlib
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .models import FileMeta
from .security import sanitize_filename

CHUNK_SIZE = 1024 * 1024  # 1MB constant as mandated
MAX_CHUNK_SIZE = 2 * 1024 * 1024  # 2MB max per chunk (anti-memory exhaustion bomb)
MAX_CONCURRENT_UPLOADS = 25  # Limit concurrent transfers to prevent resource starvation

class StorageManager:
    def __init__(self, base_dir: Optional[str] = None):
        if not base_dir:
            user_home = Path.home()
            self.base_dir = user_home / "Downloads" / "SyncFlow"
        else:
            self.base_dir = Path(base_dir)
        
        self.temp_dir = self.base_dir / ".temp"
        self.send_dir = self.base_dir / "SendQueue"
        self.ensure_dirs()

        # In-memory tracking of active uploads: transfer_id -> info
        self.active_transfers: Dict[str, dict] = {}
        # Shared files available for iPhone to download: file_id -> file path
        self.shared_files: Dict[str, Path] = {}

    def ensure_dirs(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.send_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_stale_transfers(self, max_age_seconds: int = 3600):
        """Removes orphaned or abandoned .part files older than max_age_seconds (default 1h)."""
        now = time.time()
        try:
            if self.temp_dir.exists():
                for part in self.temp_dir.glob("*.part"):
                    try:
                        if now - part.stat().st_mtime > max_age_seconds:
                            part.unlink(missing_ok=True)
                    except OSError:
                        pass
        except Exception:
            pass

        for tid in list(self.active_transfers.keys()):
            info = self.active_transfers[tid]
            if now - info.get("last_time", now) > max_age_seconds:
                self.active_transfers.pop(tid, None)

    def set_storage_dir(self, new_dir: str):
        self.base_dir = Path(new_dir)
        self.temp_dir = self.base_dir / ".temp"
        self.send_dir = self.base_dir / "SendQueue"
        self.ensure_dirs()

    def init_upload(self, transfer_id: str, meta: FileMeta) -> int:
        self.ensure_dirs()
        self.cleanup_stale_transfers()

        # Check concurrent transfers limit
        if len(self.active_transfers) >= MAX_CONCURRENT_UPLOADS:
            raise RuntimeError(f"Quá nhiều luồng truyền tải đồng thời (giới hạn {MAX_CONCURRENT_UPLOADS}).")

        # Free disk space check: enforce 200MB buffer
        try:
            usage = shutil.disk_usage(self.base_dir)
            if meta.size > (usage.free - 200 * 1024 * 1024):
                raise OSError(f"Dung lượng ổ đĩa không đủ để lưu file {meta.name} ({meta.size / (1024*1024):.1f} MB)")
        except (OSError, ValueError) as e:
            if "không đủ" in str(e):
                raise
            pass

        temp_file = self.temp_dir / f"{transfer_id}.part"
        resume_offset = 0

        if temp_file.exists():
            resume_offset = temp_file.stat().st_size
            if resume_offset > meta.size:
                # Corrupted or outdated temp file
                temp_file.unlink()
                resume_offset = 0

        self.active_transfers[transfer_id] = {
            "meta": meta,
            "temp_path": temp_file,
            "received_bytes": resume_offset,
            "start_time": time.time(),
            "last_time": time.time(),
            "last_bytes": resume_offset,
            "speed_bps": 0.0
        }
        return resume_offset

    def write_chunk(self, transfer_id: str, chunk_data: bytes, chunk_index: int) -> Tuple[int, float, float]:
        if len(chunk_data) > MAX_CHUNK_SIZE:
            raise ValueError(f"Chunk size exceeds 2MB limit ({len(chunk_data)} bytes). Possible memory bomb.")

        if transfer_id not in self.active_transfers:
            raise KeyError(f"Upload {transfer_id} not initialized")

        transfer = self.active_transfers[transfer_id]
        temp_path: Path = transfer["temp_path"]

        # Append chunk to file
        with open(temp_path, "ab") as f:
            f.write(chunk_data)

        current_size = temp_path.stat().st_size
        transfer["received_bytes"] = current_size

        # Calculate speed & ETA
        now = time.time()
        elapsed = now - transfer["last_time"]
        if elapsed >= 0.25:
            delta_bytes = current_size - transfer["last_bytes"]
            speed = delta_bytes / elapsed if elapsed > 0 else 0
            transfer["speed_bps"] = speed
            transfer["last_time"] = now
            transfer["last_bytes"] = current_size

        total = transfer["meta"].size
        remaining = max(0, total - current_size)
        speed = transfer["speed_bps"]
        eta = remaining / speed if speed > 0 else 0.0

        return current_size, speed, eta

    def finalize_upload(self, transfer_id: str) -> Tuple[bool, Path, str]:
        if transfer_id not in self.active_transfers:
            raise KeyError(f"Upload {transfer_id} not initialized")

        transfer = self.active_transfers[transfer_id]
        temp_path: Path = transfer["temp_path"]
        meta: FileMeta = transfer["meta"]

        if not temp_path.exists():
            raise FileNotFoundError("Temporary chunk file not found")

        # SHA-256 verification
        sha256 = hashlib.sha256()
        with open(temp_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha256.update(chunk)
        computed_hash = sha256.hexdigest().lower()

        verified = True
        if meta.sha256:
            expected_hash = meta.sha256.strip().lower()
            if computed_hash != expected_hash:
                verified = False
                return False, temp_path, f"Hash mismatch: expected {expected_hash}, got {computed_hash}"

        # Resolve unique filename in base_dir with anti-path-traversal protection
        target_name = sanitize_filename(meta.name)
        if meta.ext and not target_name.endswith(f".{meta.ext}"):
            target_name = f"{target_name}.{meta.ext}"

        final_path = self.base_dir / target_name
        counter = 1
        stem = Path(target_name).stem
        ext = Path(target_name).suffix
        while final_path.exists():
            final_path = self.base_dir / f"{stem}_{counter}{ext}"
            counter += 1

        temp_path.rename(final_path)
        del self.active_transfers[transfer_id]

        return True, final_path, "Upload verified and saved"

    def get_available_files(self) -> List[FileMeta]:
        """Scans base_dir and send_dir for files to share with iPhone."""
        self.ensure_dirs()
        files_list = []
        self.shared_files.clear()

        dirs_to_scan = [self.send_dir, self.base_dir]
        seen_names = set()

        for d in dirs_to_scan:
            for item in d.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    if item.name in seen_names:
                        continue
                    seen_names.add(item.name)
                    stat = item.stat()
                    mime, _ = mimetypes.guess_type(item.name)
                    file_id = hashlib.md5(f"{item.name}_{stat.st_mtime}".encode()).hexdigest()
                    self.shared_files[file_id] = item

                    meta = FileMeta(
                        file_id=file_id,
                        name=item.name,
                        ext=item.suffix.lstrip(".").lower(),
                        mime=mime or "application/octet-stream",
                        size=stat.st_size,
                        device="Desktop"
                    )
                    files_list.append(meta)
        return files_list

    def get_file_for_download(self, file_id: str) -> Optional[Path]:
        if file_id in self.shared_files:
            p = self.shared_files[file_id]
            if p.exists():
                return p
        # Refresh and look again
        self.get_available_files()
        return self.shared_files.get(file_id)

storage_manager = StorageManager()
