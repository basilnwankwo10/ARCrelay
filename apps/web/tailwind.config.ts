import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#070B14',
        foreground: '#F8FAFC',
        arc: {
          dark: '#070B14',
          surface: '#0B1120',
          card: '#0F172A',
          border: '#1E293B',
          cyan: '#00F0FF',
          blue: '#0052FF',
          purple: '#8B5CF6',
          green: '#10B981',
          muted: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 30px -5px rgba(0, 240, 255, 0.3)',
        'glow-blue': '0 0 30px -5px rgba(0, 82, 255, 0.3)',
        'glow-green': '0 0 30px -5px rgba(16, 185, 129, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};

export default config;
