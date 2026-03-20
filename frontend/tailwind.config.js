var config = {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                um: {
                    bg: "var(--um-bg)",
                    surface: "var(--um-surface)",
                    border: "var(--um-border)",
                    cyan: "var(--um-cyan)",
                    green: "var(--um-green)",
                    red: "var(--um-red)",
                    amber: "var(--um-amber)",
                    purple: "var(--um-purple)",
                    text: "var(--um-text)",
                    muted: "var(--um-muted)"
                }
            },
            fontFamily: {
                body: ["Inter", "sans-serif"],
                display: ["Space Grotesk", "sans-serif"],
                mono: ["JetBrains Mono", "monospace"]
            },
            boxShadow: {
                cyan: "0 0 0 1px rgba(0, 217, 255, 0.24), 0 18px 48px rgba(0, 217, 255, 0.12)",
                emergency: "0 0 0 1px rgba(255, 51, 85, 0.24), 0 18px 48px rgba(255, 51, 85, 0.14)"
            },
            keyframes: {
                glow: {
                    "0%, 100%": { boxShadow: "0 0 0 rgba(0, 255, 136, 0.1)" },
                    "50%": { boxShadow: "0 0 22px rgba(0, 255, 136, 0.55)" }
                },
                pulsePath: {
                    "0%": { strokeDashoffset: "120" },
                    "100%": { strokeDashoffset: "0" }
                },
                statFloat: {
                    "0%": { transform: "translateY(0px)" },
                    "50%": { transform: "translateY(-2px)" },
                    "100%": { transform: "translateY(0px)" }
                }
            },
            animation: {
                glow: "glow 1.6s ease-in-out infinite",
                "pulse-path": "pulsePath 2s linear infinite",
                "stat-float": "statFloat 2.4s ease-in-out infinite"
            }
        }
    },
    plugins: []
};
export default config;
