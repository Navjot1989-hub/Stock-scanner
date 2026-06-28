/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f3d5e",
        accent: "#0ea5a4",
      },
    },
  },
  plugins: [],
};
