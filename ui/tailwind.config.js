/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tech-dark': '#0a0b14', // Base background, almost black
        'tech-slate': '#1f2937', // Secondary bg
        'tech-cyan': '#00f2ea', // Primary accent
        'tech-magenta': '#ff0055', // Secondary accent
        'tech-grid': '#1f2937', // Grid lines
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
