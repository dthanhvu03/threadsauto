/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Design System Colors from MASTER.md
        primary: {
          DEFAULT: '#2563EB', // --color-primary
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#2563EB', // Primary
          600: '#1D4ED8',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        secondary: {
          DEFAULT: '#3B82F6', // --color-secondary
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6', // Secondary
          600: '#2563EB',
        },
        cta: {
          DEFAULT: '#F97316', // --color-cta
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#F97316', // CTA/Accent
          600: '#ea580c',
          700: '#c2410c',
        },
        background: {
          DEFAULT: '#F8FAFC', // --color-background
        },
        text: {
          DEFAULT: '#1E293B', // --color-text
        },
        border: {
          DEFAULT: '#E2E8F0', // --color-border
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6',
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
      },
      boxShadow: {
        // Design System Shadows from MASTER.md
        'sm': '0 1px 2px rgba(0,0,0,0.05)', // --shadow-sm: Subtle lift
        'md': '0 4px 6px rgba(0,0,0,0.1)', // --shadow-md: Cards, buttons
        'lg': '0 10px 15px rgba(0,0,0,0.1)', // --shadow-lg: Modals, dropdowns
        'xl': '0 20px 25px rgba(0,0,0,0.15)', // --shadow-xl: Hero images, featured cards
        // Legacy shadows (keep for backward compatibility)
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'large': '0 10px 40px -10px rgba(0, 0, 0, 0.2)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
      fontFamily: {
        // Design System Typography: Inter from MASTER.md
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "'Segoe UI'",
          "'Roboto'",
          "'Oxygen'",
          "'Ubuntu'",
          "'Cantarell'",
          "'Fira Sans'",
          "'Droid Sans'",
          "'Helvetica Neue'",
          "sans-serif",
        ],
        mono: [
          "'SF Mono'",
          "Monaco",
          "'Cascadia Code'",
          "'Roboto Mono'",
          "Consolas",
          "'Courier New'",
          "monospace",
        ],
      },
      spacing: {
        '0': '0',
        '1': '0.25rem',   // 4px
        '2': '0.5rem',    // 8px
        '3': '0.75rem',   // 12px
        '4': '1rem',      // 16px
        '5': '1.25rem',   // 20px
        '6': '1.5rem',    // 24px
        '8': '2rem',      // 32px
        '10': '2.5rem',   // 40px
        '12': '3rem',     // 48px
        '16': '4rem',     // 64px
        '20': '5rem',     // 80px
        '24': '6rem',     // 96px
        '32': '8rem',     // 128px
      },
      fontSize: {
        // Responsive typography scale
        'xs': ['0.75rem', { lineHeight: '1.5' }],      // 12px - Mobile
        'xs-md': ['0.8125rem', { lineHeight: '1.5' }], // 13px - Tablet
        'xs-lg': ['0.875rem', { lineHeight: '1.5' }], // 14px - Desktop
        'sm': ['0.875rem', { lineHeight: '1.5' }],     // 14px - Mobile
        'sm-md': ['0.9375rem', { lineHeight: '1.5' }], // 15px - Tablet
        'sm-lg': ['1rem', { lineHeight: '1.5' }],      // 16px - Desktop
        'base': ['0.875rem', { lineHeight: '1.5' }],   // 14px - Mobile (base)
        'base-md': ['0.9375rem', { lineHeight: '1.5' }], // 15px - Tablet
        'base-lg': ['1rem', { lineHeight: '1.5' }],    // 16px - Desktop
        'lg': ['1.125rem', { lineHeight: '1.4' }],     // 18px - Mobile
        'lg-md': ['1.25rem', { lineHeight: '1.4' }],   // 20px - Tablet
        'lg-lg': ['1.5rem', { lineHeight: '1.4' }],    // 24px - Desktop
        'xl': ['1.5rem', { lineHeight: '1.3' }],       // 24px - Mobile
        'xl-md': ['1.75rem', { lineHeight: '1.3' }],   // 28px - Tablet
        'xl-lg': ['2rem', { lineHeight: '1.3' }],      // 32px - Desktop
        '2xl': ['1.25rem', { lineHeight: '1.3' }],     // 20px - Mobile
        '2xl-md': ['1.5rem', { lineHeight: '1.3' }],   // 24px - Tablet
        '2xl-lg': ['1.75rem', { lineHeight: '1.3' }],  // 28px - Desktop
        '3xl': ['1.125rem', { lineHeight: '1.4' }],    // 18px - Mobile
        '3xl-md': ['1.25rem', { lineHeight: '1.4' }], // 20px - Tablet
        '3xl-lg': ['1.5rem', { lineHeight: '1.4' }],  // 24px - Desktop
        '4xl': ['1rem', { lineHeight: '1.4' }],        // 16px - Mobile
        '4xl-md': ['1.125rem', { lineHeight: '1.4' }], // 18px - Tablet
        '4xl-lg': ['1.25rem', { lineHeight: '1.4' }],  // 20px - Desktop
      },
    },
  },
  plugins: [],
}
