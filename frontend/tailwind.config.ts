import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors from specification
        brand: {
          900: "#0F1724", // Primary Deep
          800: "#1e293b",
          700: "#334155",
          600: "#0F6FFF", // Primary
          500: "#3b82f6",
          400: "#61A6FF", // Accent
          300: "#93c5fd",
          200: "#dbeafe",
          100: "#eff6ff",
        },
        success: "#16A34A", // green-600
        warning: "#F59E0B", // amber-500
        danger: "#EF4444", // red-500
        muted: "#6B7280", // gray-500
        bg: "#FAFBFE", // off-white

        // Trust score colors
        trust: {
          high: "#16A34A", // green
          medium: "#F59E0B", // amber
          low: "#EF4444", // red
        },

        // Add standard Tailwind colors for compatibility
        gray: {
          50: "#f9fafb",
          100: "#f3f4f6",
          200: "#e5e7eb",
          300: "#d1d5db",
          400: "#9ca3af",
          500: "#6b7280",
          600: "#4b5563",
          700: "#374151",
          800: "#1f2937",
          900: "#111827",
        },

        // Custom outline colors for focus states
        ring: {
          brand: "#0F6FFF",
        },
        outline: {
          brand: "#0F6FFF",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      spacing: {
        '18': '4.5rem', // For spacing consistency
        '88': '22rem',
        '92': '23rem',
        '96': '24rem',
        '100': '25rem',
        '104': '26rem',
        '108': '27rem',
        '112': '28rem',
        '116': '29rem',
        '120': '30rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-in-out',
        'slide-down': 'slideDown 0.3s ease-in-out',
        'slide-left': 'slideLeft 0.26s ease-in-out',
        'scale-in': 'scaleIn 0.18s ease-in-out',
        'pulse-subtle': 'pulseSubtle 1.8s ease-in-out infinite',
        'shake-attention': 'shakeAttention 0.4s ease-in-out',
        'shimmer': 'shimmer 1.2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideLeft: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.8)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSubtle: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        shakeAttention: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-4px)' },
          '75%': { transform: 'translateX(4px)' },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(15, 26, 36, 0.08)',
        'medium': '0 4px 16px rgba(15, 26, 36, 0.12)',
        'strong': '0 8px 32px rgba(15, 26, 36, 0.16)',
        'trust-glow': '0 0 0 2px rgba(22, 163, 74, 0.2), 0 4px 16px rgba(22, 163, 74, 0.1)',
        'warning-glow': '0 0 0 2px rgba(245, 158, 11, 0.2), 0 4px 16px rgba(245, 158, 11, 0.1)',
        'danger-glow': '0 0 0 2px rgba(239, 68, 68, 0.2), 0 4px 16px rgba(239, 68, 68, 0.1)',
      },
      borderRadius: {
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [],
};

export default config;
