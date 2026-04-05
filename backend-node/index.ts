import express, { type Request, type Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || 'http://localhost:5173,http://localhost:3000')
  .split(',')
  .map((origin) => origin.trim())
  .filter(Boolean);

// Configurar CORS para permitir comunicación con el frontend de React Vite
app.use(cors({
  origin: ALLOWED_ORIGINS,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));

app.use(express.json());

// Main entry route
app.get('/', (req: Request, res: Response) => {
  res.json({ message: 'Welcome to the Node.js API Backend' });
});

// API status route (matching the frontend mock)
app.get('/api/status', (req: Request, res: Response) => {
  res.json({
    service: "Node.js Core Backend",
    status: "online",
    uptime: `${Math.floor(process.uptime() / 60)}m ${Math.floor(process.uptime() % 60)}s`
  });
});

const appendQueryString = (url: URL, query: Request['query']) => {
  Object.entries(query).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined) {
          url.searchParams.append(key, String(item));
        }
      });
      return;
    }

    if (value !== undefined) {
      url.searchParams.append(key, String(value));
    }
  });
};

const proxyToPython = async (
  req: Request,
  res: Response,
  targetPath: string,
  method: 'GET' | 'POST' | 'PUT' = 'GET'
) => {
  const normalizedBase = PYTHON_SERVICE_URL.endsWith('/')
    ? PYTHON_SERVICE_URL
    : `${PYTHON_SERVICE_URL}/`;
  const url = new URL(targetPath.replace(/^\//, ''), normalizedBase);
  appendQueryString(url, req.query);

  const requestInit: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  if (method !== 'GET') {
    requestInit.body = JSON.stringify(req.body ?? {});
  }

  let pythonResponse: globalThis.Response;
  try {
    pythonResponse = await fetch(url, requestInit);
  } catch (error) {
    res.status(502).json({
      error: 'No se pudo contactar al microservicio Python',
      details: error instanceof Error ? error.message : 'Unknown proxy error'
    });
    return;
  }

  const payload = await pythonResponse.text();
  const contentType = pythonResponse.headers.get('content-type') || '';

  if (contentType.includes('application/json')) {
    try {
      res.status(pythonResponse.status).json(JSON.parse(payload));
      return;
    } catch {
      // Si la respuesta no era JSON valido se devuelve texto plano.
    }
  }

  res.status(pythonResponse.status).send(payload);
};

app.post('/api/music/scan', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/scan', 'POST');
});

app.get('/api/music/scan/:scanId', async (req: Request, res: Response) => {
  const scanId = (req.params.scanId as string) ?? '';
  const targetPath = `/api/music/scan/${encodeURIComponent(scanId)}`;
  await proxyToPython(req, res, targetPath, 'GET');
});

app.get('/api/music/scan/latest', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/scan/latest', 'GET');
});

app.get('/api/music/config', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/config', 'GET');
});

app.put('/api/music/config', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/config', 'PUT');
});

app.get('/api/music/catalog', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/catalog', 'GET');
});

app.get('/api/music/changes', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/music/changes', 'GET');
});

app.get('/api/system/status', async (req: Request, res: Response) => {
  await proxyToPython(req, res, '/api/system/status', 'GET');
});

app.listen(PORT, () => {
  console.log(`[server]: Node.js API Server is running at http://localhost:${PORT}`);
});
