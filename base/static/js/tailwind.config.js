module.exports = {
  content: [
    '../templates/**/*.html',
    '../static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'denr-blue': '#1a4d8c',
        'denr-blue-light': '#2a5e9e',
        'denr-green': '#2d8659',
        'denr-green-light': '#3ca76c',
        'light-green': '#e8f5e9'
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif']
      }
    }
  },
  plugins: [],
} 