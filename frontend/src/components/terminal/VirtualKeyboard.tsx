import React, { useEffect, useRef } from 'react';

type VirtualKeyboardProps = {
    isVisible: boolean;
    query: string;
    onQueryChange: (query: string) => void;
    onClose: () => void;
};

const KEYBOARD_LAYOUT = [
    ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-'],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', '/', '|']
];

function VirtualKeyboard({ isVisible, query, onQueryChange, onClose }: VirtualKeyboardProps) {
    const keyboardRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isVisible) return;

        const handleClickOutside = (e: MouseEvent | TouchEvent) => {
            const target = e.target as HTMLElement | null;
            if (
                target &&
                keyboardRef.current &&
                !keyboardRef.current.contains(target) &&
                target.id !== 'searchInput'
            ) {
                onClose();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('touchstart', handleClickOutside);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('touchstart', handleClickOutside);
        };
    }, [isVisible, onClose]);

    if (!isVisible) return null;

    const handleKeyPress = (e: React.MouseEvent | React.TouchEvent, key: string) => {
        // Prevent default to prevent search input from losing focus
        e.preventDefault();
        
        if (key === 'BACKSPACE') {
            onQueryChange(query.slice(0, -1));
        } else if (key === 'SPACE') {
            onQueryChange(query + ' ');
        } else if (key === 'CLEAR') {
            onQueryChange('');
        } else {
            onQueryChange(query + key);
        }
    };

    const handleClose = (e: React.MouseEvent | React.TouchEvent) => {
        e.preventDefault();
        onClose();
    };

    return (
        <div ref={keyboardRef} className="fixed bottom-0 left-0 right-0 z-50 animate-[slideUp_0.3s_ease-out] border-t-2 border-[#1a7a00] bg-[#030d02] p-2 pb-6 pt-3 shadow-[0_-5px_20px_rgba(57,255,20,0.15)] sm:pb-4">
            <div className="mx-auto flex max-w-[600px] flex-col gap-2">
                {/* Header/Controls */}
                <div className="flex items-center justify-between px-1 mb-1">
                    <span className="text-[10px] text-[#1a7a00] tracking-widest">[ VIRTUAL_KEYBOARD_MODE ]</span>
                    <button 
                        onMouseDown={handleClose} 
                        onTouchStart={handleClose}
                        className="text-[10px] border border-[#1a7a00] px-2 py-0.5 text-[#39ff14] hover:bg-[#1a7a00]/30 active:bg-[#39ff14]/50 transition-colors"
                    >
                        CERRAR_X
                    </button>
                </div>

                {/* Keys */}
                {KEYBOARD_LAYOUT.map((row, rowIndex) => (
                    <div key={rowIndex} className="flex justify-center gap-1 sm:gap-2">
                        {row.map((key) => (
                            <button
                                key={key}
                                onMouseDown={(e) => handleKeyPress(e, key)}
                                onTouchStart={(e) => handleKeyPress(e, key)}
                                className="flex h-10 w-8 sm:w-10 items-center justify-center border border-[#1a7a00] bg-transparent text-[16px] font-bold text-[#39ff14] transition-all hover:bg-[#1a7a00]/40 hover:shadow-[0_0_8px_#39ff14] active:scale-95 active:bg-[#39ff14] active:text-black"
                            >
                                {key.toUpperCase()}
                            </button>
                        ))}
                    </div>
                ))}
                
                {/* Bottom Row: Clear, Space, Backspace */}
                <div className="flex justify-center gap-2 mt-1 px-1">
                    <button
                        onMouseDown={(e) => handleKeyPress(e, 'CLEAR')}
                        onTouchStart={(e) => handleKeyPress(e, 'CLEAR')}
                        className="flex h-10 px-4 items-center justify-center border border-[#1a7a00] bg-transparent text-[12px] font-bold text-[#8a1f1f] transition-all hover:bg-[#8a1f1f]/30 hover:border-[#ff6f6f] hover:text-[#ff6f6f] active:scale-95"
                    >
                        CLR
                    </button>
                    <button
                        onMouseDown={(e) => handleKeyPress(e, 'SPACE')}
                        onTouchStart={(e) => handleKeyPress(e, 'SPACE')}
                        className="flex h-10 flex-1 items-center justify-center border border-[#1a7a00] bg-transparent text-[14px] font-bold text-[#39ff14] transition-all hover:bg-[#1a7a00]/40 hover:shadow-[0_0_8px_#39ff14] active:scale-95 active:bg-[#39ff14] active:text-black min-w-[120px] max-w-[300px]"
                    >
                        [     ESPACIO     ]
                    </button>
                    <button
                        onMouseDown={(e) => handleKeyPress(e, 'BACKSPACE')}
                        onTouchStart={(e) => handleKeyPress(e, 'BACKSPACE')}
                        className="flex h-10 px-4 items-center justify-center border border-[#1a7a00] bg-transparent text-[12px] font-bold text-[#39ff14] transition-all hover:bg-[#1a7a00]/40 hover:shadow-[0_0_8px_#39ff14] active:scale-95 active:bg-[#39ff14] active:text-black"
                    >
                        &lt; DEL
                    </button>
                </div>
            </div>
            {/* Inline animation keyframes for easy shipping */}
            <style>{`
                @keyframes slideUp {
                    from { transform: translateY(100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
            `}</style>
        </div>
    );
}

export default VirtualKeyboard;
