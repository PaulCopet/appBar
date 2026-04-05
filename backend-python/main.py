import json
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from music_index import DEFAULT_EXTENSIONS, MusicIndexService

app = FastAPI(title="Python Microservice API")

SERVICE_ROOT = Path(__file__).resolve().parent
DATA_DIR = SERVICE_ROOT / "data"

DEFAULT_MUSIC_PATH = os.getenv("MUSIC_LIBRARY_PATH", "").strip()
MUSIC_INDEX_DB = Path(os.getenv("MUSIC_INDEX_DB", str(DATA_DIR / "music-index.db")))
MUSIC_CONFIG_PATH = Path(os.getenv("MUSIC_CONFIG_PATH", str(DATA_DIR / "music-config.json")))
FRONTEND_STATUS_URL = os.getenv("FRONTEND_STATUS_URL", "http://127.0.0.1:5173")
NODE_STATUS_URL = os.getenv("NODE_STATUS_URL", "http://127.0.0.1:3000/api/status")
AUTO_SCAN_ENV_DEFAULT = os.getenv("MUSIC_AUTO_SCAN_ON_START", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if origin.strip()
]

music_index = MusicIndexService(MUSIC_INDEX_DB)
_active_scans: set[str] = set()
_scan_lock = threading.Lock()
_last_scan_id: str | None = None
_app_started_at = time.time()


def _default_config() -> dict[str, Any]:
    return {
        "library_path": DEFAULT_MUSIC_PATH,
        "auto_scan_on_start": AUTO_SCAN_ENV_DEFAULT,
    }


