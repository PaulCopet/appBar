from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Callable

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except Exception:  # pragma: no cover - safety fallback for environments without Tk.
    tk = None
    filedialog = None
    messagebox = None
    ttk = None

ROOT_DIR = Path(__file__).resolve().parent
LOG_DIR = ROOT_DIR / '.runtime' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
MANAGED_PORTS = (8000, 3000, 5173, 5174)

PYTHON_BASE = 'http://127.0.0.1:8000'
NODE_BASE = 'http://127.0.0.1:3000'
FRONT_BASE = 'http://127.0.0.1:5173'


ServiceDescriptor = dict[str, Any]
ApiResult = tuple[bool, int | None, dict[str, Any]]


def _cmd(name: str) -> str:
    if os.name == 'nt':
        return f'{name}.cmd'
    return name


def _service_health_url(name: str) -> str | None:
    if name == 'python':
        return f'{PYTHON_BASE}/api/ai/status'
    if name == 'node':
        return f'{NODE_BASE}/api/status'
    if name == 'frontend':
        return FRONT_BASE
    return None


def _is_endpoint_online(url: str, timeout: float = 1.2) -> bool:
    ok, _, _ = _http_json('GET', url, timeout=timeout)
    return ok


def _tool_bin(project_dir: Path, tool_name: str) -> str | None:
    executable = f'{tool_name}.cmd' if os.name == 'nt' else tool_name
    candidate = project_dir / 'node_modules' / '.bin' / executable
    if candidate.exists():
        return str(candidate)
    return None


def _find_listening_pids(port: int) -> set[int]:
    if os.name == 'nt':
        try:
            output = subprocess.check_output(
                ['netstat', '-ano'],
                text=True,
                encoding='utf-8',
                errors='ignore',
            )
        except Exception:
            return set()

        pids: set[int] = set()
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue

            proto = parts[0].upper()
            local_addr = parts[1]
            pid_text = parts[-1]
            state = parts[3].upper() if proto.startswith('TCP') and len(parts) >= 5 else ''

            if not pid_text.isdigit():
                continue

            if proto.startswith('TCP'):
                if state != 'LISTENING':
                    continue
            elif not proto.startswith('UDP'):
                continue

            _, sep, raw_port = local_addr.rpartition(':')
            if not sep:
                continue

            try:
                local_port = int(raw_port)
            except ValueError:
                continue

            if local_port != port:
                continue

            pid = int(pid_text)
            if pid != os.getpid():
                pids.add(pid)

        return pids

    try:
        output = subprocess.check_output(
            ['lsof', '-ti', f'tcp:{port}'],
            text=True,
            encoding='utf-8',
            errors='ignore',
        )
    except Exception:
        return set()

    pids = set()
    for line in output.splitlines():
        value = line.strip()
        if value.isdigit():
            pid = int(value)
            if pid != os.getpid():
                pids.add(pid)
    return pids


