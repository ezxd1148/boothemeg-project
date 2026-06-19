import { StyleSheet, Text, View } from "react-native";
import { Radius, Spacing, Typography } from "@/constants/theme";
import { useTheme } from "@/hooks/use-theme";

type BadgeVariant = "default" | "success" | "warning" | "error" | "brand";

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

const variantColors: Record<BadgeVariant, keyof ReturnType<typeof useTheme>> = {
  default: "backgroundElement",
  success: "success",
  warning: "warning",
  error: "error",
  brand: "brandAccent",
};

export function Badge({ label, variant = "default" }: BadgeProps) {
  const theme = useTheme();
  const bgColor = theme[variantColors[variant]];
  const isSemantic = variant !== "default";
  // Use onPrimary for semantic badges (white text on colored background in light mode,
  // dark text on lighter background in dark mode via theme inversion)
  const textColor = isSemantic ? theme.onPrimary : theme.textSecondary;

  return (
    <View style={[styles.badge, { backgroundColor: bgColor }]}>
      <Text style={[styles.label, { color: textColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderRadius: Radius.pill,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xxs,
    alignSelf: "flex-start",
  },
  label: {
    ...Typography.caption,
    fontWeight: "600",
  },
});
