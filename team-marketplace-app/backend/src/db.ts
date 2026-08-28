import Database from "better-sqlite3";
import path from "path";

const dbPath = path.join(__dirname, "..", "data.sqlite");
export const db = new Database(dbPath);

db.pragma("journal_mode = WAL");

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    passwordHash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'employee')) DEFAULT 'employee',
    createdAt TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS marketplace_credentials (
    marketplace TEXT PRIMARY KEY CHECK (marketplace IN ('wildberries', 'ozon')),
    apiKey TEXT,
    clientId TEXT,
    updatedAt TEXT NOT NULL DEFAULT (datetime('now'))
  );
`);

export type Role = "admin" | "employee";

export interface UserRow {
  id: number;
  email: string;
  passwordHash: string;
  name: string;
  role: Role;
  createdAt: string;
}
