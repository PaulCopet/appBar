import { useMemo, useState } from 'react';
import { songsCatalog } from '../data/songs';
import type { IndexedSong } from '../types/terminal';

export const useRockTerminal = () => {
    const [query, setQuery] = useState('');
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [echoMessage, setEchoMessage] = useState('');
    const [echoKey, setEchoKey] = useState(0);

    const totalSongs = songsCatalog.length;
    const selectedSong = selectedIndex === null ? null : songsCatalog[selectedIndex];

    const filteredSongs = useMemo<IndexedSong[]>(() => {
        const normalizedQuery = query.toLowerCase().trim();

        return songsCatalog
            .map((song, index) => ({ song, index }))
            .filter(({ song }) => {
                if (!normalizedQuery) {
                    return true;
                }

                return (
                    song.title.toLowerCase().includes(normalizedQuery) ||
                    song.artist.toLowerCase().includes(normalizedQuery)
                );
            });
    }, [query]);

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
        echoMessage,
        echoKey,
        selectSong,
        confirmSelection,
    };
};
