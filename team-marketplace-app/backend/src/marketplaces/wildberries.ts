import { MarketplaceAdapter, MarketplaceCredentials, MarketplaceStats, Period } from "./types";
import { generateMockStats } from "./mockData";
import { fetchWildberriesDailyPoints } from "./wbApi";

function summarize(points: MarketplaceStats["points"]) {
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
  return { ...totals, drr };
}

// Real integration:
// - Sales: WB Statistics API, GET https://statistics-api.wildberries.ru/api/v1/supplier/sales
// - Ads: WB Advert API, GET /adv/v1/promotion/count + POST /adv/v2/fullstats
// - Auth: single API key from the WB seller cabinet, sent as header `Authorization: <token>`
// See wbApi.ts for the actual requests. This integration was written against
// WB's documented API shape but has NOT been tested against a live response
// (this environment's network policy blocks statistics-api.wildberries.ru) —
// verify it once you run the backend somewhere with real internet access.
export const wildberriesAdapter: MarketplaceAdapter = {
  marketplace: "wildberries",

  isConfigured(credentials: MarketplaceCredentials | undefined): boolean {
    return Boolean(credentials?.apiKey);
  },

  async fetchStats(credentials: MarketplaceCredentials | undefined, period: Period): Promise<MarketplaceStats> {
    if (!this.isConfigured(credentials)) {
      return generateMockStats("wildberries", period);
    }

    try {
      const points = await fetchWildberriesDailyPoints(credentials!.apiKey!, period);
      return { marketplace: "wildberries", period, points, totals: summarize(points) };
    } catch (err) {
      // If the live API call fails (bad token, API shape changed, network
      // issue) fall back to mock data rather than breaking the dashboard,
      // and log so it's easy to notice and debug.
      console.error("[wildberries] live fetch failed, falling back to mock data:", err);
      return generateMockStats("wildberries", period);
    }
  },
};
