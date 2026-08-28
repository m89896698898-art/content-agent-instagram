import { Router } from "express";
import { requireAuth, requireAdmin, AuthedRequest } from "../auth";
import { adapters, getCredentials, setCredentials } from "../marketplaces/registry";
import { Marketplace, Period } from "../marketplaces/types";

export const statsRouter = Router();

const MARKETPLACES: Marketplace[] = ["wildberries", "ozon"];
const PERIODS: Period[] = ["day", "week", "month"];

function parsePeriod(value: unknown): Period {
  return PERIODS.includes(value as Period) ? (value as Period) : "week";
}

function parseMarketplaces(value: unknown): Marketplace[] {
  if (value === "wildberries" || value === "ozon") return [value];
  return MARKETPLACES; // default: both
}

statsRouter.get("/", requireAuth, async (req, res) => {
  const period = parsePeriod(req.query.period);
  const marketplaces = parseMarketplaces(req.query.marketplace);

  const results = await Promise.all(
    marketplaces.map((mp) => adapters[mp].fetchStats(getCredentials(mp), period))
  );

  const configured = Object.fromEntries(
    MARKETPLACES.map((mp) => [mp, adapters[mp].isConfigured(getCredentials(mp))])
  );

  res.json({ period, stats: results, configured });
});

// Admin-only: view/set marketplace API credentials
statsRouter.get("/credentials", requireAuth, requireAdmin, (_req, res) => {
  const data = Object.fromEntries(
    MARKETPLACES.map((mp) => {
      const creds = getCredentials(mp);
      return [
        mp,
        {
          configured: adapters[mp].isConfigured(creds),
          apiKey: creds?.apiKey ? "••••••" + creds.apiKey.slice(-4) : null,
          clientId: creds?.clientId ?? null,
        },
      ];
    })
  );
  res.json(data);
});

statsRouter.put("/credentials/:marketplace", requireAuth, requireAdmin, (req: AuthedRequest, res) => {
  const marketplace = req.params.marketplace as Marketplace;
  if (!MARKETPLACES.includes(marketplace)) {
    return res.status(400).json({ error: "Unknown marketplace" });
  }
  const { apiKey, clientId } = req.body ?? {};
  if (!apiKey) {
    return res.status(400).json({ error: "apiKey is required" });
  }
  setCredentials(marketplace, { apiKey, clientId });
  res.json({ ok: true });
});
