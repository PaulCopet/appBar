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
        'fade-in-echo': {
          from: { opacity: '0', transform: 'translateY(-4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        flicker: 'flicker 4s infinite',
        blink: 'blink 1s step-end infinite',
        'fade-in-echo': 'fade-in-echo 0.3s ease',
      },
    },
  },
  plugins: [],
};
