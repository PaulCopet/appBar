import type { Song } from '../../data/songs';

type SelectedTrackPanelProps = {
    selectedSong: Song | null;
    whatsAppLabel: string;
    onSend: () => void;
};

function SelectedTrackPanel({ selectedSong, whatsAppLabel, onSend }: SelectedTrackPanelProps) {
    if (!selectedSong) {
        return null;
    }

    return (
        <section className="mt-[15px] border border-[#39ff14] bg-[rgba(0,30,0,0.63)] p-3 shadow-[0_0_20px_rgba(57,255,20,0.1)]">
            <p className="text-[11px] text-[#1a7a00]">$ SELECTED_TRACK --send-to-whatsapp 3157507977</p>
            <p className="my-2 font-terminal-display text-[24px] text-[#80ff60] [text-shadow:0_0_15px_#39ff14] max-[560px]:text-[20px]">
                {`> "${selectedSong.title}" - ${selectedSong.artist} (${selectedSong.year})`}
            </p>

            <div className="flex flex-wrap items-center gap-[10px] max-[560px]:flex-col max-[560px]:items-start">
                <span className="text-[12px] text-[#1a7a00]">DESTINO:</span>
                <span className="text-[13px] text-[#80ff60]">{whatsAppLabel}</span>
                <button
                    type="button"
                    onClick={onSend}
                    className="border border-[#39ff14] bg-transparent px-4 py-1 text-[13px] tracking-[1px] text-[#80ff60] [text-shadow:0_0_8px_#39ff14] transition hover:bg-[#39ff14] hover:text-[#030d02] hover:[text-shadow:none] focus:outline-none"
                >
                    ▶ ENVIAR A WHATSAPP
                </button>
            </div>
        </section>
    );
}

export default SelectedTrackPanel;
