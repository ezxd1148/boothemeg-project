import { StyleSheet, Text, View } from 'react-native';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

interface CardProps {
  title?: string;
  subtitle?: string;
  children?: React.ReactNode;
  style?: any;
}

export function Card({ title, subtitle, children, style }: CardProps) {
  const theme = useTheme();

  return (
    <View style={[styles.card, { backgroundColor: theme.surfaceCard, borderColor: theme.hairlineSoft }, style]}>
      {title && <Text style={[styles.title, { color: theme.text }]}>{title}</Text>}
      {subtitle && <Text style={[styles.subtitle, { color: theme.textSecondary }]}>{subtitle}</Text>}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    borderWidth: 1,
  },
  title: {
    ...Typography.titleSM,
    marginBottom: Spacing.xxs,
  },
  subtitle: {
    ...Typography.bodySM,
    marginBottom: Spacing.sm,
  },
});
