import { useEffect, useState } from 'react';

function StatusBar() {
    const [memory, setMemory] = useState('62.4');

    useEffect(() => {
        const interval = setInterval(() => {
            // Fluctuación aleatoria realista entre 61.0 y 63.5
            const randomMem = (61 + Math.random() * 2.5).toFixed(1);
            setMemory(randomMem);
        }, 1500);

        return () => clearInterval(interval);
    }, []);

    return (
        <footer className="flex mt-2 justify-between text-[10px] text-[#1a7a00]">
            <span>ROCK_DB © 2026 | ALL RIGHTS RESERVED</span>
            <span>
                MEM: {memory}GB | CPU: i9-7960X |
            </span>
        </footer>
    );
}

export default StatusBar;
