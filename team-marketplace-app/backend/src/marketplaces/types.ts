export type Marketplace = "wildberries" | "ozon";
export type Period = "day" | "week" | "month";

export interface DailyPoint {
  date: string; // YYYY-MM-DD
  salesAmount: number; // revenue in RUB
  ordersCount: number;
  adsSpend: number; // RUB spent on ads
  adsImpressions: number;
  adsClicks: number;
  adsOrders: number; // orders attributed to ads
}

export interface MarketplaceStats {
  marketplace: Marketplace;
  period: Period;
  points: DailyPoint[];
  totals: {
    salesAmount: number;
    ordersCount: number;
    adsSpend: number;
    adsImpressions: number;
    adsClicks: number;
    adsOrders: number;
    drr: number; // ad spend / sales, %
  };
}

export interface MarketplaceAdapter {
  readonly marketplace: Marketplace;
  isConfigured(credentials: MarketplaceCredentials | undefined): boolean;
  fetchStats(
    credentials: MarketplaceCredentials | undefined,
    period: Period
  ): Promise<MarketplaceStats>;
}

export interface MarketplaceCredentials {
  apiKey?: string;
  clientId?: string; // Ozon requires Client-Id + Api-Key
}
