import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { type ColorValue } from "react-native";

import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

type TabConfig = {
  name: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
};

const TABS: TabConfig[] = [
  { name: "index", label: "Home", icon: "home" },
  { name: "notifications", label: "Notifications", icon: "notifications" },
  { name: "pipeline", label: "Pipeline", icon: "git-pull-request" },
  { name: "settings", label: "Settings", icon: "settings" },
];

function TabIcon({
  icon,
  color,
}: {
  icon: TabConfig["icon"];
  color: ColorValue;
}) {
  return <Ionicons name={icon} size={22} color={color} />;
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
              <TabIcon icon={tab.icon} color={color} />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}
