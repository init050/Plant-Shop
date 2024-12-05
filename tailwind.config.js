/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',  
    './**/templates/**/*.html', 
    './static/js/**/*.js',   
    './static/css/**/*.css',  
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1E40AF',
        'ww':'1B2316',
        secondary: '#64748B',
      },
    },
  },
  plugins: [],
};
