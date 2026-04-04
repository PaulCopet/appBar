import { useMemo, useState } from 'react';
import { songsCatalog } from '../data/songs';
import type { Song } from '../data/songs';
import type { IndexedSong } from '../types/terminal';

type UseRockTerminalParams = {
    whatsAppNumber: string;
    whatsAppLabel: string;
};

const buildWhatsAppUrl = (number: string, song: Song): string => {
    const message = [
        'ROCK TERMINAL SELECTION',
        '',
        `SONG: ${song.title}`,
        `ARTIST: ${song.artist}`,
        `YEAR: ${song.year}`,
        '',
        'Escucha esta cancion!',
    ].join('\n');

    return `https://wa.me/${number}?text=${encodeURIComponent(message)}`;
};

export const useRockTerminal = ({
    whatsAppNumber,
    whatsAppLabel,
}: UseRockTerminalParams) => {
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

    const selectSong = (index: number) => {
        setSelectedIndex(index);
        showEcho('"OK TU CANCION HA SIDO AGREGADA"');
    };

    const sendSelectedSongToWhatsApp = () => {
        if (!selectedSong) {
            return;
        }

        const url = buildWhatsAppUrl(whatsAppNumber, selectedSong);
        window.open(url, '_blank', 'noopener,noreferrer');
        showEcho(`"OK MENSAJE ENVIADO A WHATSAPP ${whatsAppLabel}"`);
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
        sendSelectedSongToWhatsApp,
    };
};
