import { useEffect, useState } from 'react';
import { EncryptedText } from './EncryptedText';
import { TypewriterText } from './TypewriterText';

type EchoMessageProps = {
    message: string;
    echoKey: number;
};

export default function EchoMessage({ message, echoKey }: EchoMessageProps) {
    const [hiddenKeys, setHiddenKeys] = useState<Set<number>>(new Set());

    useEffect(() => {
        if (echoKey > 0) {
            const timer = setTimeout(() => {
                setHiddenKeys((prev) => new Set(prev).add(echoKey));
            }, 6000); // 6 segundos de visibilidad total
            return () => clearTimeout(timer);
        }
    }, [echoKey]);

    const isVisible = echoKey > 0 && !hiddenKeys.has(echoKey);

    if (!message || !isVisible) {
        return null;
    }

    return (
        <div
            key={echoKey}
            className="animate-fade-in-echo mt-[10px] border border-[#39ff14] bg-[rgba(57,255,20,0.07)] px-[14px] py-[10px] font-terminal-display text-[22px] tracking-[1px] text-[#80ff60] [text-shadow:0_0_12px_#39ff14] max-[560px]:text-[18px]"
        >
            <span className="text-[16px] text-[#1a7a00]">
                <EncryptedText text="[root@rock ~]# echo " revealDelayMs={80} />
            </span>
            <TypewriterText text={message} delay={1600} speed={40} cursorClassName="text-[#39ff14]" />
        </div>
    );
}
