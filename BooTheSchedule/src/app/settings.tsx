import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button } from '@/components/button';
import { Card } from '@/components/card';
import { Badge } from '@/components/badge';
import { checkHealth, type HealthResponse } from '@/services/api';
import { API_BASE_URL, API_TIMEOUT } from '@/constants/api';
import { Spacing, Radius, Typography, MaxContentWidth } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export default function SettingsScreen() {
  const theme = useTheme();
  const [testing, setTesting] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestError(null);
    try {
      const h = await checkHealth();
      setHealth(h);
    } catch (e: any) {
      setTestError(e.message);
      setHealth(null);
    } finally {
      setTesting(false);
    }
  };

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        style={{ backgroundColor: theme.background }}>
        <Text style={[styles.heading, { color: theme.text }]}>Settings</Text>

        {/* ── Server Config ──────────────────────────────────────── */}
        <Card title="Server Configuration">
          <View style={styles.configRow}>
            <Text style={[styles.configLabel, { color: theme.textSecondary }]}>API URL</Text>
            <Text style={[styles.configValue, { color: theme.text }]}>{API_BASE_URL}</Text>
          </View>
          <View style={styles.configRow}>
            <Text style={[styles.configLabel, { color: theme.textSecondary }]}>Timeout</Text>
            <Text style={[styles.configValue, { color: theme.text }]}>{API_TIMEOUT / 1000}s</Text>
          </View>
          <Button
            variant="secondary"
            title={testing ? 'Testing...' : '🔌 Test Connection'}
            onPress={handleTestConnection}
            loading={testing}
          />
        </Card>

        {/* ── Connection Result ──────────────────────────────────── */}
        {testError && (
          <Card title="Connection Failed">
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: Spacing.xs }}>
              <Badge label="Offline" variant="error" />
              <Text style={[styles.errorMsg, { color: theme.error }]}>{testError}</Text>
            </View>
          </Card>
        )}

        {health && (
          <Card title="Server Status">
            <View style={styles.statusGrid}>
              <View style={styles.statusItem}>
                <Badge label="Online" variant="success" />
                <Text style={[styles.statusLabel, { color: theme.textSecondary }]}>Status</Text>
              </View>
              <View style={styles.statusItem}>
                <Badge
                  label={health.rate_limiting ? 'Enabled' : 'Disabled'}
                  variant={health.rate_limiting ? 'success' : 'warning'}
                />
                <Text style={[styles.statusLabel, { color: theme.textSecondary }]}>Rate Limit</Text>
              </View>
            </View>

            <Text style={[styles.availableTitle, { color: theme.text }]}>Available Endpoints</Text>
            {health.endpoints.map((ep, i) => (
              <Text key={i} style={[styles.endpoint, { color: theme.textSecondary }]}>
                • {ep}
              </Text>
            ))}
          </Card>
        )}

        {/* ── App Info ───────────────────────────────────────────── */}
        <Card title="About">
          <View style={styles.configRow}>
            <Text style={[styles.configLabel, { color: theme.textSecondary }]}>App</Text>
            <Text style={[styles.configValue, { color: theme.text }]}>BooTheSchedule v1.0</Text>
          </View>
          <View style={styles.configRow}>
            <Text style={[styles.configLabel, { color: theme.textSecondary }]}>Powered by</Text>
            <Text style={[styles.configValue, { color: theme.text }]}>Expo + Flask + OpenRouter</Text>
          </View>
          <Text style={[styles.hint, { color: theme.textMuted }]}>
            Change API_BASE_URL in src/constants/api.ts to point to your Flask server.
            For physical devices, use your computer's LAN IP address.
          </Text>
        </Card>
      </ScrollView>
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
    gap: Spacing.md,
    paddingBottom: 100,
  },
  heading: {
    ...Typography.displaySM,
  },
  configRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
  },
  configLabel: {
    ...Typography.bodySM,
  },
  configValue: {
    ...Typography.bodySM,
    fontWeight: '500',
  },
  errorMsg: {
    ...Typography.bodySM,
    flex: 1,
  },
  statusGrid: {
    flexDirection: 'row',
    gap: Spacing.lg,
    marginBottom: Spacing.sm,
  },
  statusItem: {
    alignItems: 'flex-start',
    gap: Spacing.xxs,
  },
  statusLabel: {
    ...Typography.caption,
  },
  availableTitle: {
    ...Typography.titleSM,
    marginBottom: Spacing.xs,
  },
  endpoint: {
    ...Typography.bodySM,
    paddingVertical: 2,
  },
  hint: {
    ...Typography.caption,
    marginTop: Spacing.sm,
  },
});
