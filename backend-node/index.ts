import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configurar CORS para permitir comunicación con el frontend de React Vite
app.use(cors({
  origin: 'http://localhost:5173',
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

app.listen(PORT, () => {
  console.log(`[server]: Node.js API Server is running at http://localhost:${PORT}`);
});
