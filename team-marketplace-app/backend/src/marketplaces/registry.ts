import { db } from "../db";
import { Marketplace, MarketplaceAdapter, MarketplaceCredentials } from "./types";
import { wildberriesAdapter } from "./wildberries";
import { ozonAdapter } from "./ozon";

export const adapters: Record<Marketplace, MarketplaceAdapter> = {
  wildberries: wildberriesAdapter,
  ozon: ozonAdapter,
};

interface CredentialsRow {
  marketplace: Marketplace;
  apiKey: string | null;
  clientId: string | null;
}

export function getCredentials(marketplace: Marketplace): MarketplaceCredentials | undefined {
  const row = db
    .prepare("SELECT marketplace, apiKey, clientId FROM marketplace_credentials WHERE marketplace = ?")
    .get(marketplace) as CredentialsRow | undefined;
  if (!row) return undefined;
  return { apiKey: row.apiKey ?? undefined, clientId: row.clientId ?? undefined };
}

export function setCredentials(marketplace: Marketplace, credentials: MarketplaceCredentials): void {
  db.prepare(
    `INSERT INTO marketplace_credentials (marketplace, apiKey, clientId, updatedAt)
     VALUES (?, ?, ?, datetime('now'))
     ON CONFLICT(marketplace) DO UPDATE SET apiKey = excluded.apiKey, clientId = excluded.clientId, updatedAt = excluded.updatedAt`
  ).run(marketplace, credentials.apiKey ?? null, credentials.clientId ?? null);
}
