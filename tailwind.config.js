/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",        // تمام فایل‌های HTML در پوشه templates و زیرپوشه‌های آن
    "./**/templates/**/*.html",     // برای هر ماژول که داخلش پوشه templates دارد
    "./static/**/*.css",            // تمام فایل‌های CSS در پوشه static و زیرپوشه‌های آن
    "./**/static/**/*.css",         // برای هر ماژول که داخلش پوشه static دارد
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
