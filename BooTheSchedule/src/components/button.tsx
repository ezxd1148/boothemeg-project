import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';
import { Radius, Spacing, ButtonHeight, Typography } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  onPress: () => void;
  title: string;
  disabled?: boolean;
  loading?: boolean;
}

export function Button({ variant = 'primary', onPress, title, disabled, loading }: ButtonProps) {
  const theme = useTheme();
  const isPrimary = variant === 'primary';

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor: isPrimary
            ? disabled ? theme.textMuted : theme.primary
            : 'transparent',
          borderColor: isPrimary ? 'transparent' : theme.hairline,
          borderWidth: isPrimary ? 0 : 1,
          opacity: pressed ? 0.85 : 1,
        },
      ]}>
      {loading ? (
        <ActivityIndicator color={isPrimary ? theme.onPrimary : theme.text} size="small" />
      ) : (
        <Text style={[styles.text, { color: isPrimary ? theme.onPrimary : theme.text }]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    height: ButtonHeight,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: Radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 100,
  },
  text: {
    ...Typography.button,
  },
});
