export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        shell: '#0A1628',
        accent: '#00C2CB',
        emergency: '#FF6B35',
        success: '#22C55E',
        ink: '#E8F4F8',
        muted: '#6C8CA1'
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(0, 194, 203, 0.16), 0 20px 60px rgba(0, 0, 0, 0.28)'
      },
      animation: {
        pulseRing: 'pulseRing 1.8s ease-out infinite'
      },
      keyframes: {
        pulseRing: {
          '0%': { transform: 'scale(0.95)', opacity: '0.9' },
          '100%': { transform: 'scale(1.5)', opacity: '0' }
        }
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['"Manrope"', 'sans-serif']
      }
    }
  },
  plugins: []
}
