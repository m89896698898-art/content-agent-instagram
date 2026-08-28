import React from "react";
import { StyleSheet, Text, View } from "react-native";

export default function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <View style={styles.card}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
      {sub ? <Text style={styles.sub}>{sub}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flexBasis: "48%",
    backgroundColor: "#f9fafb",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
  },
  label: { fontSize: 12, color: "#6b7280", marginBottom: 6 },
  value: { fontSize: 20, fontWeight: "700", color: "#111827" },
  sub: { fontSize: 11, color: "#9ca3af", marginTop: 4 },
});
