/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'mia-pink': '#ffb6c1',
                'mia-pink-dark': '#ff69b4',
                'cyber-black': '#1a1a1a',
                'cyber-gray': '#2d2d2d',
                'neon-blue': '#00f3ff',
                'neon-purple': '#bc13fe',
            },
            fontFamily: {
                sans: ['Inter', 'Microsoft YaHei', 'sans-serif'],
                wenkai: ['WenKai', 'Microsoft YaHei', 'monospace'],
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
