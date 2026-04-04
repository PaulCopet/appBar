import { useEffect, useState } from 'react';

type TypewriterTextProps = {
  text: string;
  delay?: number;
  speed?: number;
  className?: string;
  cursorClassName?: string;
};

export const TypewriterText = ({
  text,
  delay = 500,
  speed = 50,
  className = "",
  cursorClassName = "",
}: TypewriterTextProps) => {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    let typeInterval: ReturnType<typeof setTimeout>;

    setDisplayedText("");

    const timeout = setTimeout(() => {
      let currentIndex = 0;

      typeInterval = setInterval(() => {
        if (currentIndex < text.length) {
          setDisplayedText(text.slice(0, currentIndex + 1));
          currentIndex++;
        } else {
          clearInterval(typeInterval);
        }
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timeout);
      clearInterval(typeInterval);
    };
  }, [text, delay, speed]);

  return (
    <span className={className}>
      {displayedText} <span className={`animate-blink font-bold ${cursorClassName}`}>_</span>
    </span>
  );
};
