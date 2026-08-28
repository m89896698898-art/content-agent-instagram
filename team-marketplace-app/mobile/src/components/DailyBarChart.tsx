import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { DailyPoint } from "../api/types";

export default function DailyBarChart({ points }: { points: DailyPoint[] }) {
  const max = Math.max(1, ...points.map((p) => p.salesAmount));

  return (
    <View style={styles.container}>
      {points.map((p) => (
        <View key={p.date} style={styles.row}>
          <Text style={styles.date}>{p.date.slice(5)}</Text>
          <View style={styles.barTrack}>
            <View style={[styles.bar, { width: `${Math.max(4, (p.salesAmount / max) * 100)}%` }]} />
          </View>
          <Text style={styles.amount}>{Math.round(p.salesAmount / 1000)}k</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 8 },
  row: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
  date: { width: 40, fontSize: 11, color: "#6b7280" },
  barTrack: { flex: 1, height: 10, backgroundColor: "#f3f4f6", borderRadius: 6, marginHorizontal: 8 },
  bar: { height: 10, backgroundColor: "#111827", borderRadius: 6 },
  amount: { width: 44, fontSize: 11, color: "#374151", textAlign: "right" },
});
