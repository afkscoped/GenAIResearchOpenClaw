/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Fraunces', 'ui-serif', 'Georgia', 'serif'],
        body: ['Newsreader', 'ui-serif', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        ink: {
          DEFAULT: '#0B0B0F',
          deep: '#070709',
          soft: '#15151B',
          rule: '#1E1E26',
        },
        bone: {
          DEFAULT: '#EDE6D3',
          warm: '#E2D8BE',
          dim: '#A8A092',
          mute: '#6F695E',
        },
        oxblood: {
          DEFAULT: '#7B1E1E',
          deep: '#5A1414',
          glow: '#A82A2A',
        },
        chartreuse: {
          DEFAULT: '#D6FF3D',
          deep: '#A8CC1A',
        },
        teal: {
          faded: '#3E5C5A',
          mute: '#5C7977',
        },
      },
      letterSpacing: {
        tightest: '-0.045em',
      },
      boxShadow: {
        editorial: '0 30px 80px -30px rgba(123, 30, 30, 0.45)',
      },
    },
  },
  plugins: [],
};
