export type IndexedSong = {
    song: Song;
    index: number;
};

export type Song = {
    title: string;
    artist: string;
    year: number | null;
    path: string;
};
