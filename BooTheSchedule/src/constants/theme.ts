/**
 * DESIGN.md theme — Cal.com inspired design system.
 * Color palette, typography, spacing, and border radius tokens.
 */

import { Platform } from "react-native";
import { lightColors, darkColors } from "./colors";

// Re-export for backward compatibility with existing components
export const Colors = {
  light: lightColors,
  dark: darkColors,
} as const;

export type ThemeColor = keyof typeof lightColors & keyof typeof darkColors;

// ── Typography ────────────────────────────────────────────────────────────────
// DESIGN.md hierarchy: display-xl → display-lg → display-md → display-sm →
//                       title-lg → title-md → title-sm →
//                       body-md → body-sm → caption → code → button → nav-link

export const Fonts = Platform.select({
  ios: {
    sans: "system-ui",
    serif: "ui-serif",
    rounded: "ui-rounded",
    mono: "ui-monospace",
  },
  default: {
    sans: "normal",
    serif: "serif",
    rounded: "normal",
    mono: "monospace",
  },
  web: {
    sans: "var(--font-display)",
    serif: "var(--font-serif)",
    rounded: "var(--font-rounded)",
    mono: "var(--font-mono)",
  },
});

export const Typography = {
  displayXL: {
    fontSize: 64,
    fontWeight: "600" as const,
    lineHeight: 72,
    letterSpacing: -2,
  },
  displayLG: {
    fontSize: 48,
    fontWeight: "600" as const,
    lineHeight: 56,
    letterSpacing: -1.5,
  },
  displayMD: {
    fontSize: 36,
    fontWeight: "600" as const,
    lineHeight: 44,
    letterSpacing: -1,
  },
  displaySM: {
    fontSize: 28,
    fontWeight: "600" as const,
    lineHeight: 36,
    letterSpacing: -0.5,
  },
  titleLG: {
    fontSize: 22,
    fontWeight: "600" as const,
    lineHeight: 28,
    letterSpacing: -0.3,
  },
  titleMD: {
    fontSize: 18,
    fontWeight: "600" as const,
    lineHeight: 24,
    letterSpacing: 0,
  },
  titleSM: {
    fontSize: 16,
    fontWeight: "600" as const,
    lineHeight: 22,
    letterSpacing: 0,
  },
  bodyMD: {
    fontSize: 16,
    fontWeight: "400" as const,
    lineHeight: 24,
    letterSpacing: 0,
  },
  bodySM: {
    fontSize: 14,
    fontWeight: "400" as const,
    lineHeight: 20,
    letterSpacing: 0,
  },
  caption: {
    fontSize: 13,
    fontWeight: "400" as const,
    lineHeight: 18,
    letterSpacing: 0,
  },
  code: {
    fontSize: 14,
    fontWeight: "500" as const,
    lineHeight: 20,
    letterSpacing: 0,
  },
  button: {
    fontSize: 14,
    fontWeight: "600" as const,
    lineHeight: 20,
    letterSpacing: 0,
  },
  navLink: {
    fontSize: 14,
    fontWeight: "500" as const,
    lineHeight: 20,
    letterSpacing: 0,
  },
} as const;

// ── Radius (DESIGN.md rounded scale) ──────────────────────────────────────────
export const Radius = {
  xs: 4,
  sm: 6,
  md: 8,
  lg: 12,
  xl: 16,
  pill: 9999,
  full: 9999,
} as const;

// ── Spacing (DESIGN.md scale) ─────────────────────────────────────────────────
export const Spacing = {
  xxs: 4,
  xs: 8,
  sm: 12,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  section: 96,
  // Legacy aliases for backward compatibility
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

// ── Layout ────────────────────────────────────────────────────────────────────
export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 600;
export const ButtonHeight = 40;
export const TopNavHeight = 64;
export const IconButtonSize = 36;
