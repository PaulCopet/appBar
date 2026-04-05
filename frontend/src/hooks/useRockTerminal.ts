import { useEffect, useMemo, useState } from 'react';
import { fetchDetectedLibraryPath, fetchMusicCatalog } from '../services/musicCatalog';
import type { IndexedSong, Song } from '../types/terminal';

const SEARCH_DEBOUNCE_MS = 220;
const AUTO_REFRESH_MS = 8_000;
const CATALOG_LIMIT = 500;

export const useRockTerminal = () => {
    const [query, setQuery] = useState('');
    const [songs, setSongs] = useState<Song[]>([]);
    const [totalSongs, setTotalSongs] = useState(0);
    const [hasMoreResults, setHasMoreResults] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [detectedLibraryPath, setDetectedLibraryPath] = useState('(sin ruta configurada)');
    const [refreshTick, setRefreshTick] = useState(0);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [echoMessage, setEchoMessage] = useState('');
    const [echoKey, setEchoKey] = useState(0);

    useEffect(() => {
        const intervalId = window.setInterval(() => {
            setRefreshTick((current) => current + 1);
        }, AUTO_REFRESH_MS);

        return () => {
            window.clearInterval(intervalId);
        };
    }, []);

    useEffect(() => {
        const controller = new AbortController();

        void (async () => {
            try {
                const activePath = await fetchDetectedLibraryPath(controller.signal);
                setDetectedLibraryPath(activePath || '(sin ruta configurada)');
            } catch {
                setDetectedLibraryPath('(sin ruta configurada)');
            }
        })();

        return () => {
            controller.abort();
        };
    }, [refreshTick]);

    useEffect(() => {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => {
            void (async () => {
                setIsLoading(true);
                try {
                    const catalog = await fetchMusicCatalog({
                        query,
                        offset: 0,
                        limit: CATALOG_LIMIT,
                        signal: controller.signal,
                    });

                    setSongs(catalog.songs);
                    setTotalSongs(catalog.total);
                    setHasMoreResults(catalog.hasMore);
                    setLoadError(null);
                } catch (error) {
                    if (error instanceof DOMException && error.name === 'AbortError') {
                        return;
                    }

                    setSongs([]);
                    setTotalSongs(0);
                    setHasMoreResults(false);
                    setLoadError(error instanceof Error ? error.message : 'No se pudo cargar catalogo');
                } finally {
                    setIsLoading(false);
                }
            })();
        }, SEARCH_DEBOUNCE_MS);

        return () => {
            controller.abort();
            window.clearTimeout(timeoutId);
        };
    }, [query, refreshTick]);

    useEffect(() => {
        if (selectedIndex !== null && selectedIndex >= songs.length) {
            setSelectedIndex(null);
        }
    }, [selectedIndex, songs.length]);

    const selectedSong = selectedIndex === null ? null : songs[selectedIndex] ?? null;

    const filteredSongs = useMemo<IndexedSong[]>(() => {
        return songs.map((song, index) => ({ song, index }));
    }, [songs]);

    const showEcho = (message: string) => {
        setEchoMessage(message);
        setEchoKey((current) => current + 1);
    };

    const selectSong = (index: number | null) => {
        setSelectedIndex(index);
    };

    const confirmSelection = () => {
        if (!selectedSong) {
            return;
        }

        showEcho('"CANCION CONFIRMADA EN LA TERMINAL"');
        setSelectedIndex(null);
    };

    return {
        query,
        setQuery,
        selectedIndex,
        selectedSong,
        totalSongs,
        filteredSongs,
        hasMoreResults,
        isLoading,
        loadError,
        detectedLibraryPath,
        echoMessage,
        echoKey,
        selectSong,
        confirmSelection,
    };
};
