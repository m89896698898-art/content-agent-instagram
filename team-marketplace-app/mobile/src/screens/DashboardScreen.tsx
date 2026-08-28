import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";
import { useAuth } from "../context/AuthContext";
import { fetchStats } from "../api/endpoints";
import { Marketplace, Period, StatsResponse } from "../api/types";
import StatCard from "../components/StatCard";
import DailyBarChart from "../components/DailyBarChart";

const PERIODS: { key: Period; label: string }[] = [
  { key: "day", label: "День" },
  { key: "week", label: "Неделя" },
  { key: "month", label: "Месяц" },
];

const MARKETPLACES: { key: Marketplace | "all"; label: string }[] = [
  { key: "all", label: "Все" },
  { key: "wildberries", label: "Wildberries" },
  { key: "ozon", label: "Ozon" },
];

function formatMoney(n: number): string {
  return `${n.toLocaleString("ru-RU")} ₽`;
}

export default function DashboardScreen() {
  const { user, logout } = useAuth();
  const [period, setPeriod] = useState<Period>("week");
  const [marketplace, setMarketplace] = useState<Marketplace | "all">("all");
  const [data, setData] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await fetchStats(period, marketplace === "all" ? undefined : marketplace);
      setData(res);
    } catch (e) {
      setError("Не удалось загрузить данные");
    }
  }, [period, marketplace]);

  useEffect(() => {
    setLoading(true);
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const totals = (data?.stats ?? []).reduce(
    (acc, s) => {
      acc.salesAmount += s.totals.salesAmount;
      acc.ordersCount += s.totals.ordersCount;
      acc.adsSpend += s.totals.adsSpend;
      return acc;
    },
    { salesAmount: 0, ordersCount: 0, adsSpend: 0 }
  );
  const drr = totals.salesAmount > 0 ? ((totals.adsSpend / totals.salesAmount) * 100).toFixed(1) : "0";

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ padding: 16, paddingBottom: 40 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Привет, {user?.name}</Text>
          <Text style={styles.role}>{user?.role === "admin" ? "Администратор" : "Сотрудник"}</Text>
        </View>
        <Pressable onPress={logout}>
          <Text style={styles.logout}>Выйти</Text>
        </Pressable>
      </View>

      <View style={styles.segment}>
        {PERIODS.map((p) => (
          <Pressable
            key={p.key}
            style={[styles.segmentItem, period === p.key && styles.segmentItemActive]}
            onPress={() => setPeriod(p.key)}
          >
            <Text style={[styles.segmentText, period === p.key && styles.segmentTextActive]}>{p.label}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.segment}>
        {MARKETPLACES.map((m) => (
          <Pressable
            key={m.key}
            style={[styles.segmentItem, marketplace === m.key && styles.segmentItemActive]}
            onPress={() => setMarketplace(m.key)}
          >
            <Text style={[styles.segmentText, marketplace === m.key && styles.segmentTextActive]}>{m.label}</Text>
          </Pressable>
        ))}
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: 40 }} />
      ) : error ? (
        <Text style={styles.error}>{error}</Text>
      ) : (
        <>
          <View style={styles.cardsRow}>
            <StatCard label="Продажи" value={formatMoney(totals.salesAmount)} />
            <StatCard label="Заказы" value={String(totals.ordersCount)} />
            <StatCard label="Расход на рекламу" value={formatMoney(totals.adsSpend)} />
            <StatCard label="ДРР" value={`${drr}%`} sub="доля рекламных расходов" />
          </View>

          {data?.stats.map((s) => (
            <View key={s.marketplace} style={styles.mpBlock}>
              <View style={styles.mpHeader}>
                <Text style={styles.mpTitle}>{s.marketplace === "wildberries" ? "Wildberries" : "Ozon"}</Text>
                {!data.configured[s.marketplace] && (
                  <Text style={styles.mockBadge}>демо-данные</Text>
                )}
              </View>
              <DailyBarChart points={s.points} />
            </View>
          ))}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  greeting: { fontSize: 20, fontWeight: "700" },
  role: { fontSize: 13, color: "#6b7280", marginTop: 2 },
  logout: { color: "#dc2626", fontSize: 14 },
  segment: { flexDirection: "row", backgroundColor: "#f3f4f6", borderRadius: 10, padding: 4, marginBottom: 12 },
  segmentItem: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: "center" },
  segmentItemActive: { backgroundColor: "#111827" },
  segmentText: { fontSize: 13, color: "#374151" },
  segmentTextActive: { color: "#fff", fontWeight: "600" },
  cardsRow: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between", marginTop: 8 },
  mpBlock: { marginTop: 20, backgroundColor: "#f9fafb", borderRadius: 12, padding: 14 },
  mpHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 4 },
  mpTitle: { fontSize: 16, fontWeight: "700" },
  mockBadge: { fontSize: 11, color: "#b45309", backgroundColor: "#fef3c7", paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  error: { color: "#dc2626", textAlign: "center", marginTop: 40 },
});
