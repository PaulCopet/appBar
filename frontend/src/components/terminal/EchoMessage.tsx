type EchoMessageProps = {
    message: string;
    echoKey: number;
};

function EchoMessage({ message, echoKey }: EchoMessageProps) {
    if (!message) {
        return null;
    }

    return (
        <div
            key={echoKey}
            className="animate-fade-in-echo mt-[10px] border border-[#39ff14] bg-[rgba(57,255,20,0.07)] px-[14px] py-[10px] font-terminal-display text-[22px] tracking-[1px] text-[#80ff60] [text-shadow:0_0_12px_#39ff14] max-[560px]:text-[18px]"
        >
            <span className="text-[16px] text-[#1a7a00]">[root@rock ~]# echo </span>
            {message} <span className="animate-blink">_</span>
        </div>
    );
}

export default EchoMessage;
