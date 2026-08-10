import type { Config } from "tailwindcss";
import tailwindAnimate from "tailwindcss-animate";

// Design tokens per PRD Chapter 5 (Design System & UI Standards).
// Do not introduce new colors, spacing, or typography values outside this file.
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./features/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#1E3A8A", foreground: "#FFFFFF" },
        secondary: { DEFAULT: "#2563EB", foreground: "#FFFFFF" },
        accent: { DEFAULT: "#0F766E", foreground: "#FFFFFF" },
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        background: "#F8FAFC",
        surface: "#FFFFFF",
        sidebar: "#0F172A",
        border: "#E5E7EB",
        "text-primary": "#111827",
        "text-secondary": "#6B7280",
        disabled: "#9CA3AF",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "Segoe UI", "Roboto", "sans-serif"],
      },
      fontSize: {
        display: ["48px", { lineHeight: "120%", fontWeight: "700" }],
        h1: ["36px", { lineHeight: "120%", fontWeight: "700" }],
        h2: ["30px", { lineHeight: "120%", fontWeight: "600" }],
        h3: ["24px", { lineHeight: "120%", fontWeight: "600" }],
        h4: ["20px", { lineHeight: "120%", fontWeight: "600" }],
        h5: ["18px", { lineHeight: "120%", fontWeight: "600" }],
        "body-lg": ["16px", { lineHeight: "160%", fontWeight: "400" }],
        body: ["14px", { lineHeight: "160%", fontWeight: "400" }],
        caption: ["12px", { lineHeight: "160%", fontWeight: "400" }],
        button: ["14px", { lineHeight: "120%", fontWeight: "600" }],
      },
      spacing: {
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        6: "24px",
        8: "32px",
        10: "40px",
        12: "48px",
        14: "56px",
        16: "64px",
        20: "80px",
        24: "96px",
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "16px",
        modal: "20px",
        card: "16px",
      },
      boxShadow: {
        "level-1": "0 1px 2px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.08)",
        "level-2": "0 4px 6px rgba(15, 23, 42, 0.07), 0 2px 4px rgba(15, 23, 42, 0.06)",
        "level-3": "0 10px 15px rgba(15, 23, 42, 0.08), 0 4px 6px rgba(15, 23, 42, 0.05)",
        "level-4": "0 20px 25px rgba(15, 23, 42, 0.1), 0 8px 10px rgba(15, 23, 42, 0.06)",
      },
      transitionDuration: {
        micro: "150ms",
        card: "180ms",
        dialog: "220ms",
        page: "250ms",
      },
      maxWidth: {
        content: "1600px",
        form: "720px",
        dialog: "720px",
      },
      screens: {
        tablet: "1024px",
        laptop: "1280px",
        desktop: "1440px",
        "desktop-xl": "1600px",
      },
    },
  },
  plugins: [tailwindAnimate],
};

export default config;
