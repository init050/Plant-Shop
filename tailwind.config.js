/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./home_module/templates/**/*.html",
    "./templates/**/*.html",
    "./static/css/src/**/*.{html,js,css}"
  ],
  theme: {
    extend: {
      spacing: {
        '10p':'10%',
      },
    },
  },
  plugins: [],
}
