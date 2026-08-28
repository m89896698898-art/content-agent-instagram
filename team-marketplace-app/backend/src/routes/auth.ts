import { Router } from "express";
import bcrypt from "bcryptjs";
import { db, UserRow } from "../db";
import { signToken, requireAuth, AuthedRequest } from "../auth";

export const authRouter = Router();

authRouter.post("/register", async (req, res) => {
  const { email, password, name } = req.body ?? {};
  if (!email || !password || !name) {
    return res.status(400).json({ error: "email, password, name are required" });
  }

  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) {
    return res.status(409).json({ error: "Email already registered" });
  }

  const userCount = (db.prepare("SELECT COUNT(*) as c FROM users").get() as { c: number }).c;
  const role = userCount === 0 ? "admin" : "employee";

  const passwordHash = await bcrypt.hash(password, 10);
  const info = db
    .prepare("INSERT INTO users (email, passwordHash, name, role) VALUES (?, ?, ?, ?)")
    .run(email, passwordHash, name, role);

  const token = signToken({ userId: Number(info.lastInsertRowid), role });
  res.status(201).json({ token, user: { id: info.lastInsertRowid, email, name, role } });
});

authRouter.post("/login", async (req, res) => {
  const { email, password } = req.body ?? {};
  if (!email || !password) {
    return res.status(400).json({ error: "email and password are required" });
  }

  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email) as UserRow | undefined;
  if (!user) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const valid = await bcrypt.compare(password, user.passwordHash);
  if (!valid) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  const token = signToken({ userId: user.id, role: user.role });
  res.json({ token, user: { id: user.id, email: user.email, name: user.name, role: user.role } });
});

authRouter.get("/me", requireAuth, (req: AuthedRequest, res) => {
  const user = db.prepare("SELECT id, email, name, role FROM users WHERE id = ?").get(req.user!.userId);
  if (!user) return res.status(404).json({ error: "User not found" });
  res.json({ user });
});
