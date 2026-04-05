from __future__ import annotations

import os
import sqlite3
import importlib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Sequence

def _load_mutagen_file():
    try:
        module = importlib.import_module("mutagen")
    except Exception:  # pragma: no cover - optional dependency
        return None

    return getattr(module, "File", None)


MutagenFile = _load_mutagen_file()

DEFAULT_EXTENSIONS = {".mp3", ".flac", ".m4a", ".mp4", ".aac", ".wav", ".ogg", ".wma"}
DEFAULT_LIMIT = 100
MAX_LIMIT = 500
MAX_CHANGES_LIMIT = 5_000


@dataclass
class ScanProgress:
    processed: int = 0
    new: int = 0
    modified: int = 0
    deleted: int = 0
    unchanged: int = 0


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_path(path: Path) -> str:
    return str(path.expanduser().resolve())


class MusicIndexService:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")
        connection.execute("PRAGMA busy_timeout = 5000;")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    root_path TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    relative_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    album TEXT NOT NULL,
                    year INTEGER,
                    size_bytes INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    scan_id TEXT PRIMARY KEY,
                    root_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    processed_files INTEGER NOT NULL DEFAULT 0,
                    new_files INTEGER NOT NULL DEFAULT 0,
                    modified_files INTEGER NOT NULL DEFAULT 0,
                    deleted_files INTEGER NOT NULL DEFAULT 0,
                    unchanged_files INTEGER NOT NULL DEFAULT 0,
                    error TEXT
                );
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_root_active ON songs(root_path, active);"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_updated_at ON songs(updated_at);"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title COLLATE NOCASE);"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist COLLATE NOCASE);"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_album ON songs(album COLLATE NOCASE);"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_runs_status ON scan_runs(status, started_at DESC);"
            )
            connection.commit()

    def _normalize_extensions(self, extensions: Optional[Sequence[str]]) -> set[str]:
        if not extensions:
            return DEFAULT_EXTENSIONS

        normalized = set()
        for item in extensions:
            ext = item.strip().lower()
            if not ext:
                continue
            normalized.add(ext if ext.startswith(".") else f".{ext}")

        return normalized or DEFAULT_EXTENSIONS

    def _iter_music_files(self, root_path: Path, extensions: set[str], recursive: bool):
        if recursive:
            for current_root, _, files in os.walk(root_path):
                for filename in files:
                    file_path = Path(current_root) / filename
                    if file_path.suffix.lower() in extensions:
                        yield file_path
            return

        for file_path in root_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                yield file_path

    def _extract_metadata(self, file_path: Path) -> dict[str, object]:
        title = file_path.stem
        artist = "Unknown Artist"
        album = "Unknown Album"
        year = None

        if MutagenFile is not None:
            try:
                audio = MutagenFile(file_path, easy=True)
                tags = getattr(audio, "tags", None) or {}
                title = self._first_tag(tags.get("title")) or title
                artist = self._first_tag(tags.get("artist")) or artist
                album = self._first_tag(tags.get("album")) or album
                year_text = self._first_tag(tags.get("date")) or self._first_tag(tags.get("year"))
                year = self._parse_year(year_text)
            except Exception:
                pass

        if artist == "Unknown Artist" and " - " in file_path.stem:
            maybe_artist, maybe_title = file_path.stem.split(" - ", 1)
            if maybe_artist.strip():
                artist = maybe_artist.strip()
            if maybe_title.strip():
                title = maybe_title.strip()

        return {
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
        }

    @staticmethod
    def _first_tag(value: object) -> Optional[str]:
        if isinstance(value, list) and value:
            text = str(value[0]).strip()
            return text or None

        if value is None:
            return None

        text = str(value).strip()
        return text or None

    @staticmethod
    def _parse_year(year_text: Optional[str]) -> Optional[int]:
        if not year_text:
            return None

        for token in year_text.replace("/", "-").split("-"):
            trimmed = token.strip()
            if len(trimmed) == 4 and trimmed.isdigit():
                return int(trimmed)

        return None

    def _start_scan_run(self, scan_id: str, root_path: str) -> None:
        started_at = utc_now_iso()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO scan_runs (
                    scan_id, root_path, status, started_at, finished_at,
                    processed_files, new_files, modified_files, deleted_files, unchanged_files, error
                ) VALUES (?, ?, 'in_progress', ?, NULL, 0, 0, 0, 0, 0, NULL)
                """,
                (scan_id, root_path, started_at),
            )
            connection.commit()

    def _update_scan_run(
        self,
        scan_id: str,
        progress: ScanProgress,
        status: Optional[str] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        finished_at = utc_now_iso() if finished else None
        fields = [
            "processed_files = ?",
            "new_files = ?",
            "modified_files = ?",
            "deleted_files = ?",
            "unchanged_files = ?",
        ]
        values: list[object] = [
            progress.processed,
            progress.new,
            progress.modified,
            progress.deleted,
            progress.unchanged,
        ]

        if status is not None:
            fields.append("status = ?")
            values.append(status)

        if error is not None:
            fields.append("error = ?")
            values.append(error)

        if finished_at is not None:
            fields.append("finished_at = ?")
            values.append(finished_at)

        values.append(scan_id)

        with self._connection() as connection:
            connection.execute(
                f"UPDATE scan_runs SET {', '.join(fields)} WHERE scan_id = ?",
                values,
            )
            connection.commit()

    def scan_library(
        self,
        scan_id: str,
        root_path: str,
        extensions: Optional[Sequence[str]] = None,
        recursive: bool = True,
        full_rescan: bool = False,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None,
    ) -> dict[str, object]:
        root = Path(root_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Music path is invalid: {root}")

        normalized_root = str(root)
        extension_set = self._normalize_extensions(extensions)
        progress = ScanProgress()

        self._start_scan_run(scan_id, normalized_root)

        try:
            with self._connection() as connection:
                cursor = connection.cursor()
                existing_rows = cursor.execute(
                    "SELECT path, mtime_ns, size_bytes, active FROM songs WHERE root_path = ?",
                    (normalized_root,),
                ).fetchall()

                existing_map: dict[str, tuple[int, int, int]] = {
                    str(row["path"]): (int(row["mtime_ns"]), int(row["size_bytes"]), int(row["active"]))
                    for row in existing_rows
                }

                for file_path in self._iter_music_files(root, extension_set, recursive):
                    try:
                        absolute_path = str(file_path.resolve())
                        relative_path = os.path.relpath(absolute_path, normalized_root).replace("\\", "/")
                        file_stat = file_path.stat()
                        mtime_ns = int(file_stat.st_mtime_ns)
                        size_bytes = int(file_stat.st_size)
                    except (FileNotFoundError, PermissionError, OSError):
                        continue

                    progress.processed += 1
                    existing = existing_map.pop(absolute_path, None)
                    unchanged_file = (
                        existing is not None
                        and existing[0] == mtime_ns
                        and existing[1] == size_bytes
                        and existing[2] == 1
                        and not full_rescan
                    )

                    if unchanged_file:
                        progress.unchanged += 1
                    else:
                        metadata = self._extract_metadata(file_path)
                        timestamp = utc_now_iso()

                        if existing is None:
                            cursor.execute(
                                """
                                INSERT INTO songs (
                                    root_path, path, relative_path, filename, extension,
                                    title, artist, album, year, size_bytes, mtime_ns,
                                    active, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                                """,
                                (
                                    normalized_root,
                                    absolute_path,
                                    relative_path,
                                    file_path.name,
                                    file_path.suffix.lower(),
                                    metadata["title"],
                                    metadata["artist"],
                                    metadata["album"],
                                    metadata["year"],
                                    size_bytes,
                                    mtime_ns,
                                    timestamp,
                                    timestamp,
                                ),
                            )
                            progress.new += 1
                        else:
                            cursor.execute(
                                """
                                UPDATE songs
                                SET
                                    relative_path = ?,
                                    filename = ?,
                                    extension = ?,
                                    title = ?,
                                    artist = ?,
                                    album = ?,
                                    year = ?,
                                    size_bytes = ?,
                                    mtime_ns = ?,
                                    active = 1,
                                    updated_at = ?
                                WHERE path = ?
                                """,
                                (
                                    relative_path,
                                    file_path.name,
                                    file_path.suffix.lower(),
                                    metadata["title"],
                                    metadata["artist"],
                                    metadata["album"],
                                    metadata["year"],
                                    size_bytes,
                                    mtime_ns,
                                    timestamp,
                                    absolute_path,
                                ),
                            )

                            if existing[2] == 0:
                                progress.new += 1
                            else:
                                progress.modified += 1

                    if progress.processed % 250 == 0:
                        connection.commit()

                    if progress.processed % 200 == 0:
                        cursor.execute(
                            """
                            UPDATE scan_runs
                            SET
                                processed_files = ?,
                                new_files = ?,
                                modified_files = ?,
                                deleted_files = ?,
                                unchanged_files = ?
                            WHERE scan_id = ?
                            """,
                            (
                                progress.processed,
                                progress.new,
                                progress.modified,
                                progress.deleted,
                                progress.unchanged,
                                scan_id,
                            ),
                        )
                        connection.commit()

                        if progress_callback:
                            progress_callback(progress)

                stale_active_paths = [
                    path for path, state in existing_map.items() if int(state[2]) == 1
                ]
                if stale_active_paths:
                    timestamp = utc_now_iso()
                    cursor.executemany(
                        "UPDATE songs SET active = 0, updated_at = ? WHERE path = ?",
                        [(timestamp, stale_path) for stale_path in stale_active_paths],
                    )
                    progress.deleted += len(stale_active_paths)

                connection.commit()

            self._update_scan_run(scan_id, progress, status="completed", finished=True)
            if progress_callback:
                progress_callback(progress)

            return {
                "scan_id": scan_id,
                "status": "completed",
                "root_path": normalized_root,
                "processed_files": progress.processed,
                "new_files": progress.new,
                "modified_files": progress.modified,
                "deleted_files": progress.deleted,
                "unchanged_files": progress.unchanged,
                "extensions": sorted(extension_set),
                "recursive": recursive,
                "full_rescan": full_rescan,
            }
        except Exception as exc:
            self._update_scan_run(
                scan_id,
                progress,
                status="failed",
                error=str(exc),
                finished=True,
            )
            raise

    def get_scan_run(self, scan_id: str) -> Optional[dict[str, object]]:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    scan_id,
                    root_path,
                    status,
                    started_at,
                    finished_at,
                    processed_files,
                    new_files,
                    modified_files,
                    deleted_files,
                    unchanged_files,
                    error
                FROM scan_runs
                WHERE scan_id = ?
                """,
                (scan_id,),
            ).fetchone()

        if row is None:
            return None

        return self._scan_run_row_to_dict(row)

    def get_latest_scan_run(self) -> Optional[dict[str, object]]:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    scan_id,
                    root_path,
                    status,
                    started_at,
                    finished_at,
                    processed_files,
                    new_files,
                    modified_files,
                    deleted_files,
                    unchanged_files,
                    error
                FROM scan_runs
                ORDER BY started_at DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return self._scan_run_row_to_dict(row)

    def list_catalog(
        self,
        query: str = "",
        offset: int = 0,
        limit: int = DEFAULT_LIMIT,
        sort: str = "title",
        include_inactive: bool = False,
        root_path: Optional[str] = None,
        dedupe: bool = False,
    ) -> dict[str, object]:
        safe_offset = max(offset, 0)
        safe_limit = max(1, min(limit, MAX_LIMIT))
        normalized_query = query.strip().lower()

        sort_map = {
            "title": "title COLLATE NOCASE ASC, artist COLLATE NOCASE ASC",
            "artist": "artist COLLATE NOCASE ASC, title COLLATE NOCASE ASC",
            "updated": "updated_at DESC",
            "newest": "created_at DESC",
        }
        order_by = sort_map.get(sort, sort_map["title"])

        where_clauses: list[str] = []
        params: list[object] = []

        if not include_inactive:
            where_clauses.append("active = 1")

        if root_path:
            normalized_root = normalize_path(Path(root_path))
            where_clauses.append("root_path = ?")
            params.append(normalized_root)

        if normalized_query:
            like_query = f"%{normalized_query}%"
            where_clauses.append(
                "("  # nosec B608 - parameters are bound separately
                "LOWER(title) LIKE ? OR "
                "LOWER(artist) LIKE ? OR "
                "LOWER(album) LIKE ? OR "
                "LOWER(filename) LIKE ? OR "
                "LOWER(relative_path) LIKE ?"
                ")"
            )
            params.extend([like_query, like_query, like_query, like_query, like_query])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        if dedupe:
            cte_sql = f"""
                WITH ranked AS (
                    SELECT
                        id,
                        root_path,
                        path,
                        relative_path,
                        filename,
                        extension,
                        title,
                        artist,
                        album,
                        year,
                        size_bytes,
                        mtime_ns,
                        active,
                        created_at,
                        updated_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY LOWER(title), LOWER(artist), COALESCE(year, -1)
                            ORDER BY updated_at DESC, id DESC
                        ) AS rn
                    FROM songs
                    {where_sql}
                )
            """

            with self._connection() as connection:
                total = int(
                    connection.execute(
                        f"""
                        {cte_sql}
                        SELECT COUNT(*) AS total
                        FROM ranked
                        WHERE rn = 1
                        """,
                        params,
                    ).fetchone()["total"]
                )

                rows = connection.execute(
                    f"""
                    {cte_sql}
                    SELECT
                        id,
                        root_path,
                        path,
                        relative_path,
                        filename,
                        extension,
                        title,
                        artist,
                        album,
                        year,
                        size_bytes,
                        mtime_ns,
                        active,
                        created_at,
                        updated_at
                    FROM ranked
                    WHERE rn = 1
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                    """,
                    [*params, safe_limit, safe_offset],
                ).fetchall()
        else:
            with self._connection() as connection:
                total = int(
                    connection.execute(
                        f"SELECT COUNT(*) AS total FROM songs {where_sql}",
                        params,
                    ).fetchone()["total"]
                )

                rows = connection.execute(
                    f"""
                    SELECT
                        id,
                        root_path,
                        path,
                        relative_path,
                        filename,
                        extension,
                        title,
                        artist,
                        album,
                        year,
                        size_bytes,
                        mtime_ns,
                        active,
                        created_at,
                        updated_at
                    FROM songs
                    {where_sql}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                    """,
                    [*params, safe_limit, safe_offset],
                ).fetchall()

        songs = [self._song_row_to_dict(row) for row in rows]
        return {
            "pagination": {
                "offset": safe_offset,
                "limit": safe_limit,
                "total": total,
                "has_more": safe_offset + safe_limit < total,
            },
            "songs": songs,
        }

    def get_catalog_tree(self) -> dict[str, object]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT root_path, relative_path FROM songs WHERE active=1"
            ).fetchall()

        roots: dict[str, dict[str, object]] = {}

        for root_path, rel_path in rows:
            normalized_root = str(root_path or "default")
            root_node = roots.setdefault(normalized_root, {"count": 0, "children": {}})

            parent_parts = Path(str(rel_path)).parent.parts
            clean_parts = [part for part in parent_parts if part and part != "."]

            current = root_node
            current["count"] = int(current.get("count", 0)) + 1

            for part in clean_parts:
                children = current.setdefault("children", {})
                if not isinstance(children, dict):
                    children = {}
                    current["children"] = children

                child = children.setdefault(part, {"count": 0, "children": {}})
                if not isinstance(child, dict):
                    child = {"count": 0, "children": {}}
                    children[part] = child

                child["count"] = int(child.get("count", 0)) + 1
                current = child

        return roots

    def list_changes(self, since: Optional[str], limit: int = DEFAULT_LIMIT) -> dict[str, object]:
        safe_limit = max(1, min(limit, MAX_CHANGES_LIMIT))
        params: list[object] = [safe_limit]

        where_sql = ""
        if since:
            where_sql = "WHERE updated_at > ?"
            params = [since, safe_limit]

        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    id,
                    root_path,
                    path,
                    relative_path,
                    filename,
                    extension,
                    title,
                    artist,
                    album,
                    year,
                    size_bytes,
                    mtime_ns,
                    active,
                    created_at,
                    updated_at
                FROM songs
                {where_sql}
                ORDER BY updated_at ASC
                LIMIT ?
                """,
                params,
            ).fetchall()

        return {
            "changes": [self._song_row_to_dict(row) for row in rows],
            "count": len(rows),
        }

    @staticmethod
    def _song_row_to_dict(row: sqlite3.Row) -> dict[str, object]:
        return {
            "id": int(row["id"]),
            "root_path": row["root_path"],
            "path": row["path"],
            "relative_path": row["relative_path"],
            "filename": row["filename"],
            "extension": row["extension"],
            "title": row["title"],
            "artist": row["artist"],
            "album": row["album"],
            "year": row["year"],
            "size_bytes": int(row["size_bytes"]),
            "mtime_ns": int(row["mtime_ns"]),
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _scan_run_row_to_dict(row: sqlite3.Row) -> dict[str, object]:
        return {
            "scan_id": row["scan_id"],
            "root_path": row["root_path"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "processed_files": int(row["processed_files"]),
            "new_files": int(row["new_files"]),
            "modified_files": int(row["modified_files"]),
            "deleted_files": int(row["deleted_files"]),
            "unchanged_files": int(row["unchanged_files"]),
            "error": row["error"],
        }
