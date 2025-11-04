import { useState } from "react";
import { Appearance, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useTheme } from "@/theme/useTheme";

export default function SettingsScreen() {
  const { mode, setMode, resolved, colors } = useTheme();
  const [trackLocation, setTrackLocation] = useState(true);

  const Choice = ({ value, label }: { value: "system" | "light" | "dark"; label: string }) => {
    const active = mode === value;
    return (
      <TouchableOpacity
        onPress={() => setMode(value)}
        style={[
          s.choiceChip,
          { backgroundColor: active ? colors.primary : colors.card, borderColor: colors.border },
        ]}
        activeOpacity={0.9}
      >
        <Text style={[s.choiceChipText, { color: active ? "#fff" : colors.text }]}>{label}</Text>
      </TouchableOpacity>
    );
  };

  return (
    <ScrollView style={[s.page, { backgroundColor: colors.bg }]} contentContainerStyle={{ padding: 16, gap: 16 }}>
      {/* Preferences */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Preferences</Text>

        <TouchableOpacity style={s.toggleRow} onPress={() => setTrackLocation((v) => !v)}>
          <Text style={[s.toggleLabel, { color: colors.text }]}>Location tracking</Text>
          <View
            style={[
              s.toggle,
              { backgroundColor: trackLocation ? colors.primary : colors.card, borderColor: colors.border },
            ]}
          >
            <View style={[s.knob, trackLocation && s.knobOn]} />
          </View>
        </TouchableOpacity>
        <Text style={[s.helperText, { color: colors.textDim }]}>
          Used to center the map and improve recommendations. Never shares exact coordinates publicly.
        </Text>
      </View>

      {/* Appearance */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Appearance</Text>
        <View style={{ flexDirection: "row", gap: 8 }}>
          <Choice value="system" label="System" />
          <Choice value="light" label="Light" />
          <Choice value="dark" label="Dark" />
        </View>
        <Text style={[s.helperText, { color: colors.textDim }]}>
          Currently using <Text style={{ fontWeight: "700", color: colors.text }}>{resolved}</Text> theme.
        </Text>
      </View>

      {/* Privacy */}
      <View>
        <Text style={[s.sectionTitle, { color: colors.text }]}>Privacy</Text>
        <Text style={[s.bodyText, { color: colors.text }]}>
          Check-ins are anonymous by default. Friend presence (future) is opt-in and shown only at the place level.
        </Text>
      </View>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  page: { flex: 1 },
  sectionTitle: { fontSize: 18, fontWeight: "800", marginBottom: 6 },
  helperText: { fontSize: 12 },
  bodyText: { fontSize: 14 },

  toggleRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingVertical: 8 },
  toggleLabel: { fontSize: 16, fontWeight: "700" },
  toggle: { width: 54, height: 32, borderRadius: 999, padding: 4, borderWidth: 1 },
  knob: { width: 24, height: 24, borderRadius: 12, backgroundColor: "#fff" },
  knobOn: { marginLeft: 22 },

  choiceChip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, borderWidth: 1 },
  choiceChipText: { fontWeight: "700" },
});
