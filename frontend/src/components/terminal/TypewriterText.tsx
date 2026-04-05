import { useEffect, useState } from 'react';

type TypewriterTextProps = {
  text: string;
  delay?: number;
  speed?: number;
  className?: string;
  cursorClassName?: string;
  hideCursorOnComplete?: boolean;
};

export const TypewriterText = ({
  text,
  delay = 500,
  speed = 50,
  className = "",
  cursorClassName = "",
  hideCursorOnComplete = false,
}: TypewriterTextProps) => {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    let typeInterval: ReturnType<typeof setTimeout>;

    setDisplayedText("");
    setIsComplete(false);

    const timeout = setTimeout(() => {
      let currentIndex = 0;

      typeInterval = setInterval(() => {
        if (currentIndex < text.length) {
          setDisplayedText(text.slice(0, currentIndex + 1));
          currentIndex++;
        } else {
          setIsComplete(true);
          clearInterval(typeInterval);
        }
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timeout);
      clearInterval(typeInterval);
    };
  }, [text, delay, speed]);

  const showCursor = !hideCursorOnComplete || !isComplete;

  return (
    <span className={className}>
      {displayedText} {showCursor && <span className={`animate-blink font-bold ${cursorClassName}`}>_</span>}
    </span>
  );
};
