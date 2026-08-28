import { MarketplaceAdapter, MarketplaceCredentials, MarketplaceStats, Period } from "./types";
import { generateMockStats } from "./mockData";

// Real integration notes (fill in once API access is granted):
// - Sales: Ozon Seller API, POST https://api-seller.ozon.ru/v3/finance/transaction/list
// - Ads: Ozon Performance API, POST https://performance.ozon.ru/api/client/statistics
// - Auth: requires both `Client-Id` and `Api-Key` headers from the Ozon seller cabinet
export const ozonAdapter: MarketplaceAdapter = {
  marketplace: "ozon",

  isConfigured(credentials: MarketplaceCredentials | undefined): boolean {
    return Boolean(credentials?.apiKey && credentials?.clientId);
  },

  async fetchStats(credentials: MarketplaceCredentials | undefined, period: Period): Promise<MarketplaceStats> {
    if (!this.isConfigured(credentials)) {
      // No API key/Client-Id on file yet -> serve mock data so the app stays usable.
      return generateMockStats("ozon", period);
    }

    // TODO: replace with real calls to api-seller.ozon.ru / performance.ozon.ru
    // using credentials.clientId + credentials.apiKey, then map the response into MarketplaceStats.
    return generateMockStats("ozon", period);
  },
};
