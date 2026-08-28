export type Role = "admin" | "employee";
export type Marketplace = "wildberries" | "ozon";
export type Period = "day" | "week" | "month";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface DailyPoint {
  date: string;
  salesAmount: number;
  ordersCount: number;
  adsSpend: number;
  adsImpressions: number;
  adsClicks: number;
  adsOrders: number;
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
    drr: number;
  };
}

export interface StatsResponse {
  period: Period;
  stats: MarketplaceStats[];
  configured: Record<Marketplace, boolean>;
}
