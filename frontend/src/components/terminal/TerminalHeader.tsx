type TerminalHeaderProps = {
    totalSongs: number;
};

const BORDER_LINE = '################################################################################';

function TerminalHeader({ totalSongs }: TerminalHeaderProps) {
    return (
        <header className="mb-2 border border-[#1a7a00] bg-[rgba(0,30,0,0.4)] p-2">
            <p className="mb-2 overflow-hidden whitespace-nowrap text-[11px] text-[#1a7a00]">{BORDER_LINE}</p>
            <h1 className="animate-flicker font-terminal-display text-[1.2rem] tracking-[0.13em] text-[#80ff60] [text-shadow:0_0_20px_#39ff14,0_0_40px_#1a7a00]">
                # ROCK_DATABASE ▶
            </h1>
            <p className="text-[12px] leading-relaxed text-[#1a7a00]">
                # HOST: rock-terminal.local # ARCH: x86_64 # SONGS: <span className="text-[#39ff14]">{totalSongs}</span>
                <br />
                # STATUS: <span className="text-[#39ff14]">ONLINE</span> # WHATSAPP:{' '}
                <span className="text-[#39ff14]">ENABLED</span> <span className="animate-blink">_</span>
            </p>
            <p className="mt-2 overflow-hidden whitespace-nowrap text-[11px] text-[#1a7a00]">{BORDER_LINE}</p>
        </header>
    );
}

export default TerminalHeader;
