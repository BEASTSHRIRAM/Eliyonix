/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'e-black':      '#000000',
        'e-near-black': '#17171c',
        'e-green':      '#003c33',
        'e-navy':       '#071829',
        'e-blue':       '#1863dc',
        'e-coral':      '#ff7759',
        'e-s-coral':    '#ffad9b',
        'e-canvas':     '#ffffff',
        'e-stone':      '#eeece7',
        'e-p-green':    '#edfce9',
        'e-p-blue':     '#f1f5ff',
        'e-ink':        '#212121',
        'e-muted':      '#93939f',
        'e-hairline':   '#d9d9dd',
      },
      fontFamily: {
        grotesk: ['Space Grotesk', 'sans-serif'],
        dm:      ['DM Sans', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