def _kill_pid_tree(pid: int) -> None:
    if pid <= 0 or pid == os.getpid():
        return

    if os.name == 'nt':
        subprocess.run(
            ['taskkill', '/PID', str(pid), '/T', '/F'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return

    try:
        os.kill(pid, 15)
    except Exception:
        pass


def _free_managed_ports(ports: tuple[int, ...] = MANAGED_PORTS) -> None:
    pids: set[int] = set()
    for port in ports:
        pids.update(_find_listening_pids(port))

    for pid in sorted(pids):
        _kill_pid_tree(pid)


def _open_log(name: str):
    log_path = LOG_DIR / f'{name}.log'
    handle = open(log_path, 'a', encoding='utf-8')
    handle.write(f"\n===== START {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    handle.flush()
    return handle, log_path


def _start_service(
    name: str,
    command: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> ServiceDescriptor:
    log_handle, log_path = _open_log(name)
    process = subprocess.Popen(
        command,
        cwd=str(cwd or ROOT_DIR),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env={**os.environ, **(env or {})},
        creationflags=CREATE_NO_WINDOW,
    )
    return {
        'name': name,
        'process': process,
        'log_handle': log_handle,
        'log_path': log_path,
        'command': command,
    }


def _stop_service(service: ServiceDescriptor) -> None:
    process: subprocess.Popen[Any] = service['process']

    if process.poll() is None:
        if os.name == 'nt':
            subprocess.run(
                ['taskkill', '/PID', str(process.pid), '/T', '/F'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        else:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    log_handle = service.get('log_handle')
    if log_handle and not log_handle.closed:
        log_handle.write(f"===== STOP {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        log_handle.close()


def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 8.0,
) -> ApiResult:
    headers: dict[str, str] = {}
    body: bytes | None = None

    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'

    request = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode('utf-8', errors='ignore')
            parsed: Any
            if raw:
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = {'raw': raw}
            else:
                parsed = {}

            if isinstance(parsed, dict):
                return True, response.status, parsed

            return True, response.status, {'payload': parsed}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='ignore')
        parsed_error: Any = {'raw': raw}
        if raw:
            try:
                parsed_error = json.loads(raw)
            except json.JSONDecodeError:
                pass

        if isinstance(parsed_error, dict):
            return False, exc.code, parsed_error

        return False, exc.code, {'payload': parsed_error}
    except Exception as exc:
        return False, None, {'detail': str(exc)}


def _wait_for_endpoint(url: str, timeout_seconds: float = 30.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        ok, _, _ = _http_json('GET', url, timeout=1.5)
        if ok:
            return True
        time.sleep(0.35)
    return False


def _extract_error(payload: dict[str, Any]) -> str:
    detail = payload.get('detail')
    if isinstance(detail, str) and detail.strip():
        return detail

    raw = payload.get('raw')
    if isinstance(raw, str) and raw.strip():
        return raw

    return str(payload)


class ServiceRuntime:
    def __init__(self) -> None:
        self.services: list[ServiceDescriptor] = []

    def start(self) -> tuple[bool, str]:
        self.stop()
        _free_managed_ports()

        python_env = {
            'MUSIC_AUTO_SCAN_ON_START': 'true',
        }

        try:
            python_dir = ROOT_DIR / 'backend-python'
            node_dir = ROOT_DIR / 'backend-node'
            front_dir = ROOT_DIR / 'frontend'

            node_runner = _tool_bin(node_dir, 'tsx')
            front_runner = _tool_bin(front_dir, 'vite')

            node_command = [node_runner, 'index.ts'] if node_runner else [_cmd('npm'), 'run', 'dev']
            front_command = (
                [front_runner, '--host', '127.0.0.1', '--port', '5173', '--strictPort']
                if front_runner
                else [_cmd('npm'), 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5173', '--strictPort']
            )

            self.services.append(
                _start_service(
                    'python',
                    [
                        sys.executable,
                        '-m',
                        'uvicorn',
                        'main:app',
                        '--host',
                        '127.0.0.1',
                        '--port',
                        '8000',
                    ],
                    env=python_env,
                    cwd=python_dir,
                )
            )

            time.sleep(0.8)

            self.services.append(
                _start_service(
                    'node',
                    node_command,
                    cwd=node_dir,
                )
            )

            time.sleep(0.8)

            self.services.append(
                _start_service(
                    'frontend',
                    front_command,
                    cwd=front_dir,
                )
            )

            python_ready = _wait_for_endpoint(f'{PYTHON_BASE}/api/ai/status', timeout_seconds=30)
            if not python_ready:
                return False, 'Python API no inicio correctamente. Revisa los logs ocultos.'

            node_ready = _wait_for_endpoint(f'{NODE_BASE}/api/status', timeout_seconds=15)
            if not node_ready:
                return False, 'Node API no inicio correctamente. Revisa los logs ocultos.'

            front_ready = _wait_for_endpoint(FRONT_BASE, timeout_seconds=15)
            if not front_ready:
                return False, 'Frontend no inicio correctamente en el puerto 5173. Revisa los logs ocultos.'

            return True, ''
        except Exception as exc:
            return False, str(exc)

    def stop(self) -> None:
        for service in reversed(self.services):
            try:
                _stop_service(service)
            except Exception:
                # Evita que un fallo en un proceso impida apagar el resto.
                pass
        self.services.clear()
        _free_managed_ports()

    def stopped_services(self) -> list[ServiceDescriptor]:
        stopped: list[ServiceDescriptor] = []
        for service in self.services:
            if service['process'].poll() is None:
                continue

            health_url = _service_health_url(service['name'])
            if health_url and _is_endpoint_online(health_url):
                continue

            stopped.append(service)

        return stopped

    def logs_text(self) -> str:
        lines = []
        for service in self.services:
            lines.append(f"{service['name']}: {service['log_path']}")
        return '\n'.join(lines)


class DesktopAdminApp:
    def __init__(self, runtime: ServiceRuntime) -> None:
        if tk is None or ttk is None or filedialog is None or messagebox is None:
            raise RuntimeError('Tkinter no esta disponible en este entorno.')

        self.runtime = runtime
        self.root = tk.Tk()
        self.root.title('Python Music Admin')
        self.root.geometry('940x670')
        self.root.minsize(860, 620)
        self.root.configure(bg='#07130a')

        self._closing = False
        self._refresh_in_progress = False
        self._service_error_reported = False

        self.python_status_var = tk.StringVar(value='cargando...')
        self.node_status_var = tk.StringVar(value='cargando...')
        self.frontend_status_var = tk.StringVar(value='cargando...')

        self.library_path_var = tk.StringVar(value='')
        self.auto_scan_var = tk.BooleanVar(value=True)
        self.full_rescan_var = tk.BooleanVar(value=False)

        self.scan_id_var = tk.StringVar(value='-')
        self.scan_status_var = tk.StringVar(value='not_started')
        self.scan_stats_var = tk.StringVar(value='procesados=0 | new=0 | mod=0 | del=0')
        self.catalog_total_var = tk.StringVar(value='0')
        self.detected_library_path_var = tk.StringVar(value='(sin ruta configurada)')

        self.message_var = tk.StringVar(value='Servicios iniciados. Cargando estado...')
        self.logs_var = tk.StringVar(value=self.runtime.logs_text())

        self.library_entry: Any = None
        self.message_label: Any = None

        self._build_styles()
        self._build_ui()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

        self._refresh_async('Sincronizando estado inicial...')
        self._schedule_periodic_checks()

    def _build_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('Main.TFrame', background='#07130a')
        style.configure('Card.TLabelframe', background='#0d1d11', foreground='#7eff6f')
        style.configure('Card.TLabelframe.Label', background='#0d1d11', foreground='#7eff6f')
        style.configure('TLabel', background='#0d1d11', foreground='#c6ffd0')
        style.configure('Dim.TLabel', background='#0d1d11', foreground='#84b88e')
        style.configure('Status.TLabel', background='#0d1d11', foreground='#7eff6f')
        style.configure('Message.TLabel', background='#07130a', foreground='#88d592')

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14, style='Main.TFrame')
        main.pack(fill='both', expand=True)

        title = ttk.Label(
            main,
            text='Python Music Admin (Desktop UI)',
            style='Status.TLabel',
            font=('Consolas', 14, 'bold'),
        )
        title.pack(anchor='w', pady=(0, 10))

        status_card = ttk.LabelFrame(main, text='Estado de servicios', style='Card.TLabelframe', padding=10)
        status_card.pack(fill='x', pady=(0, 8))

        status_grid = ttk.Frame(status_card, style='Main.TFrame')
        status_grid.pack(fill='x')

        self._status_label(status_grid, 'Python', self.python_status_var, 0)
        self._status_label(status_grid, 'Node API', self.node_status_var, 1)
        self._status_label(status_grid, 'Frontend', self.frontend_status_var, 2)

        config_card = ttk.LabelFrame(main, text='Configuracion de biblioteca', style='Card.TLabelframe', padding=10)
        config_card.pack(fill='x', pady=(0, 8))

        ttk.Label(config_card, text='Ruta de biblioteca:', style='Dim.TLabel').grid(row=0, column=0, sticky='w')

        self.library_entry = ttk.Entry(config_card, textvariable=self.library_path_var, width=88)
        self.library_entry.grid(row=1, column=0, columnspan=3, sticky='ew', pady=(4, 8))

        browse_button = ttk.Button(config_card, text='Examinar...', command=self._on_browse_path)
        browse_button.grid(row=1, column=3, sticky='e', padx=(8, 0), pady=(4, 8))

        auto_scan_checkbox = ttk.Checkbutton(
            config_card,
            text='Auto escanear al iniciar Python',
            variable=self.auto_scan_var,
        )
        auto_scan_checkbox.grid(row=2, column=0, sticky='w')

        full_rescan_checkbox = ttk.Checkbutton(
            config_card,
            text='Full rescan para el proximo escaneo',
            variable=self.full_rescan_var,
        )
        full_rescan_checkbox.grid(row=2, column=1, sticky='w')

        config_card.columnconfigure(0, weight=1)
        config_card.columnconfigure(1, weight=1)
        config_card.columnconfigure(2, weight=1)

        actions_card = ttk.LabelFrame(main, text='Acciones', style='Card.TLabelframe', padding=10)
        actions_card.pack(fill='x', pady=(0, 8))

        ttk.Button(actions_card, text='Guardar configuracion', command=self._on_save_config).grid(
            row=0,
            column=0,
            padx=(0, 8),
            pady=(0, 8),
            sticky='w',
        )
        ttk.Button(actions_card, text='Iniciar escaneo', command=self._on_start_scan).grid(
            row=0,
            column=1,
            padx=(0, 8),
            pady=(0, 8),
            sticky='w',
        )
        ttk.Button(actions_card, text='Refrescar estado', command=lambda: self._refresh_async('Actualizando estado...')).grid(
            row=0,
            column=2,
            padx=(0, 8),
            pady=(0, 8),
            sticky='w',
        )
        ttk.Button(actions_card, text='Abrir frontend', command=lambda: webbrowser.open(FRONT_BASE)).grid(
            row=0,
            column=3,
            pady=(0, 8),
            sticky='w',
        )
        ttk.Button(actions_card, text='Abrir carpeta de logs', command=self._on_open_logs_folder).grid(
            row=1,
            column=0,
            padx=(0, 8),
            sticky='w',
        )
        ttk.Button(actions_card, text='Cerrar servicios y salir', command=self._on_close).grid(
            row=1,
            column=1,
            padx=(0, 8),
            sticky='w',
        )

        scan_card = ttk.LabelFrame(main, text='Estado de escaneo', style='Card.TLabelframe', padding=10)
        scan_card.pack(fill='x', pady=(0, 8))

        ttk.Label(scan_card, text='Scan ID:', style='Dim.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(scan_card, textvariable=self.scan_id_var, style='Status.TLabel').grid(row=0, column=1, sticky='w')

        ttk.Label(scan_card, text='Estado:', style='Dim.TLabel').grid(row=1, column=0, sticky='w')
        ttk.Label(scan_card, textvariable=self.scan_status_var, style='Status.TLabel').grid(row=1, column=1, sticky='w')

        ttk.Label(scan_card, text='Estadisticas:', style='Dim.TLabel').grid(row=2, column=0, sticky='w')
        ttk.Label(scan_card, textvariable=self.scan_stats_var, style='Status.TLabel').grid(row=2, column=1, sticky='w')

        ttk.Label(scan_card, text='Total catalogo:', style='Dim.TLabel').grid(row=3, column=0, sticky='w')
        ttk.Label(scan_card, textvariable=self.catalog_total_var, style='Status.TLabel').grid(row=3, column=1, sticky='w')

        ttk.Label(scan_card, text='Ruta activa detectada:', style='Dim.TLabel').grid(row=4, column=0, sticky='w')
        detected_path_label = ttk.Label(
            scan_card,
            textvariable=self.detected_library_path_var,
            style='Status.TLabel',
            justify='left',
        )
        detected_path_label.grid(row=4, column=1, sticky='w')
        detected_path_label.configure(wraplength=700)

        logs_card = ttk.LabelFrame(main, text='Logs ocultos', style='Card.TLabelframe', padding=10)
        logs_card.pack(fill='x', pady=(0, 8))

        ttk.Label(logs_card, textvariable=self.logs_var, justify='left', style='Dim.TLabel').pack(anchor='w')

        self.message_label = ttk.Label(main, textvariable=self.message_var, style='Message.TLabel')
        self.message_label.pack(fill='x', pady=(4, 0))

    def _status_label(self, parent: Any, title: str, variable: Any, column: int) -> None:
        card = ttk.Frame(parent, style='Main.TFrame')
        card.grid(row=0, column=column, sticky='nsew', padx=(0 if column == 0 else 10, 0))
        ttk.Label(card, text=title, style='Dim.TLabel').pack(anchor='w')
        ttk.Label(card, textvariable=variable, style='Status.TLabel').pack(anchor='w')
        parent.columnconfigure(column, weight=1)

    def _set_message(self, text: str, is_error: bool = False) -> None:
        self.message_var.set(text)
        if self.message_label is not None:
            foreground = '#ff7373' if is_error else '#88d592'
            self.message_label.configure(foreground=foreground)

    def _safe_after(self, delay_ms: int, callback: Callable[[], None]) -> bool:
        if self._closing:
            return False

        def guarded_callback() -> None:
            if self._closing:
                return
            callback()

        try:
            self.root.after(delay_ms, guarded_callback)
            return True
        except Exception:
            return False

    def _schedule_periodic_checks(self) -> None:
        self._monitor_services()
        self._periodic_refresh()

    def _periodic_refresh(self) -> None:
        if self._closing:
            return

        self._refresh_async()
        self._safe_after(4500, self._periodic_refresh)

    def _monitor_services(self) -> None:
        if self._closing:
            return

        stopped = self.runtime.stopped_services()
        if stopped:
            names = ', '.join([service['name'] for service in stopped])
            details = '\n'.join([f"{service['name']}: {service['log_path']}" for service in stopped])
            self._set_message(f'Servicios detenidos: {names}. Revisa logs.', is_error=True)

            if not self._service_error_reported:
                self._service_error_reported = True
                messagebox.showerror(
                    'Servicio detenido',
                    f'Uno o mas servicios se detuvieron: {names}\n\n{details}',
                )
        else:
            self._service_error_reported = False

        self._safe_after(1800, self._monitor_services)

    def _on_browse_path(self) -> None:
        initial_dir = self.library_path_var.get().strip() or str(Path.home())
        selected = filedialog.askdirectory(initialdir=initial_dir)
        if selected:
            self.library_path_var.set(selected)

    def _on_open_logs_folder(self) -> None:
        try:
            if os.name == 'nt':
                os.startfile(LOG_DIR)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(LOG_DIR)])
            else:
                subprocess.Popen(['xdg-open', str(LOG_DIR)])
        except Exception as exc:
            self._set_message(f'No se pudo abrir la carpeta de logs: {exc}', is_error=True)

    def _run_background_action(
        self,
        action_name: str,
        worker: Callable[[], ApiResult],
        on_success: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if self._closing:
            return

        self._set_message(action_name)

        def job() -> None:
            ok, _, payload = worker()

            def after() -> None:
                if self._closing:
                    return

                if not ok:
                    self._set_message(_extract_error(payload), is_error=True)
                    return

                if on_success is not None:
                    on_success(payload)

                self._refresh_async('Estado actualizado.')

            self._safe_after(0, after)

        threading.Thread(target=job, daemon=True).start()

    def _on_save_config(self) -> None:
        payload = {
            'path': self.library_path_var.get().strip(),
            'auto_scan_on_start': bool(self.auto_scan_var.get()),
        }

        def worker() -> ApiResult:
            return _http_json('PUT', f'{PYTHON_BASE}/api/music/config', payload=payload)

        def on_success(response: dict[str, Any]) -> None:
            path_value = str(response.get('library_path', '')).strip() or '(vacia)'
            auto_value = 'si' if response.get('auto_scan_on_start') else 'no'
            self._set_message(f'Configuracion guardada. Ruta={path_value} | auto_scan={auto_value}')

        self._run_background_action('Guardando configuracion...', worker, on_success)

    def _on_start_scan(self) -> None:
        payload = {
            'path': self.library_path_var.get().strip(),
            'recursive': True,
            'full_rescan': bool(self.full_rescan_var.get()),
        }

        def worker() -> ApiResult:
            return _http_json('POST', f'{PYTHON_BASE}/api/music/scan', payload=payload)

        def on_success(response: dict[str, Any]) -> None:
            scan_id = response.get('scan_id', '-')
            self._set_message(f'Escaneo iniciado: {scan_id}')

        self._run_background_action('Iniciando escaneo...', worker, on_success)

    def _fetch_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {}

        ok_config, _, config = _http_json('GET', f'{PYTHON_BASE}/api/music/config', timeout=2.5)
        if not ok_config:
            snapshot['error'] = f"No se pudo leer configuracion: {_extract_error(config)}"
            return snapshot

        snapshot['config'] = config

        ok_system, _, system = _http_json('GET', f'{PYTHON_BASE}/api/system/status', timeout=2.5)
        if not ok_system:
            snapshot['error'] = f"No se pudo leer estado del sistema: {_extract_error(system)}"
            return snapshot

        snapshot['system'] = system

        configured_path = str(config.get('library_path', '')).strip()
        active_library_path = configured_path

        latest_scan = system.get('latest_scan')
        if isinstance(latest_scan, dict):
            scan_root_path = str(latest_scan.get('root_path', '')).strip()
            if scan_root_path:
                active_library_path = scan_root_path

        snapshot['active_library_path'] = active_library_path

        query_data = {'offset': 0, 'limit': 1}
        if active_library_path:
            query_data['root_path'] = active_library_path

        query = urllib.parse.urlencode(query_data)
        ok_catalog, _, catalog = _http_json('GET', f'{PYTHON_BASE}/api/music/catalog?{query}', timeout=2.5)
        if ok_catalog:
            pagination = catalog.get('pagination', {})
            total = pagination.get('total', 0)
            if isinstance(total, (int, float)):
                snapshot['catalog_total'] = int(total)
            else:
                snapshot['catalog_total'] = 0
        else:
            snapshot['catalog_total'] = 0

        return snapshot

    def _refresh_async(self, message: str | None = None) -> None:
        if self._closing or self._refresh_in_progress:
            return

        if message:
            self._set_message(message)

        self._refresh_in_progress = True

        def job() -> None:
            snapshot = self._fetch_snapshot()

            def after() -> None:
                self._refresh_in_progress = False
                if self._closing:
                    return
                self._apply_snapshot(snapshot)

            self._safe_after(0, after)

        threading.Thread(target=job, daemon=True).start()

    def _apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        error = snapshot.get('error')
        if isinstance(error, str) and error.strip():
            self._set_message(error, is_error=True)
            return

        config = snapshot.get('config', {})
        if isinstance(config, dict):
            focused_widget = self.root.focus_get()
            if focused_widget is not self.library_entry:
                self.library_path_var.set(str(config.get('library_path', '')))
            self.auto_scan_var.set(bool(config.get('auto_scan_on_start', True)))

        system = snapshot.get('system', {})
        if isinstance(system, dict):
            python_info = system.get('python', {})
            node_info = system.get('node', {})
            frontend_info = system.get('frontend', {})

            python_online = bool(isinstance(python_info, dict) and python_info.get('online'))
            python_scans = python_info.get('active_scans', 0) if isinstance(python_info, dict) else 0
            python_uptime = python_info.get('uptime_seconds', 0) if isinstance(python_info, dict) else 0
            self.python_status_var.set(
                f"{'online' if python_online else 'offline'} | scans={python_scans} | uptime={python_uptime}s"
            )

            node_online = bool(isinstance(node_info, dict) and node_info.get('online'))
            node_status_code = node_info.get('status_code', '-') if isinstance(node_info, dict) else '-'
            self.node_status_var.set(f"{'online' if node_online else 'offline'} | code={node_status_code}")

            frontend_online = bool(isinstance(frontend_info, dict) and frontend_info.get('online'))
            frontend_status_code = frontend_info.get('status_code', '-') if isinstance(frontend_info, dict) else '-'
            self.frontend_status_var.set(
                f"{'online' if frontend_online else 'offline'} | code={frontend_status_code}"
            )

            latest_scan = system.get('latest_scan')
            if isinstance(latest_scan, dict):
                self.scan_id_var.set(str(latest_scan.get('scan_id', '-')))
                self.scan_status_var.set(str(latest_scan.get('status', 'unknown')))
                processed = latest_scan.get('processed_files', 0)
                new_files = latest_scan.get('new_files', 0)
                modified_files = latest_scan.get('modified_files', 0)
                deleted_files = latest_scan.get('deleted_files', 0)
                self.scan_stats_var.set(
                    f'procesados={processed} | new={new_files} | mod={modified_files} | del={deleted_files}'
                )
            else:
                self.scan_id_var.set('-')
                self.scan_status_var.set('not_started')
                self.scan_stats_var.set('procesados=0 | new=0 | mod=0 | del=0')

        total = snapshot.get('catalog_total', 0)
        self.catalog_total_var.set(str(total))

        active_library_path = str(snapshot.get('active_library_path', '')).strip()
        self.detected_library_path_var.set(active_library_path or '(sin ruta configurada)')

        self.logs_var.set(self.runtime.logs_text())
        self._set_message(f"Estado sincronizado ({time.strftime('%H:%M:%S')}).")

    def _on_close(self) -> None:
        if self._closing:
            return

        self._closing = True
        self._set_message('Deteniendo servicios...')
        self.runtime.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    if tk is None or ttk is None or filedialog is None or messagebox is None:
        print('Tkinter no esta disponible. Instala Tk para usar la interfaz desktop.')
        return 1

    runtime = ServiceRuntime()
    ok, detail = runtime.start()
    if not ok:
        runtime.stop()
        print(f'[ERROR] {detail}')
        print('Revisa los logs en .runtime/logs para mas detalle.')
        return 1

    app = DesktopAdminApp(runtime)
    app.run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
