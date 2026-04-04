import songsSeed from './songs.json';

export type Song = {
    title: string;
    artist: string;
    year: number;
};

const TARGET_SONGS = 500;
const seedSongs = songsSeed as Song[];

const buildCatalog = (): Song[] => {
    const catalog = [...seedSongs];
    let cursor = 0;

    while (catalog.length < TARGET_SONGS) {
        const seed = seedSongs[cursor % seedSongs.length];
        const archiveId = String(catalog.length + 1).padStart(3, '0');

        catalog.push({
            title: `${seed.title} [Archive ${archiveId}]`,
            artist: seed.artist,
            year: seed.year,
        });

        cursor += 1;
    }

    return catalog;
};

export const songsCatalog: Song[] = buildCatalog();
