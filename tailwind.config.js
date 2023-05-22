/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./hypha/templates/**/*.html",
        "./hypha/**/templates/**/*.html",
        "./hypha/**/*.{py,js}",
    ],
    theme: {
        extend: {
            colors: {
                'light-blue' : '#0d7db0',
                'tomato': '#f05e54',
                'mid-grey': '#cfcfcf',
            },
        },
    },
    plugins: [require("@tailwindcss/forms")],
};
