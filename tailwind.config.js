/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.html",
    "./src/static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'timetracker-primary': '#E85D8A',
        'timetracker-secondary': '#4A4A4A',
      }
    },
  },
  plugins: [],
}