def _load_music_config() -> dict[str, Any]:
    config = _default_config()

    if not MUSIC_CONFIG_PATH.exists():
        return config

    try:
        payload = json.loads(MUSIC_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config

    if isinstance(payload, dict):
        library_path = str(payload.get("library_path", "")).strip()
        config["library_path"] = library_path

        auto_scan = payload.get("auto_scan_on_start")
        if isinstance(auto_scan, bool):
            config["auto_scan_on_start"] = auto_scan

    return config


def _save_music_config(config: dict[str, Any]) -> None:
    MUSIC_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    MUSIC_CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


music_config = _load_music_config()


# Configurar CORS para permitir que el frontend se comunique con este servicio
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MusicScanRequest(BaseModel):
    path: str = Field(default="", description="Carpeta raiz a escanear")
    full_rescan: bool = Field(default=False, description="Si true, fuerza recargar metadata")
    recursive: bool = Field(default=True, description="Si true, incluye subcarpetas")
    extensions: list[str] | None = Field(
        default=None,
        description="Extensiones de audio permitidas; por defecto usa formato comun",
    )


class MusicConfigRequest(BaseModel):
    path: str | None = Field(default=None, description="Ruta de biblioteca por defecto")
    auto_scan_on_start: bool | None = Field(
        default=None,
        description="Si true, inicia escaneo automaticamente al levantar Python",
    )


def _current_library_path() -> str:
    configured = str(music_config.get("library_path", "")).strip()
    if configured:
        return configured

    return DEFAULT_MUSIC_PATH


def _resolve_music_root(request_path: str) -> str:
    selected_path = request_path.strip() or _current_library_path()
    if not selected_path:
        raise HTTPException(
            status_code=400,
            detail="Debes enviar path en el request o configurar una ruta por defecto",
        )

    root = Path(selected_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"La ruta no existe o no es una carpeta valida: {root}",
        )

    return str(root)


def _probe_url(url: str, timeout_seconds: float = 1.5) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(2048).decode("utf-8", errors="ignore")
            parsed: Any = None

            if body:
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = None

            return {
                "url": url,
                "online": True,
                "status_code": response.status,
                "payload": parsed,
            }
    except urllib.error.URLError as exc:
        return {
            "url": url,
            "online": False,
            "status_code": None,
            "error": str(exc.reason) if getattr(exc, "reason", None) else str(exc),
        }
    except Exception as exc:
        return {
            "url": url,
            "online": False,
            "status_code": None,
            "error": str(exc),
        }


def _run_scan_job(
    *,
    scan_id: str,
    root_path: str,
    full_rescan: bool,
    recursive: bool,
    extensions: list[str] | None,
) -> None:
    try:
        music_index.scan_library(
            scan_id=scan_id,
            root_path=root_path,
            full_rescan=full_rescan,
            recursive=recursive,
            extensions=extensions,
        )
    except Exception as exc:
        print(f"[music-scan] Scan failed ({scan_id}): {exc}")
    finally:
        with _scan_lock:
            _active_scans.discard(scan_id)


def _start_scan(
    *,
    path: str,
    full_rescan: bool,
    recursive: bool,
    extensions: list[str] | None,
) -> dict[str, Any]:
    scan_root = _resolve_music_root(path)

    with _scan_lock:
        if _active_scans:
            raise HTTPException(
                status_code=409,
                detail="Ya hay un escaneo en progreso. Espera a que finalice o consulta su estado.",
            )

        scan_id = f"scan-{uuid.uuid4().hex[:12]}"
        _active_scans.add(scan_id)

    global _last_scan_id
    _last_scan_id = scan_id

    worker = threading.Thread(
        target=_run_scan_job,
        kwargs={
            "scan_id": scan_id,
            "root_path": scan_root,
            "full_rescan": full_rescan,
            "recursive": recursive,
            "extensions": extensions,
        },
        daemon=True,
        name=f"music-scan-{scan_id}",
    )
    worker.start()

    return {
        "scan_id": scan_id,
        "status": "in_progress",
        "root_path": scan_root,
        "recursive": recursive,
        "full_rescan": full_rescan,
        "extensions": extensions or sorted(DEFAULT_EXTENSIONS),
    }


@app.on_event("startup")
def on_startup() -> None:
    should_auto_scan = bool(music_config.get("auto_scan_on_start", True))
    if not should_auto_scan:
        return

    configured_path = _current_library_path().strip()
    if not configured_path:
        return

    try:
        started = _start_scan(
            path=configured_path,
            full_rescan=False,
            recursive=True,
            extensions=None,
        )
        print(
            f"[music-scan] Auto scan iniciado. scan_id={started['scan_id']} root={started['root_path']}"
        )
    except HTTPException as exc:
        print(f"[music-scan] Auto scan omitido: {exc.detail}")
    except Exception as exc:
        print(f"[music-scan] Auto scan error: {exc}")


@app.get("/")
def read_root():
    return {
        "message": "Python Music Service online",
        "admin": "Desktop UI disponible con start_all.py",
    }


@app.get("/api/ai/status")
def read_status():
    return {
        "service": "FastAPI ML Service",
        "status": "online",
        "models_loaded": 3,
        "uptime_seconds": int(time.time() - _app_started_at),
    }


@app.get("/api/system/status")
def get_system_status():
    latest_scan = music_index.get_scan_run(_last_scan_id) if _last_scan_id else music_index.get_latest_scan_run()
    node = _probe_url(NODE_STATUS_URL)
    frontend = _probe_url(FRONTEND_STATUS_URL)

    return {
        "python": {
            "online": True,
            "uptime_seconds": int(time.time() - _app_started_at),
            "active_scans": len(_active_scans),
        },
        "node": node,
        "frontend": frontend,
        "latest_scan": latest_scan,
    }


@app.get("/api/music/config")
def get_music_config():
    return {
        "library_path": _current_library_path(),
        "auto_scan_on_start": bool(music_config.get("auto_scan_on_start", True)),
    }


@app.put("/api/music/config")
def update_music_config(request: MusicConfigRequest):
    if request.path is not None:
        normalized_path = request.path.strip()

        if normalized_path:
            root = Path(normalized_path).expanduser().resolve()
            if not root.exists() or not root.is_dir():
                raise HTTPException(
                    status_code=400,
                    detail=f"La ruta no existe o no es carpeta: {root}",
                )
            music_config["library_path"] = str(root)
        else:
            music_config["library_path"] = ""

    if request.auto_scan_on_start is not None:
        music_config["auto_scan_on_start"] = bool(request.auto_scan_on_start)

    _save_music_config(music_config)
    return get_music_config()


@app.post("/api/music/scan")
def start_music_scan(request: MusicScanRequest):
    return _start_scan(
        path=request.path,
        full_rescan=request.full_rescan,
        recursive=request.recursive,
        extensions=request.extensions,
    )


@app.get("/api/music/scan/latest")
def get_latest_scan_status():
    run = music_index.get_scan_run(_last_scan_id) if _last_scan_id else music_index.get_latest_scan_run()
    if run is None:
        return {
            "status": "not_started",
            "detail": "Todavia no se ha ejecutado ningun escaneo",
        }

    return run


@app.get("/api/music/scan/{scan_id}")
def get_scan_status(scan_id: str):
    run = music_index.get_scan_run(scan_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No existe un escaneo con ese scan_id")

    return run


@app.get("/api/music/catalog")
def get_music_catalog(
    q: str = Query(default=""),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    sort: str = Query(default="title"),
    include_inactive: bool = Query(default=False),
    root_path: str | None = Query(default=None),
    dedupe: bool = Query(default=True),
):
    return music_index.list_catalog(
        query=q,
        offset=offset,
        limit=limit,
        sort=sort,
        include_inactive=include_inactive,
        root_path=root_path,
        dedupe=dedupe,
    )


@app.get("/api/music/changes")
def get_music_changes(
    since: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=5000),
):
    return music_index.list_changes(since=since, limit=limit)

@app.get("/api/music/stats/tree")
def get_music_stats_tree():
    return music_index.get_catalog_tree()

@app.get("/api/music/stats/tree")
def get_music_stats_tree():
    return music_index.get_catalog_tree()

