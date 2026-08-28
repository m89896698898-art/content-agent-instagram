import { daysForPeriod } from "./dateRange";
import { DailyPoint, Period } from "./types";

const STATS_BASE = "https://statistics-api.wildberries.ru";
const ADVERT_BASE = "https://advert-api.wildberries.ru";

// -- Sales -------------------------------------------------------------
// GET /api/v1/supplier/sales?dateFrom=YYYY-MM-DD
// Returns a flat array of individual sale records. Each record roughly has:
//   { date: string, forPay: number, priceWithDisc: number, saleID: string, ... }
// "forPay" is what WB actually pays the seller after their commission; we
// use it as the revenue figure. One array entry = one sold unit.
interface WbSaleRecord {
  date: string; // ISO datetime
  forPay: number;
  saleID: string;
}

async function fetchWbSales(apiKey: string, dateFrom: string): Promise<WbSaleRecord[]> {
  const res = await fetch(`${STATS_BASE}/api/v1/supplier/sales?dateFrom=${dateFrom}`, {
    headers: { Authorization: apiKey },
  });
  if (!res.ok) {
    throw new Error(`WB sales request failed: ${res.status} ${await res.text().catch(() => "")}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error("WB sales response was not an array — API shape may have changed");
  }
  return data as WbSaleRecord[];
}

// -- Ads -----------------------------------------------------------------
// GET /adv/v1/promotion/count -> list of active campaign ids
// POST /adv/v2/fullstats { body: [{ id, dates: [YYYY-MM-DD, ...] }] }
//   -> per-campaign, per-day stats: { views, clicks, sum (spend), orders }
interface WbCampaignListItem {
  advertId: number;
}

interface WbCampaignDayStat {
  date: string;
  views: number;
  clicks: number;
  sum: number; // spend, RUB
  orders?: number;
}

interface WbFullStatsEntry {
  advertId: number;
  days?: WbCampaignDayStat[];
}

async function fetchWbAdsCampaignIds(apiKey: string): Promise<number[]> {
  const res = await fetch(`${ADVERT_BASE}/adv/v1/promotion/count`, {
    headers: { Authorization: apiKey },
  });
  if (!res.ok) {
    throw new Error(`WB campaign list request failed: ${res.status}`);
  }
  const data = await res.json();
  // Response groups campaigns by status/type; flatten whatever shape we get.
  const ids: number[] = [];
  const collect = (node: unknown) => {
    if (Array.isArray(node)) {
      node.forEach((item) => {
        if (item && typeof item === "object" && "advertId" in item) {
          ids.push((item as WbCampaignListItem).advertId);
        } else {
          collect(item);
        }
      });
    } else if (node && typeof node === "object") {
      Object.values(node as Record<string, unknown>).forEach(collect);
    }
  };
  collect(data);
  return ids;
}

async function fetchWbAdsStats(apiKey: string, campaignIds: number[], dates: string[]): Promise<WbFullStatsEntry[]> {
  if (campaignIds.length === 0) return [];
  const res = await fetch(`${ADVERT_BASE}/adv/v2/fullstats`, {
    method: "POST",
    headers: { Authorization: apiKey, "Content-Type": "application/json" },
    body: JSON.stringify(campaignIds.map((id) => ({ id, dates }))),
  });
  if (!res.ok) {
    throw new Error(`WB ads stats request failed: ${res.status}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error("WB ads stats response was not an array — API shape may have changed");
  }
  return data as WbFullStatsEntry[];
}

// -- Aggregation -----------------------------------------------------------

export async function fetchWildberriesDailyPoints(apiKey: string, period: Period): Promise<DailyPoint[]> {
  const days = daysForPeriod(period);
  const dateFrom = new Date();
  dateFrom.setDate(dateFrom.getDate() - (days - 1));
  const dateFromStr = dateFrom.toISOString().slice(0, 10);

  const byDate = new Map<string, DailyPoint>();
  const ensure = (date: string): DailyPoint => {
    let p = byDate.get(date);
    if (!p) {
      p = { date, salesAmount: 0, ordersCount: 0, adsSpend: 0, adsImpressions: 0, adsClicks: 0, adsOrders: 0 };
      byDate.set(date, p);
    }
    return p;
  };

  const sales = await fetchWbSales(apiKey, dateFromStr);
  for (const sale of sales) {
    const date = sale.date.slice(0, 10);
    const point = ensure(date);
    point.salesAmount += sale.forPay;
    point.ordersCount += 1;
  }

  try {
    const campaignIds = await fetchWbAdsCampaignIds(apiKey);
    const dates: string[] = [];
    for (let i = 0; i < days; i++) {
      const d = new Date(dateFrom);
      d.setDate(d.getDate() + i);
      dates.push(d.toISOString().slice(0, 10));
    }
    const adsStats = await fetchWbAdsStats(apiKey, campaignIds, dates);
    for (const campaign of adsStats) {
      for (const day of campaign.days ?? []) {
        const date = day.date.slice(0, 10);
        const point = ensure(date);
        point.adsSpend += day.sum ?? 0;
        point.adsImpressions += day.views ?? 0;
        point.adsClicks += day.clicks ?? 0;
        point.adsOrders += day.orders ?? 0;
      }
    }
  } catch (err) {
    // Ads data is a bonus on top of sales — if the advert API call fails
    // (e.g. no active campaigns, or the response shape changed), keep the
    // sales numbers and just leave ad figures at zero instead of failing
    // the whole dashboard.
    console.warn("[wildberries] ads stats unavailable:", err instanceof Error ? err.message : err);
  }

  return Array.from(byDate.values()).sort((a, b) => a.date.localeCompare(b.date));
}
