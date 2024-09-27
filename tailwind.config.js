/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html', './static/**/*.js', './**/*.py'],
  theme: {
    extend: {
      colors: {
        'lime-yellow': '#CCCC33',
        'olive-green': '#669933',
        'sea-green': '#339966',
        'forest-green': '#006633',
      },
    },
  },
  plugins: [require("daisyui")],
}


