/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#E8EDF5',
          100: '#C5D0E5',
          200: '#9FB0D0',
          300: '#7890BB',
          400: '#5A76AA',
          500: '#3C5C99',
          600: '#2E4A7A',
          700: '#1E3460',
          800: '#0F2040',
          900: '#0A1628',
          950: '#06101A',
        },
        ocean: {
          50: '#E6F3FF',
          100: '#C1E0FF',
          200: '#96CEFF',
          300: '#61B6FF',
          400: '#3AA1FF',
          500: '#0D8BFF',
          600: '#006AD4',
          700: '#0054A6',
          800: '#003E7A',
          900: '#0D4F8C',
        },
        sonar: {
          cyan: '#00B4D8',
          teal: '#0077B6',
          blue: '#0096C7',
          dark: '#03045E',
          accent: '#48CAE4',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      backgroundImage: {
        'sonar-grid': "url(\"data:image/svg+xml,%3Csvg width='40' height='40' xmlns='http://www.w3.org/2000/svg'%3E%3Cdefs%3E%3Cpattern id='grid' width='40' height='40' patternUnits='userSpaceOnUse'%3E%3Cpath d='M 40 0 L 0 0 0 40' fill='none' stroke='rgba(0,180,216,0.06)' stroke-width='1'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100%25' height='100%25' fill='url(%23grid)'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
}
