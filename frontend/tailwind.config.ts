/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        navy: {
          DEFAULT: '#000080',
          hover: '#000066',
        },
        saffron: '#FF9933',
        green: {
          DEFAULT: '#138808',
          600: '#138808',
          700: '#0f6b06',
        },
        white: '#FFFFFF',
        red: {
          DEFAULT: '#dc3545',
          600: '#dc3545',
          700: '#c82333',
        },
        'gov-bg': '#f5f7fa',
        'gov-text': '#0b1a30',
        'gov-border': '#d1d9e2',
      },
      fontFamily: {
        heading: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
        body: ['"Inter"', 'sans-serif'],
        futuristic: ['"Orbitron"', 'sans-serif'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0,217,255,0.3)',
        'glow-green': '0 0 20px rgba(0,255,136,0.3)',
        'glow-red': '0 0 25px rgba(255, 51, 85, 0.4)',
        'glow-purple': '0 0 20px rgba(170, 85, 255, 0.3)',
        'glow-amber': '0 0 20px rgba(255, 204, 0, 0.3)',
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'energy-flow': 'energyFlow 3s linear infinite',
        'radar-scan': 'radarScan 4s linear infinite',
        'spin-slow': 'spin 12s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'neon-glow': 'neonGlow 2s infinite',
        'neon-rotate': 'neonRotate 8s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: '0.6', filter: 'blur(2px)' },
          '50%': { opacity: '1', filter: 'blur(0px)' },
        },
        energyFlow: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        radarScan: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        neonGlow: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(0, 217, 255, 0.5), 0 0 20px rgba(0, 217, 255, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(0, 217, 255, 0.8), 0 0 40px rgba(0, 217, 255, 0.5)' },
        },
        neonRotate: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        }
      },
    },
  },
  plugins: [],
};
