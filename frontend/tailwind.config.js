/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'space-black': '#020408',
        'space-navy': '#050d1a',
        'surface': '#0a1628',
        'border-dim': '#0e2040',
        'accent-cyan': '#00d4ff',
        'accent-blue': '#0070f3',
        'accent-violet': '#7c3aed',
        'text-primary': '#e8f4ff',
        'text-secondary': '#6b8fa8',
        'text-telemetry': '#00d4ff',
        'badge-demo': '#f59e0b',
        'badge-real': '#22c55e',
        'badge-fallback': '#a855f7',
        'limitation': '#64748b',
      },
      fontFamily: {
        'space': ['"Space Grotesk"', 'sans-serif'],
        'mono': ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'spin-slow': 'spin 20s linear infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        'orbit': 'orbit 8s linear infinite',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'glow-pulse': 'glowPulse 3s ease-in-out infinite',
      },
      keyframes: {
        orbit: {
          '0%': { transform: 'translateX(-50%) rotate(0deg) translateX(180px) rotate(0deg)' },
          '100%': { transform: 'translateX(-50%) rotate(360deg) translateX(180px) rotate(-360deg)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(0, 212, 255, 0.2)' },
          '50%': { boxShadow: '0 0 24px rgba(0, 212, 255, 0.5)' },
        },
      },
      backdropBlur: {
        xs: '4px',
      },
    },
  },
  plugins: [],
}
