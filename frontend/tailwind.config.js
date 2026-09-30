/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          850: '#151f32',
          950: '#0a0f1d',
        },
        hazard: {
          flood: '#38bdf8',
          blocked: '#ef4444',
          affected: '#f59e0b',
          open: '#10b981',
          critical: '#dc2626',
          isolated: '#f97316'
        }
      }
    },
  },
  plugins: [],
}
