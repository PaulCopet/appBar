# my-modern-app - Setup completo (Python + Node)

Este README deja el setup completo del proyecto con las versiones actuales detectadas y todos los comandos de instalacion.

## Quick Start (Copiar y Pegar)

Si acabas de clonar el proyecto, simplemente copia todo este bloque, pégalo en tu terminal (en la raíz del proyecto) y presiona Enter:

```bash
# INSTALAR BACKEND NODE
cd backend-node
npm install
cd ..

# INSTALAR FRONTEND
cd frontend
npm install
cd ..

# INSTALAR PYTHON BACKEND & VENV
cd backend-python
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install python-osc
cd ..

# LISTO, AHORA PUEDES INICIAR TODO EL PROYECTO CON:
# py start_all.py
```

## Versiones usadas (actuales en esta maquina)
- Python: `3.12.6`
- pip: `26.0.1`
- Node.js: `v24.13.0`
- npm: `11.8.0`

## Estructura del proyecto

- `backend-python/` -> API FastAPI + indexador de musica
- `backend-node/` -> API Node/Express (proxy hacia Python)
- `frontend/` -> React + Vite + Tailwind
- `start_all.py` -> levanta todo (Python + Node + Frontend)

## 1) Instalacion de Python (Windows)

### Crear/usar entorno virtual

Si quieres crear un entorno virtual en la raiz del proyecto:

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app
py -3.12 -m venv .venv
```

Activar entorno virtual:

```bash
C:/Users/jhanc/OneDrive/Desktop/my-modern-app/.venv/Scripts/activate
```

Actualizar pip:

```bash
python -m pip install --upgrade pip
```

### Instalar librerias Python del proyecto

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-python
pip install -r requirements.txt
```

Dependencias Python usadas por el proyecto:

- `fastapi>=0.116.0,<1.0.0`
- `uvicorn[standard]>=0.34.0,<1.0.0`
- `mutagen>=1.47.0,<2.0.0`

## 2) Instalacion de Node.js y paquetes JS/TS

### Dependencias de la raiz

> Necesarias para utilidades compartidas (ej. `vite-plugin-pwa`)

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app
npm install
```

Dependencia actual en raiz:

- `vite-plugin-pwa@^1.2.0`

### Dependencias de backend-node

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-node
npm install
```

Dependencias runtime (`backend-node/package.json`):

- `express@^5.2.1`
- `cors@^2.8.6`
- `dotenv@^17.4.0`

Dependencias dev (`backend-node/package.json`):

- `typescript@^6.0.2`
- `tsx@^4.21.0`
- `@types/node@^25.5.0`
- `@types/express@^5.0.6`
- `@types/cors@^2.8.19`

### Dependencias de frontend

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/frontend
npm install
```

Dependencias runtime (`frontend/package.json`):

- `react@^19.2.4`
- `react-dom@^19.2.4`

Dependencias dev (`frontend/package.json`):

- `vite@^8.0.1`
- `typescript@~5.9.3`
- `@vitejs/plugin-react@^6.0.1`
- `@types/node@^24.12.0`
- `@types/react@^19.2.14`
- `@types/react-dom@^19.2.3`
- `eslint@^9.39.4`
- `@eslint/js@^9.39.4`
- `typescript-eslint@^8.57.0`
- `eslint-plugin-react-hooks@^7.0.1`
- `eslint-plugin-react-refresh@^0.5.2`
- `globals@^17.4.0`
- `tailwindcss@^3.4.19`
- `postcss@^8.5.8`
- `autoprefixer@^10.4.27`

## 3) Verificacion rapida

### Python

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-python
python -m py_compile main.py music_index.py
```

### Node backend

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-node
npx tsc --noEmit
```

### Frontend

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/frontend
npm run lint
npm run build
```

## 4) Ejecutar el proyecto

## Opcion A: levantar todo junto

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app
python start_all.py
```

Por defecto, `start_all.py` detecta una IP privada LAN y publica el frontend para otros dispositivos en la misma red.
Si quieres una URL fija (siempre la misma), define la IP manualmente antes de ejecutar:

```bash
set APP_LAN_HOST=192.168.1.50
python start_all.py
```

> Recomendado: asigna esa IP como fija/reservada en tu router para que no cambie.

## Opcion B: levantar por separado (3 terminales)

### Terminal 1 - Python API

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-python
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Terminal 2 - Node API

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-node
npx tsx index.ts
```

### Terminal 3 - Frontend

```bash
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/frontend
npm run dev
```

## 5) URLs esperadas

- Frontend (LAN): `http://<APP_LAN_HOST o IP detectada>:5173`
- Node API (solo local del host): `http://127.0.0.1:3000`
- Python API (solo local del host): `http://127.0.0.1:8000`

## Notas

- Si usas `.venv`, recuerda activarlo antes de ejecutar comandos Python.
- Si cambias de version de Node o Python, borra `node_modules` y reinstala.
- Para reproducir entorno limpio, sigue esta guia en orden (raiz -> backend-node -> frontend -> backend-python).

## 6) Integración VirtualDJ OSC (Rockola Mode)

Para que el frontend pueda enviar las ordenes "Cargar y Reproducir" directo a tu instancia Local de VirtualDJ, ya hemos completado la integración del API OSC nativo.

SOLO COPIA Y PEGA estos comandos (con tu VirtualDJ cerrado) si clonas o reinstalas el proyecto por primera vez:

```bash
# 1. Habilitar OSC Port 8001 en VirtualDJ (Por linea de comandos PowerShell, o configuralo manual en VDJ -> Settings -> oscPort: 8001)
# 2. Instalar el cliente python-osc en el entorno de nuestro backend
cd C:/Users/jhanc/OneDrive/Desktop/my-modern-app/backend-python
../.venv/Scripts/pip install python-osc   # si usas el venv local
# o si usas el python global: pip install python-osc
```
