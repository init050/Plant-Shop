/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./home_module/templates/**/*.html",
    "./account_module/templates/**/*.html",
    "./chat_module/templates/**/*.html", 
    "./article_module/templates/**/*.html", 
    "./templates/**/*.html",
    "./static/css/src/**/*.{html,js,css}"
  ],
  theme: {
    extend: {
      colors : {
        'color-footer':'222C1D'
      },
      spacing: {
        '10p':'10%',
      },
      animation: {
        'bounce': 'bounce 1s infinite',  
      }
    },
  },
  plugins: [],
}