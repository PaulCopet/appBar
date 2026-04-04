import type { Song } from '../../data/songs';

type SelectedTrackModalProps = {
    selectedSong: Song | null;
    onConfirm: () => void;
    onClose: () => void;
};

export default function SelectedTrackModal({ selectedSong, onConfirm, onClose }: SelectedTrackModalProps) {
    if (!selectedSong) {
        return null;
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#020702]/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-[600px] border border-[#39ff14] bg-[rgba(0,30,0,0.9)] p-6 shadow-[0_0_30px_rgba(57,255,20,0.2)] animate-fade-in-echo relative">
                <button
                    onClick={onClose}
                    className="absolute top-2 right-3 text-[#39ff14] hover:text-white focus:outline-none font-bold text-xl"
                >
                    [X]
                </button>

                <p className="text-[12px] text-[#1a7a00] mb-2">$ SELECTED_TRACK --confirm-selection</p>
                <div className="mb-6 font-terminal-display text-[24px] text-[#80ff60] [text-shadow:0_0_15px_#39ff14] text-center border-y border-[#1a7a00] py-4">
                    {`> "${selectedSong.title}"`}
                    <br />
                    <span className="text-[18px] text-[#39ff14]">
                        {selectedSong.artist} ({selectedSong.year})
                    </span>
                </div>

                <div className="flex flex-col items-center gap-[15px]">
                    <div className="flex gap-4 w-full justify-center">
                        <button
                            type="button"
                            onClick={onClose}
                            className="border border-[#1a7a00] bg-transparent px-6 py-2 text-[14px] tracking-[1px] text-[#1a7a00] transition hover:bg-[#1a7a00] hover:text-[#030d02] focus:outline-none flex-1 max-w-[200px]"
                        >
                            CANCELAR
                        </button>
                        <button
                            type="button"
                            onClick={onConfirm}
                            className="border border-[#39ff14] bg-transparent px-6 py-2 text-[14px] font-bold tracking-[2px] text-[#80ff60] [text-shadow:0_0_8px_#39ff14] transition hover:bg-[#39ff14] hover:text-[#030d02] hover:[text-shadow:none] focus:outline-none flex-1 max-w-[200px]"
                        >
                            ▶ ACEPTAR
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
