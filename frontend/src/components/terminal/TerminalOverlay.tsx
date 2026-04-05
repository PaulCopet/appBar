function TerminalOverlay() {
    return (
        <>
            <div
                aria-hidden="true"
                className="pointer-events-none fixed inset-0 z-40 opacity-80 bg-[repeating-linear-gradient(0deg,transparent,transparent_2px,rgba(0,255,0,0.03)_2px,rgba(0,255,0,0.03)_4px)]"
            />
            <div
                aria-hidden="true"
                className="pointer-events-none fixed inset-0 z-30 bg-[radial-gradient(ellipse_at_center,transparent_58%,rgba(0,0,0,0.86)_100%)]"
            />
        </>
    );
}

export default TerminalOverlay;
