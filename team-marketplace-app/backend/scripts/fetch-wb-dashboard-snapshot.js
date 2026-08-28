// Fetches real Wildberries sales (and, best-effort, ads) data and prints a
// JSON snapshot shaped for the dashboard: per-day points for the last 30
// days, from which day/week/month views can be sliced.
// Run:  WB_API_KEY="токен" node fetch-wb-dashboard-snapshot.js

const apiKey = process.env.WB_API_KEY;
if (!apiKey) {
  console.error("WB_API_KEY is not set");
  process.exit(1);
}

const STATS_BASE = "https://statistics-api.wildberries.ru";
const ADVERT_BASE = "https://advert-api.wildberries.ru";

function lastNDates(n) {
  const dates = [];
  const today = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    dates.push(d.toISOString().slice(0, 10));
  }
  return dates;
}

async function fetchSales(dateFrom) {
  const res = await fetch(`${STATS_BASE}/api/v1/supplier/sales?dateFrom=${dateFrom}`, {
    headers: { Authorization: apiKey },
  });
  if (!res.ok) throw new Error(`sales request failed: ${res.status}`);
  const data = await res.json();
  if (!Array.isArray(data)) throw new Error("sales response was not an array");
  return data;
}

async function fetchAdsCampaignIds() {
  const res = await fetch(`${ADVERT_BASE}/adv/v1/promotion/count`, {
    headers: { Authorization: apiKey },
  });
  if (!res.ok) throw new Error(`campaign list request failed: ${res.status}`);
  const data = await res.json();
  const ids = [];
  const collect = (node) => {
    if (Array.isArray(node)) {
      node.forEach((item) => {
        if (item && typeof item === "object" && "advertId" in item) ids.push(item.advertId);
        else collect(item);
      });
    } else if (node && typeof node === "object") {
      Object.values(node).forEach(collect);
    }
  };
  collect(data);
  return ids;
}

async function fetchAdsStats(campaignIds, dates) {
  if (campaignIds.length === 0) return [];
  const res = await fetch(`${ADVERT_BASE}/adv/v2/fullstats`, {
    method: "POST",
    headers: { Authorization: apiKey, "Content-Type": "application/json" },
    body: JSON.stringify(campaignIds.map((id) => ({ id, dates }))),
  });
  if (!res.ok) throw new Error(`ads stats request failed: ${res.status}`);
  const data = await res.json();
  if (!Array.isArray(data)) throw new Error("ads stats response was not an array");
  return data;
}

async function main() {
  const dates = lastNDates(30);
  const byDate = new Map();
  const ensure = (date) => {
    let p = byDate.get(date);
    if (!p) {
      p = { date, salesAmount: 0, ordersCount: 0, adsSpend: 0, adsImpressions: 0, adsClicks: 0, adsOrders: 0 };
      byDate.set(date, p);
    }
    return p;
  };
  dates.forEach(ensure);

  const sales = await fetchSales(dates[0]);
  for (const sale of sales) {
    const date = sale.date.slice(0, 10);
    if (!byDate.has(date)) continue; // outside our 30-day window
    const point = ensure(date);
    point.salesAmount += sale.forPay;
    point.ordersCount += 1;
  }

  let adsAvailable = false;
  try {
    const campaignIds = await fetchAdsCampaignIds();
    const adsStats = await fetchAdsStats(campaignIds, dates);
    for (const campaign of adsStats) {
      for (const day of campaign.days ?? []) {
        const date = day.date.slice(0, 10);
        if (!byDate.has(date)) continue;
        const point = ensure(date);
        point.adsSpend += day.sum ?? 0;
        point.adsImpressions += day.views ?? 0;
        point.adsClicks += day.clicks ?? 0;
        point.adsOrders += day.orders ?? 0;
      }
    }
    adsAvailable = true;
  } catch (err) {
    console.error("ads unavailable:", err.message);
  }

  const points = dates.map((d) => byDate.get(d));
  const snapshot = {
    generatedAt: new Date().toISOString(),
    adsAvailable,
    points,
  };

  console.log("---SNAPSHOT_JSON_START---");
  console.log(JSON.stringify(snapshot));
  console.log("---SNAPSHOT_JSON_END---");
}

main().catch((err) => {
  console.error("Failed:", err.message);
  process.exit(1);
});
