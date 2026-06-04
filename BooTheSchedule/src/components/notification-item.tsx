import { StyleSheet, Text, View } from 'react-native';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { Badge } from './badge';
import { useTheme } from '@/hooks/use-theme';
import type { Notification } from '@/services/api';

export function NotificationItem({ app, sender, message, time, category }: Notification) {
  const theme = useTheme();

  return (
    <View style={[styles.row, { backgroundColor: theme.surfaceCard, borderColor: theme.hairlineSoft }]}>
      <View style={styles.header}>
        <Text style={[styles.app, { color: theme.brandAccent }]}>{app}</Text>
        {category && <Badge label={category} variant="default" />}
      </View>
      {sender && <Text style={[styles.sender, { color: theme.text }]}>{sender}</Text>}
      {message ? (
        <Text style={[styles.message, { color: theme.textSecondary }]} numberOfLines={2}>{message}</Text>
      ) : (
        <Text style={[styles.message, { color: theme.textMuted }]}>(no message)</Text>
      )}
      {time && <Text style={[styles.time, { color: theme.textMuted }]}>{time}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    gap: Spacing.xxs,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  app: {
    ...Typography.titleSM,
  },
  sender: {
    ...Typography.bodySM,
    fontWeight: '500',
  },
  message: {
    ...Typography.bodySM,
  },
  time: {
    ...Typography.caption,
  },
});
