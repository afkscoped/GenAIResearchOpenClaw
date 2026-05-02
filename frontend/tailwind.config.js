/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        prism: '0 0 80px rgba(99, 102, 241, 0.25)',
      },
    },
  },
  plugins: [],
};
