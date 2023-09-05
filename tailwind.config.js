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
                "light-blue": "#0d7db0",
                "dark-blue": "#0c72a0",
                tomato: "#f05e54",
                "mid-grey": "#cfcfcf",
                arsenic: "#404041",
                "fg-muted": "var(--color-fg-muted)",
                "fg-default": "var(--color-fg-default)",
            },
        },
    },
    plugins: [
        require("@tailwindcss/forms"),
        require("@tailwindcss/typography"),
    ],
};
