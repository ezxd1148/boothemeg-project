import { SymbolView, type SFSymbol } from "expo-symbols";
import { Tabs } from "expo-router";
import { useColorScheme, type ColorValue } from "react-native";

import { Colors } from "@/constants/theme";

type TabConfig = {
  name: string;
  label: string;
  icon: SFSymbol;
};

const TABS: TabConfig[] = [
  { name: "index", label: "Home", icon: "house.fill" },
  { name: "notifications", label: "Notifications", icon: "bell.badge.fill" },
  { name: "pipeline", label: "Pipeline", icon: "arrow.triangle.pull" },
  { name: "settings", label: "Settings", icon: "gearshape.fill" },
];

function TabIcon({ symbol, color }: { symbol: SFSymbol; color: ColorValue }) {
  return (
    <SymbolView tintColor={color} name={symbol} size={22} weight="medium" />
  );
}

export default function AppTabs() {
  const scheme = useColorScheme();
  const colors = Colors[scheme === "unspecified" ? "light" : scheme];

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.text,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.background,
          borderTopColor: colors.hairline,
        },
        headerStyle: {
          backgroundColor: colors.background,
        },
        headerTintColor: colors.text,
        headerShown: false,
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.label,
            tabBarIcon: ({ color }) => (
              <TabIcon symbol={tab.icon} color={color} />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}
