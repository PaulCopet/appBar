function StatusBar() {
    return (
        <footer className="mt-4 flex justify-between gap-2 border-t border-[#1a7a00] pt-2 text-[11px] text-[#1a7a00] max-[760px]:flex-col">
            <span>ROCK_DB © 2026 | ALL RIGHTS RESERVED</span>
            <span>
                MEM: 62.4GB | CPU: i9-7960X | <span className="animate-blink">▮</span>
            </span>
        </footer>
    );
}

export default StatusBar;
