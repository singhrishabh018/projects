import { db } from "@/db";
import { pushSubscriptions } from "@/db/schema";
import { ensureWebPushConfigured, webpush } from "@/lib/web-push";

/**
 * PRD Section 10 step 4: push a "today's topic is ready" notification.
 * Designed to be called by n8n's Notification workflow (see n8n/README.md)
 * via a shared bearer token, or manually for testing.
 */
export async function POST(request: Request) {
  const token = request.headers.get("authorization")?.replace("Bearer ", "");
  if (process.env.NOTIFY_TOKEN && token !== process.env.NOTIFY_TOKEN) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!ensureWebPushConfigured()) {
    return Response.json(
      { error: "VAPID keys not configured. Run `npx web-push generate-vapid-keys` and set VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY." },
      { status: 500 },
    );
  }

  const body = await request.json().catch(() => ({}));
  const title = body.title || "System Design Loop";
  const message = body.body || "Today's topic is ready.";
  const url = body.url || "/";

  const subs = await db.select().from(pushSubscriptions);
  const results = await Promise.allSettled(
    subs.map((sub) =>
      webpush.sendNotification(
        { endpoint: sub.endpoint, keys: { p256dh: sub.p256dh, auth: sub.auth } },
        JSON.stringify({ title, body: message, url }),
      ),
    ),
  );

  return Response.json({
    sent: results.filter((r) => r.status === "fulfilled").length,
    failed: results.filter((r) => r.status === "rejected").length,
  });
}
