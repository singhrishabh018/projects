import { db } from "@/db";
import { discoveredItems } from "@/db/schema";
import { eq } from "drizzle-orm";
import { checkPipelineAuth } from "@/lib/pipeline-auth";

/** Classification marks an item resolved after it either writes a real-world example or gives up on it. */
export async function PATCH(request: Request, ctx: RouteContext<"/api/pipeline/discovered-items/[id]">) {
  if (!checkPipelineAuth(request)) return Response.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await ctx.params;
  const { classificationStatus } = await request.json();
  if (!["pending", "classified", "low-confidence", "irrelevant"].includes(classificationStatus)) {
    return Response.json({ error: "Invalid status" }, { status: 400 });
  }

  await db.update(discoveredItems).set({ classificationStatus }).where(eq(discoveredItems.id, id));
  return Response.json({ ok: true });
}
