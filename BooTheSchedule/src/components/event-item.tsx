import { StyleSheet, Text, View } from 'react-native';
import { Radius, Spacing, Typography } from '@/constants/theme';
import { Badge } from './badge';
import { useTheme } from '@/hooks/use-theme';
import type { CalendarEvent } from '@/services/api';

interface EventItemProps {
  event: CalendarEvent;
}

export function EventItem({ event }: EventItemProps) {
  const theme = useTheme();

  return (
    <View style={[styles.row, { backgroundColor: theme.surfaceCard, borderColor: theme.hairlineSoft }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]} numberOfLines={1}>
          {event.title || 'Untitled'}
        </Text>
        <Badge
          label={event.is_schedulable ? '✓ Scheduled' : '— Skipped'}
          variant={event.is_schedulable ? 'success' : 'default'}
        />
      </View>

      {event.date && (
        <View style={styles.datetime}>
          <Text style={[styles.date, { color: theme.brandAccent }]}>
            {event.date}
            {event.time ? ` at ${event.time}` : ''}
          </Text>
          {event.duration_minutes && (
            <Text style={[styles.duration, { color: theme.textMuted }]}>
              ({event.duration_minutes} min)
            </Text>
          )}
        </View>
      )}

      {event.description ? (
        <Text style={[styles.description, { color: theme.textSecondary }]} numberOfLines={2}>
          {event.description}
        </Text>
      ) : null}

      {event.location && (
        <Text style={[styles.location, { color: theme.textSecondary }]}>
          📍 {event.location}
        </Text>
      )}

      {event.attendees && event.attendees.length > 0 && (
        <Text style={[styles.attendees, { color: theme.textMuted }]} numberOfLines={1}>
          👥 {event.attendees.join(', ')}
        </Text>
      )}

      {event.recurrence && (
        <Badge label={`🔁 ${event.recurrence}`} variant="brand" />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    borderRadius: Radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    gap: Spacing.xs,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    ...Typography.titleSM,
    flex: 1,
    marginRight: Spacing.xs,
  },
  datetime: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  date: {
    ...Typography.bodySM,
    fontWeight: '500',
  },
  duration: {
    ...Typography.caption,
  },
  description: {
    ...Typography.bodySM,
  },
  location: {
    ...Typography.bodySM,
  },
  attendees: {
    ...Typography.caption,
  },
});
