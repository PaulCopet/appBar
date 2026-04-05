type TerminalHeaderProps = {
    totalSongs: number;
};

const BORDER_LINE = '################################################################################';

function TerminalHeader({ totalSongs }: TerminalHeaderProps) {
    return (
        <header className="mb-2 border border-[#1a7a00] bg-[rgba(0,30,0,0.4)] p-2">
            <p className="mb-1 overflow-hidden whitespace-nowrap text-[11px] text-[#1a7a00]">{BORDER_LINE}</p>
            <div className="flex justify-between items-center mr-5">
                <h1 className="animate-flicker font-terminal-display text-[1.2rem] tracking-[0.13em] text-[#80ff60] [text-shadow:0_0_20px_#39ff14,0_0_40px_#1a7a00]">
                    # ROCK_DATABASE ▶
                </h1>
                <p className="text-[10px]">
                    # STATUS: <span className="animate-pulse font-bold tracking-[2px] text-[#39ff14] [text-shadow:0_0_8px_#39ff14]">ONLINE</span>
                </p>
            </div>
            <p className="text-[12px] leading-relaxed text-[#1a7a00]">
                # HOST: rock-terminal.local # ARCH: x86_64 # SONGS: <span className="text-[#39ff14]">{totalSongs}</span>
                <br />
                # SYSTEM:{' '}
                <span className="text-[#39ff14]">ACTIVE</span> <span className="animate-blink">_</span>
            </p>
            <p className="mt-1 overflow-hidden whitespace-nowrap text-[11px] text-[#1a7a00]">{BORDER_LINE}</p>
        </header>
    );
}

export default TerminalHeader;
