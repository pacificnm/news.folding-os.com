/** @type {import('tailwindcss').Config} */
module.exports = {
  presets: [require("foldingos-ui/tailwind.preset")],
  // foldingos-ui ships raw .tsx (no build step) — its own source must be
  // scanned here too, since Tailwind v3 presets don't merge `content`
  // arrays (see foldingos-ui/tailwind.preset.js).
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
    "./node_modules/foldingos-ui/src/**/*.{ts,tsx}",
  ],
};
