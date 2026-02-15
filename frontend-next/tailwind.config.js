/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'monad-deep': '#0f0a2e',
        'monad-cream': '#faf3e0',
        'monad-teal': '#3dd9c4',
        'monad-burgundy': '#4a1528',
        'monad-gold': '#d4af37',
        'monad-coral': '#e8736a',
      },
      fontFamily: {
        'serif': ['Playfair Display', 'serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
