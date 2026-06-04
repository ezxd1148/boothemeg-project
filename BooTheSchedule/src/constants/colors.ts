/**
 * DESIGN.md color palette — Cal.com inspired design system.
 * Anchored on white canvas with black primary CTAs.
 */

export const palette = {
  // ── Brand & Primary ───────────────────────────────────────────────────────
  primary: '#1A1A1A',
  primaryActive: '#000000',
  primaryDisabled: '#A0A0A0',

  // ── Ink / Text ────────────────────────────────────────────────────────────
  ink: '#1A1A1A',
  body: '#4B4B4B',
  muted: '#8A8A8A',
  mutedSoft: '#B5B5B5',

  // ── Hairlines ─────────────────────────────────────────────────────────────
  hairline: '#D4D4D4',
  hairlineSoft: '#EAEAEA',

  // ── Surfaces ──────────────────────────────────────────────────────────────
  canvas: '#FFFFFF',
  surfaceSoft: '#F7F7F7',
  surfaceCard: '#FFFFFF',
  surfaceStrong: '#F0F0F0',
  surfaceDark: '#1A1A1A',
  surfaceDarkElevated: '#2A2A2A',

  // ── On-colors ─────────────────────────────────────────────────────────────
  onPrimary: '#FFFFFF',
  onDark: '#FFFFFF',
  onDarkSoft: '#B5B5B5',

  // ── Brand accent (blue) ───────────────────────────────────────────────────
  brandAccent: '#3B82F6',

  // ── Semantic ──────────────────────────────────────────────────────────────
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',

  // ── Badge colors ──────────────────────────────────────────────────────────
  badgeOrange: '#F97316',
  badgePink: '#EC4899',
  badgeViolet: '#8B5CF6',
  badgeEmerald: '#10B981',
} as const;

// ── Light mode semantic mapping ──────────────────────────────────────────────
export const lightColors = {
  text: palette.ink,
  textSecondary: palette.body,
  textMuted: palette.muted,
  background: palette.canvas,
  backgroundElement: palette.surfaceSoft,
  backgroundSelected: palette.surfaceStrong,
  surfaceCard: palette.surfaceCard,
  surfaceDark: palette.surfaceDark,
  hairline: palette.hairline,
  hairlineSoft: palette.hairlineSoft,
  primary: palette.primary,
  onPrimary: palette.onPrimary,
  brandAccent: palette.brandAccent,
  success: palette.success,
  warning: palette.warning,
  error: palette.error,
  // badge
  badgeOrange: palette.badgeOrange,
  badgePink: palette.badgePink,
  badgeViolet: palette.badgeViolet,
  badgeEmerald: palette.badgeEmerald,
} as const;

// ── Dark mode semantic mapping ───────────────────────────────────────────────
export const darkColors = {
  text: palette.onDark,
  textSecondary: palette.onDarkSoft,
  textMuted: '#6B7280',
  background: palette.ink,
  backgroundElement: palette.surfaceDarkElevated,
  backgroundSelected: '#3A3A3A',
  surfaceCard: palette.surfaceDarkElevated,
  surfaceDark: palette.canvas,
  hairline: '#3A3A3A',
  hairlineSoft: '#2A2A2A',
  primary: palette.onPrimary,
  onPrimary: palette.ink,
  brandAccent: '#60A5FA',
  success: '#34D399',
  warning: '#FBBF24',
  error: '#F87171',
  // badge
  badgeOrange: '#FB923C',
  badgePink: '#F472B6',
  badgeViolet: '#A78BFA',
  badgeEmerald: '#34D399',
} as const;
