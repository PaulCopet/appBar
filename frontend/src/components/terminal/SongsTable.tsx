import type { IndexedSong } from '../../types/terminal';

type SongsTableProps = {
    songs: IndexedSong[];
    selectedIndex: number | null;
    onSelectSong: (index: number) => void;
};

function SongsTable({ songs, selectedIndex, onSelectSong }: SongsTableProps) {
    return (
        <div className="flex min-h-0 flex-1 flex-col">
            <div className="flex gap-3 border border-b-0 border-[#1a7a00] bg-[rgba(0,20,0,0.86)] px-3 py-1 text-[11px] text-[#1a7a00]">
                <span className="min-w-[42px]">#NUM</span>
                <span className="flex-1">TITLE</span>
                <span className="min-w-[190px] max-[760px]:min-w-[130px] max-[560px]:hidden">ARTIST</span>
                <span className="min-w-[56px] max-[760px]:hidden">YEAR</span>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto border border-[#1a7a00] bg-[rgba(0,15,0,0.54)]">
                {songs.length === 0 ? (
                    <div className="p-5 text-center text-[13px] text-[#1a7a00]">
                        &gt; ERROR: NO RECORDS FOUND. TRY ANOTHER QUERY. _
                    </div>
                ) : (
                    songs.map(({ song, index }) => {
                        const isSelected = selectedIndex === index;
                        const yearLabel = song.year ?? '----';

                        return (
                            <button
                                key={`${song.title}-${song.artist}-${index}`}
                                type="button"
                                onClick={() => onSelectSong(index)}
                                className={`flex w-full items-center gap-3 border-b border-[rgba(0,100,0,0.2)] px-3 py-[7px] text-left text-[13px] transition-colors focus:outline-none ${isSelected
                                    ? 'bg-[rgba(57,255,20,0.15)] text-[#80ff60] [text-shadow:0_0_10px_#39ff14]'
                                    : 'hover:bg-[rgba(57,255,20,0.08)] hover:text-[#80ff60] hover:[text-shadow:0_0_8px_#39ff14]'
                                    }`}
                            >
                                <span className="min-w-[42px] text-[12px] text-[#1a7a00]">{String(index + 1).padStart(3, '0')}</span>
                                <span className="flex-1">{song.title}</span>
                                <span className="min-w-[190px] text-[12px] text-[#1a7a00] max-[760px]:min-w-[130px] max-[560px]:hidden">
                                    {song.artist}
                                </span>
                                <span className="min-w-[56px] text-[12px] text-[#1a7a00] max-[760px]:hidden">{yearLabel}</span>
                            </button>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default SongsTable;
