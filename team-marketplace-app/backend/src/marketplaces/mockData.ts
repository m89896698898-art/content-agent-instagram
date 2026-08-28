import { DailyPoint, Marketplace, MarketplaceStats, Period } from "./types";
import { daysForPeriod, lastNDates } from "./dateRange";

// Deterministic pseudo-random generator seeded by a string, so mock numbers
// stay stable across requests instead of jumping around on every reload.
function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const x = Math.sin(hash) * 10000;
  return x - Math.floor(x);
}

function generateDailyPoint(marketplace: Marketplace, date: string): DailyPoint {
  const base = marketplace === "wildberries" ? 45000 : 32000;
  const r1 = seededRandom(`${marketplace}-${date}-sales`);
  const r2 = seededRandom(`${marketplace}-${date}-orders`);
  const r3 = seededRandom(`${marketplace}-${date}-ads`);

  const salesAmount = Math.round(base + r1 * base * 0.8);
  const ordersCount = Math.round(10 + r2 * 30);
  const adsSpend = Math.round(salesAmount * (0.05 + r3 * 0.1));
  const adsImpressions = Math.round(5000 + r3 * 15000);
  const adsClicks = Math.round(adsImpressions * (0.01 + r1 * 0.02));
  const adsOrders = Math.round(ordersCount * (0.2 + r2 * 0.3));

  return { date, salesAmount, ordersCount, adsSpend, adsImpressions, adsClicks, adsOrders };
}

export function generateMockStats(marketplace: Marketplace, period: Period): MarketplaceStats {
  const dates = lastNDates(daysForPeriod(period));
  const points = dates.map((date) => generateDailyPoint(marketplace, date));

  const totals = points.reduce(
    (acc, p) => {
      acc.salesAmount += p.salesAmount;
      acc.ordersCount += p.ordersCount;
      acc.adsSpend += p.adsSpend;
      acc.adsImpressions += p.adsImpressions;
      acc.adsClicks += p.adsClicks;
      acc.adsOrders += p.adsOrders;
      return acc;
    },
    { salesAmount: 0, ordersCount: 0, adsSpend: 0, adsImpressions: 0, adsClicks: 0, adsOrders: 0 }
  );

  const drr = totals.salesAmount > 0 ? Number(((totals.adsSpend / totals.salesAmount) * 100).toFixed(2)) : 0;

  return { marketplace, period, points, totals: { ...totals, drr } };
}
