import { useState } from "react";
import {
  FlatList,
  StyleSheet,
  Text,
  View,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { Button } from "@/components/button";
import { NotificationItem } from "@/components/notification-item";
import { EventItem } from "@/components/event-item";
import { Badge } from "@/components/badge";
import {
  processNotifications,
  addToCalendar,
  type Notification,
  type CalendarEvent,
  type CalendarAddResult,
} from "@/services/api";
import {
  Spacing,
  Radius,
  Typography,
  MaxContentWidth,
} from "@/constants/theme";
import { useTheme } from "@/hooks/use-theme";

const MOCK_NOTIFICATIONS: Notification[] = [
  {
    app: "Telegram",
    sender: "Alice Chen",
    message:
      "Team standup tomorrow at 10am in Conference Room B. Bring your sprint update.",
    time: "10 min ago",
    category: "msg",
  },
  {
    app: "WhatsApp",
    sender: "Bob Martinez",
    message:
      "Dinner this Friday at 7pm at Din Tai Fung? Let me know if you can make it!",
    time: "25 min ago",
    category: "msg",
  },
  {
    app: "Gmail",
    sender: "HR Department",
    message:
      "Your performance review is scheduled for next Monday at 10am in Room 301.",
    time: "1 hour ago",
    category: "email",
  },
  {
    app: "Slack",
    sender: "Product Team",
    message: "hey what up",
    time: "2 hours ago",
    category: "msg",
  },
];

export default function NotificationsScreen() {
  const theme = useTheme();
  const [notifications] = useState<Notification[]>(MOCK_NOTIFICATIONS);
  const [events, setEvents] = useState<CalendarEvent[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [calendarResult, setCalendarResult] =
    useState<CalendarAddResult | null>(null);
  const [addingToCalendar, setAddingToCalendar] = useState(false);
  const [step, setStep] = useState<"notifications" | "results">(
    "notifications",
  );

  const handleProcess = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await processNotifications(notifications);
      setEvents(result);
      setStep("results");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setEvents(null);
    setError(null);
    setCalendarResult(null);
    setStep("notifications");
  };

  const handleAddToCalendar = async () => {
    if (!events) return;
    setAddingToCalendar(true);
    setError(null);
    try {
      const result = await addToCalendar(events);
      setCalendarResult(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setAddingToCalendar(false);
    }
  };

  if (step === "results" && events) {
    const schedulable = events.filter((e) => e.is_schedulable);
    return (
      <SafeAreaView
        style={[styles.safeArea, { backgroundColor: theme.background }]}
      >
        <FlatList
          data={events}
          keyExtractor={(_, i) => String(i)}
          renderItem={({ item }) => <EventItem event={item} />}
          ListHeaderComponent={() => (
            <View style={styles.content}>
              <Text style={[styles.heading, { color: theme.text }]}>
                Processing Results
              </Text>
              <Text style={[styles.summary, { color: theme.textSecondary }]}>
                {events.length} analyzed — {schedulable.length} schedulable
              </Text>
              {schedulable.length > 0 && !calendarResult && (
                <Button
                  variant="primary"
                  title={
                    addingToCalendar
                      ? "Adding to Calendar..."
                      : "Add to Calendar →"
                  }
                  onPress={handleAddToCalendar}
                  loading={addingToCalendar}
                />
              )}
              {calendarResult && (
                <View
                  style={{
                    flexDirection: "row",
                    gap: Spacing.xs,
                    flexWrap: "wrap",
                  }}
                >
                  <Badge
                    label={`${calendarResult.added} added`}
                    variant="success"
                  />
                  <Badge
                    label={`${calendarResult.skipped} skipped`}
                    variant="warning"
                  />
                </View>
              )}
              <View style={{ height: Spacing.sm }} />
              <Button
                variant="secondary"
                title="← Back to Notifications"
                onPress={handleReset}
              />
              <Text
                style={[
                  styles.sectionTitle,
                  { color: theme.text, marginTop: Spacing.md },
                ]}
              >
                All Events
              </Text>
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 100 }}
          style={{ backgroundColor: theme.background }}
          ItemSeparatorComponent={() => <View style={{ height: Spacing.sm }} />}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: theme.background }]}
    >
      <FlatList
        data={notifications}
        keyExtractor={(_, i) => String(i)}
        renderItem={({ item }) => <NotificationItem {...item} />}
        ListHeaderComponent={() => (
          <View style={styles.content}>
            <Text style={[styles.heading, { color: theme.text }]}>
              Notifications
            </Text>
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
              {notifications.length} notification
              {notifications.length !== 1 ? "s" : ""} ready to process
            </Text>

            {error && (
              <View
                style={[
                  styles.errorBox,
                  { backgroundColor: theme.hairlineSoft },
                ]}
              >
                <Text style={[styles.errorText, { color: theme.error }]}>
                  {error}
                </Text>
              </View>
            )}

            <Button
              variant="primary"
              title={loading ? "Processing with AI..." : "🤖 Process with AI"}
              onPress={handleProcess}
              disabled={notifications.length === 0}
              loading={loading}
            />
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              All Notifications
            </Text>
          </View>
        )}
        contentContainerStyle={{ paddingBottom: 100 }}
        style={{ backgroundColor: theme.background }}
        ItemSeparatorComponent={() => <View style={{ height: Spacing.sm }} />}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  content: {
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.lg,
    maxWidth: MaxContentWidth,
    alignSelf: "center",
    width: "100%",
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  heading: {
    ...Typography.displaySM,
  },
  subtitle: {
    ...Typography.bodyMD,
  },
  sectionTitle: {
    ...Typography.titleSM,
    marginTop: Spacing.sm,
  },
  summary: {
    ...Typography.bodySM,
  },
  errorBox: {
    padding: Spacing.sm,
    borderRadius: Radius.md,
  },
  errorText: {
    ...Typography.bodySM,
    fontWeight: "500",
  },
});
