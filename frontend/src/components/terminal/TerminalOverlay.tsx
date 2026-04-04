function TerminalOverlay() {
    return (
        <>
            <div
                aria-hidden="true"
                className="pointer-events-none fixed inset-0 z-40 opacity-80"
                style={{
                    background:
                        'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,0,0.03) 2px, rgba(0,255,0,0.03) 4px)',
                }}
            />
            <div
                aria-hidden="true"
                className="pointer-events-none fixed inset-0 z-30 bg-[radial-gradient(ellipse_at_center,transparent_58%,rgba(0,0,0,0.86)_100%)]"
            />
        </>
    );
}

export default TerminalOverlay;
