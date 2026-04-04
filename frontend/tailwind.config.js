/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        terminal: {
          bg: '#030d02',
          green: '#39ff14',
          bright: '#80ff60',
          dim: '#1a7a00',
        },
      },
      fontFamily: {
        terminal: ['Share Tech Mono', 'monospace'],
        'terminal-display': ['VT323', 'monospace'],
      },
      keyframes: {
        flicker: {
          '0%, 96%, 100%': { opacity: '1' },
          '97%': { opacity: '0.82' },
          '98%': { opacity: '1' },
          '99%': { opacity: '0.62' },
        },
        blink: {
          '50%': { opacity: '0' },
        },
        'glow-pulse': {
          '0%, 100%': { filter: 'brightness(1)', textShadow: '0 0 5px #39ff14', boxShadow: '0 0 0px rgba(57,255,20,0)' },
          '50%': { filter: 'brightness(1.2)', textShadow: '0 0 20px #80ff60, 0 0 35px #39ff14', boxShadow: '0 0 30px 10px rgba(57,255,20,0.8), inset 0 0 20px 5px rgba(57,255,20,0.6)' },
        },
        'fade-in-echo': {
          from: { opacity: '0', transform: 'translateY(-4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        flicker: 'flicker 4s infinite',
        blink: 'blink 1s step-end infinite',
        'fade-in-echo': 'fade-in-echo 0.3s ease',
        'glow-pulse': 'glow-pulse 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
