import { db } from "@/db";
import { pushSubscriptions } from "@/db/schema";
import { eq } from "drizzle-orm";

export async function POST(request: Request) {
  const sub = await request.json();
  if (!sub?.endpoint || !sub?.keys?.p256dh || !sub?.keys?.auth) {
    return Response.json({ error: "Invalid subscription" }, { status: 400 });
  }

  const existing = await db
    .select()
    .from(pushSubscriptions)
    .where(eq(pushSubscriptions.endpoint, sub.endpoint));

  if (existing.length === 0) {
    await db.insert(pushSubscriptions).values({
      id: crypto.randomUUID(),
      endpoint: sub.endpoint,
      p256dh: sub.keys.p256dh,
      auth: sub.keys.auth,
      createdAt: new Date().toISOString(),
    });
  }

  return Response.json({ ok: true });
}
