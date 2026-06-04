import { useState } from 'react';
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/button';
import { Card } from '@/components/card';
import { Badge } from '@/components/badge';
import { EventItem } from '@/components/event-item';
import { runPipeline, type Notification, type PipelineResult } from '@/services/api';
import { Spacing, Radius, Typography, MaxContentWidth } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

const SEED_MESSAGES = [
  'Team standup tomorrow at 10am in Conference Room B',
  'Dinner this Friday at 7pm at Din Tai Fung',
  'Performance review next Monday at 10am in Room 301',
  'Flight to Tokyo on March 15th at 8am, JAL 001',
  'Dentist appointment every 6 months starting Jan 10 at 2pm',
];

export default function PipelineScreen() {
  const theme = useTheme();
  const [inputText, setInputText] = useState('');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addNotification = (message: string) => {
    if (!message.trim()) return;
    setNotifications((prev) => [
      ...prev,
      {
        app: 'Manual',
        sender: 'You',
        message: message.trim(),
        time: new Date().toLocaleString(),
        category: 'manual',
      },
    ]);
    setInputText('');
    setResult(null);
    setError(null);
  };

  const addSeedMessage = (message: string) => {
    addNotification(message);
  };

  const handleRunPipeline = async () => {
    if (notifications.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runPipeline(notifications);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setNotifications([]);
    setResult(null);
    setError(null);
    setInputText('');
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <FlatList
          data={notifications}
          keyExtractor={(_, i) => String(i)}
          renderItem={({ item }) => (
            <View style={[styles.notifItem, { borderColor: theme.hairlineSoft }]}>
              <Text style={[styles.notifApp, { color: theme.brandAccent }]}>
                {item.app}
              </Text>
              <Text style={[styles.notifMsg, { color: theme.text }]} numberOfLines={2}>
                {item.message}
              </Text>
            </View>
          )}
          ListHeaderComponent={() => (
            <View style={styles.content}>
              {/* ── Heading ──────────────────────────────────────── */}
              <Text style={[styles.heading, { color: theme.text }]}>Pipeline</Text>
              <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
                Type or select a notification, then run the full pipeline
              </Text>

              {/* ── Input ────────────────────────────────────────── */}
              <View style={styles.inputRow}>
                <TextInput
                  style={[
                    styles.textInput,
                    {
                      backgroundColor: theme.backgroundElement,
                      color: theme.text,
                      borderColor: theme.hairline,
                    },
                  ]}
                  placeholder="Type a notification message..."
                  placeholderTextColor={theme.textMuted}
                  value={inputText}
                  onChangeText={setInputText}
                  onSubmitEditing={() => addNotification(inputText)}
                  returnKeyType="done"
                  multiline
                  numberOfLines={2}
                />
                <Button
                  variant="primary"
                  title="Add"
                  onPress={() => addNotification(inputText)}
                  disabled={!inputText.trim()}
                />
              </View>

              {/* ── Seed messages ────────────────────────────────── */}
              <Text style={[styles.label, { color: theme.textSecondary }]}>
                Quick add:
              </Text>
              <View style={styles.seeds}>
                {SEED_MESSAGES.map((msg, i) => (
                  <View key={i} style={styles.seedWrapper}>
                    <Button
                      variant="secondary"
                      title={msg.length > 40 ? msg.slice(0, 40) + '…' : msg}
                      onPress={() => addSeedMessage(msg)}
                    />
                  </View>
                ))}
              </View>

              {/* ── Pipeline Actions ─────────────────────────────── */}
              <View style={styles.actions}>
                <Button
                  variant="primary"
                  title={loading ? 'Running Pipeline...' : `🚀 Run Pipeline (${notifications.length})`}
                  onPress={handleRunPipeline}
                  disabled={notifications.length === 0}
                  loading={loading}
                />
                {notifications.length > 0 && (
                  <Button variant="secondary" title="Clear All" onPress={handleClear} />
                )}
              </View>

              {/* ── Error ────────────────────────────────────────── */}
              {error && (
                <View style={[styles.errorBox, { backgroundColor: theme.hairlineSoft }]}>
                  <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
                </View>
              )}

              {/* ── Result ───────────────────────────────────────── */}
              {result && (
                <Card title="Pipeline Result">
                  <View style={styles.resultStats}>
                    <Badge label={`${result.processed} processed`} variant="default" />
                    <Badge label={`${result.schedulable} schedulable`} variant="brand" />
                    <Badge label={`${result.added} added`} variant="success" />
                    <Badge label={`${result.skipped} skipped`} variant="warning" />
                  </View>
                  {result.events.map((ev, i) => (
                    <View key={i} style={{ marginTop: Spacing.xs }}>
                      <View style={{ flexDirection: 'row', gap: Spacing.xs }}>
                        {ev.summary && (
                          <Text style={[styles.eventLine, { color: theme.text }]}>
                            {ev.summary}
                          </Text>
                        )}
                        {ev.link && (
                          <Text style={[styles.eventLine, { color: theme.success }]}>✓ Added</Text>
                        )}
                        {ev.error && (
                          <Text style={[styles.eventLine, { color: theme.error }]}>
                            ✗ {ev.error}
                          </Text>
                        )}
                      </View>
                    </View>
                  ))}
                </Card>
              )}

              {notifications.length > 0 && (
                <Text style={[styles.listTitle, { color: theme.text }]}>
                  Queued ({notifications.length})
                </Text>
              )}
            </View>
          )}
          contentContainerStyle={{ paddingBottom: 100 }}
          style={{ backgroundColor: theme.background }}
          keyboardShouldPersistTaps="handled"
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  content: {
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.lg,
    maxWidth: MaxContentWidth,
    alignSelf: 'center',
    width: '100%',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  heading: {
    ...Typography.displaySM,
  },
  subtitle: {
    ...Typography.bodyMD,
  },
  listTitle: {
    ...Typography.titleSM,
  },
  label: {
    ...Typography.caption,
  },
  inputRow: {
    flexDirection: 'column',
    gap: Spacing.sm,
  },
  textInput: {
    ...Typography.bodyMD,
    borderWidth: 1,
    borderRadius: Radius.lg,
    padding: Spacing.sm,
    minHeight: 60,
    textAlignVertical: 'top',
  },
  seeds: {
    gap: Spacing.xs,
  },
  seedWrapper: {
    width: '100%',
  },
  actions: {
    gap: Spacing.sm,
  },
  errorBox: {
    padding: Spacing.sm,
    borderRadius: Radius.md,
  },
  errorText: {
    ...Typography.bodySM,
    fontWeight: '500',
  },
  notifItem: {
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    gap: Spacing.xxs,
  },
  notifApp: {
    ...Typography.caption,
    fontWeight: '600',
  },
  notifMsg: {
    ...Typography.bodySM,
  },
  resultStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  eventLine: {
    ...Typography.bodySM,
  },
});
