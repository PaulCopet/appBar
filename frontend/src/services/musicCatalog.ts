import type { Song } from '../types/terminal';

type CatalogApiSong = {
    title?: unknown;
    artist?: unknown;
    year?: unknown;
    filename?: unknown;
    path?: unknown;
};

type CatalogApiResponse = {
    pagination?: {
        total?: unknown;
        has_more?: unknown;
    };
    songs?: CatalogApiSong[];
};

type FetchMusicCatalogParams = {
    query: string;
    offset?: number;
    limit?: number;
    rootPath?: string;
    signal?: AbortSignal;
};

type FetchMusicCatalogResult = {
    songs: Song[];
    total: number;
    hasMore: boolean;
};

type MusicConfigResponse = {
    library_path?: unknown;
};

type LatestScanResponse = {
    status?: unknown;
    root_path?: unknown;
};

const API_BASE = (() => {
    const configured = import.meta.env.VITE_NODE_API_URL;
    if (typeof configured !== 'string') {
        return '';
    }

    const normalized = configured.trim();
    return normalized.replace(/\/+$/, '');
})();

const toSafeText = (value: unknown, fallback: string) => {
    if (typeof value !== 'string') {
        return fallback;
    }

    const normalized = value.trim();
    return normalized || fallback;
};

const toSafeYear = (value: unknown): number | null => {
    if (typeof value === 'number' && Number.isFinite(value)) {
        return Math.trunc(value);
    }

    if (typeof value === 'string') {
        const parsed = Number.parseInt(value, 10);
        if (Number.isFinite(parsed)) {
            return parsed;
        }
    }

    return null;
};

const normalizeSong = (item: CatalogApiSong): Song => {
    const fallbackTitle = toSafeText(item.filename, 'Sin titulo');
    const path = toSafeText(item.path, '');

    return {
        title: toSafeText(item.title, fallbackTitle),
        artist: toSafeText(item.artist, 'Unknown Artist'),
        year: toSafeYear(item.year),
        path,
    };
};

const buildCatalogUrl = ({ query, offset = 0, limit = 500, rootPath }: FetchMusicCatalogParams) => {
    const pathname = API_BASE ? `${API_BASE}/api/music/catalog` : '/api/music/catalog';
    const url = new URL(pathname, window.location.origin);

    url.searchParams.set('q', query);
    url.searchParams.set('offset', String(Math.max(0, offset)));
    url.searchParams.set('limit', String(Math.max(1, limit)));
    url.searchParams.set('sort', 'title');
    url.searchParams.set('dedupe', 'true');

    const normalizedRootPath = typeof rootPath === 'string' ? rootPath.trim() : '';
    if (normalizedRootPath) {
        url.searchParams.set('root_path', normalizedRootPath);
    }

    return url;
};

const parseTotal = (response: CatalogApiResponse, fallback: number) => {
    const total = response.pagination?.total;
    if (typeof total === 'number' && Number.isFinite(total)) {
        return Math.trunc(total);
    }

    return fallback;
};

const parseHasMore = (response: CatalogApiResponse) => {
    return Boolean(response.pagination?.has_more);
};

const buildApiUrl = (path: string) => {
    const pathname = API_BASE ? `${API_BASE}${path}` : path;
    return new URL(pathname, window.location.origin);
};

const fetchApiJson = async <T>(path: string, signal?: AbortSignal): Promise<T> => {
    const response = await fetch(buildApiUrl(path), {
        method: 'GET',
        headers: {
            Accept: 'application/json',
        },
        signal,
    });

    if (!response.ok) {
        throw new Error(`Request failed (${response.status})`);
    }

    return (await response.json()) as T;
};

export const fetchDetectedLibraryPath = async (signal?: AbortSignal): Promise<string> => {
    const [config, latestScan] = await Promise.all([
        fetchApiJson<MusicConfigResponse>('/api/music/config', signal),
        fetchApiJson<LatestScanResponse>('/api/music/scan/latest', signal),
    ]);

    const configuredPath = toSafeText(config.library_path, '');
    const latestScanStatus = toSafeText(latestScan.status, '');
    const latestScanRoot = toSafeText(latestScan.root_path, '');

    if (latestScanStatus && latestScanStatus !== 'not_started' && latestScanRoot) {
        return latestScanRoot;
    }

    return configuredPath || '(sin ruta configurada)';
};

export const fetchMusicCatalog = async (
    params: FetchMusicCatalogParams,
): Promise<FetchMusicCatalogResult> => {
    const url = buildCatalogUrl(params);
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            Accept: 'application/json',
        },
        signal: params.signal,
    });

    if (!response.ok) {
        let detail = `No se pudo cargar catalogo (${response.status})`;
        try {
            const errorPayload = (await response.json()) as { detail?: unknown };
            if (typeof errorPayload.detail === 'string' && errorPayload.detail.trim()) {
                detail = errorPayload.detail;
            }
        } catch {
            // Ignora payloads invalidos y usa el mensaje por defecto.
        }

        throw new Error(detail);
    }

    const payload = (await response.json()) as CatalogApiResponse;
    const songs = Array.isArray(payload.songs)
        ? payload.songs.map((item) => normalizeSong(item))
        : [];

    const hasMore = parseHasMore(payload);
    const total = parseTotal(payload, songs.length);

    return {
        songs,
        total,
        hasMore,
    };
};

export const triggerVirtualDJPlay = async (path: string, signal?: AbortSignal): Promise<void> => {
    if (!path) return;

    const url = buildApiUrl('/api/music/play');
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
        },
        body: JSON.stringify({ file_path: path }),
        signal,
    });

    if (!response.ok) {
        throw new Error('Error enviando cancion a VirtualDJ');
    }
};
