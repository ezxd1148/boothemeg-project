import { useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";

import { Button } from "@/components/button";
import { Card } from "@/components/card";
import { Badge } from "@/components/badge";
import { checkHealth, type HealthResponse } from "@/services/api";
import {
  Spacing,
  Radius,
  Typography,
  MaxContentWidth,
} from "@/constants/theme";
import { useTheme } from "@/hooks/use-theme";

const QUICK_ACTIONS = [
  { title: "Fetch Notifications", route: "/notifications", icon: "📱" },
  { title: "Process Notifications", route: "/notifications", icon: "🤖" },
  { title: "Run Full Pipeline", route: "/pipeline", icon: "🚀" },
  { title: "Settings", route: "/settings", icon: "⚙️" },
] as const;

export default function HomeScreen() {
  const theme = useTheme();
  const router = useRouter();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHealth = async () => {
    try {
      setHealthError(null);
      const h = await checkHealth();
      setHealth(h);
    } catch (e: any) {
      setHealthError(e.message);
      setHealth(null);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchHealth();
    setRefreshing(false);
  };

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: theme.background }]}
    >
      <FlatList
        data={[]}
        renderItem={() => null}
        ListHeaderComponent={() => (
          <View style={styles.content}>
            {/* ── Hero ────────────────────────────────────────────── */}
            <View style={styles.hero}>
              <Text style={[styles.display, { color: theme.text }]}>
                BooTheSchedule
              </Text>
              <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
                Turn notifications into calendar events with AI
              </Text>
            </View>

            {/* ── Server Status Card ──────────────────────────────── */}
            <Card
              title="Backend Status"
              subtitle={
                healthError
                  ? `Error: ${healthError}`
                  : health
                    ? `Rate limiting: ${health.rate_limiting ? "enabled" : "disabled"}`
                    : "Checking..."
              }
            >
              <View style={styles.statusRow}>
                <Badge
                  label={
                    healthError
                      ? "Offline"
                      : health
                        ? "Connected"
                        : "Connecting..."
                  }
                  variant={
                    healthError ? "error" : health ? "success" : "warning"
                  }
                />
              </View>
            </Card>

            {/* ── Quick Actions ───────────────────────────────────── */}
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Quick Actions
            </Text>
            <View style={styles.actions}>
              {QUICK_ACTIONS.map((action) => (
                <View key={action.route} style={styles.actionWrapper}>
                  <Button
                    variant="secondary"
                    title={`${action.icon}  ${action.title}`}
                    onPress={() => router.push(action.route as any)}
                  />
                </View>
              ))}
            </View>
          </View>
        )}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={{ paddingBottom: 100 }}
        style={{ backgroundColor: theme.background }}
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
    gap: Spacing.md,
  },
  hero: {
    paddingBottom: Spacing.md,
  },
  display: {
    ...Typography.displaySM,
    marginBottom: Spacing.xxs,
  },
  subtitle: {
    ...Typography.bodyMD,
  },
  statusRow: {
    flexDirection: "row",
    gap: Spacing.xs,
  },
  sectionTitle: {
    ...Typography.titleSM,
    marginTop: Spacing.sm,
  },
  actions: {
    gap: Spacing.sm,
  },
  actionWrapper: {
    width: "100%",
  },
});
