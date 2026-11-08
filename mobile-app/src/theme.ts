/**
 * Design tokens transcribed from VaneUI's prop vocabulary.
 *
 * VaneUI is a web component library (65 docs, no React Native target), so its
 * components cannot be imported here. Its prop *names* are the useful part:
 * `appearance`, `variant`, `size`, `shape`. This file maps those to concrete
 * values so the mobile app and any future web dashboard stay visually aligned.
 * Source of truth: vaneui get_component_props("card" | "button").
 */

export type Appearance =
  | "primary" | "accent" | "secondary" | "success"
  | "danger" | "warning" | "info";

export type Variant = "filled" | "outline" | "ghost";
export type Size = "xs" | "sm" | "md" | "lg" | "xl";

export const colors = {
  bg: "#0b0f14",
  surface: "#141b24",
  border: "#25303c",
  text: "#e8eef5",
  muted: "#8b9aab",
  primary: "#4c9aff",
  success: "#3ddc84",
  warning: "#ffb020",
  danger: "#ff5c5c",
} as const;

export const space = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 } as const;

export const radius = { rounded: 10, pill: 999, sharp: 0 } as const;

export const fontSize: Record<Size, number> = {
  xs: 11, sm: 13, md: 15, lg: 18, xl: 24,
};

export function appearanceColor(appearance: Appearance): string {
  return colors[appearance] ?? colors.primary;
}
