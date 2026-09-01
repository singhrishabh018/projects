/**
 * Bulk-seeds the `sources` table from kilimchoi/engineering-blogs' OPML file
 * (PRD Section 10, step 2). That repo isn't reachable from this sandbox's
 * network (github raw content and most third-party hosts are egress-blocked
 * here), so this script takes a LOCAL OPML file path instead of fetching one
 * -- download it yourself from
 * https://github.com/kilimchoi/engineering-blogs (look for the .opml file in
 * the repo) on a machine with normal internet access, then run:
 *
 *   npx tsx scripts/import-opml.ts /path/to/engineering-blogs.opml
 *
 * Every imported feed defaults to sourceType "technical-newsletter" and
 * active=true -- re-tag company-official / named-practitioner sources
 * afterward (e.g. via a small SQL update or a future admin UI); this script
 * intentionally does not guess that classification from the feed title.
 */
import fs from "node:fs";
import { db } from "../src/db";
import { sources } from "../src/db/schema";
import { eq } from "drizzle-orm";

function extractOutlines(xml: string): { title: string; xmlUrl: string }[] {
  const results: { title: string; xmlUrl: string }[] = [];
  const outlineRe = /<outline\b[^>]*>/gi;
  let match: RegExpExecArray | null;
  while ((match = outlineRe.exec(xml))) {
    const tag = match[0];
    const xmlUrlMatch = tag.match(/xmlUrl="([^"]+)"/i);
    if (!xmlUrlMatch) continue;
    const titleMatch = tag.match(/(?:title|text)="([^"]+)"/i);
    results.push({
      title: titleMatch ? decodeEntities(titleMatch[1]) : xmlUrlMatch[1],
      xmlUrl: decodeEntities(xmlUrlMatch[1]),
    });
  }
  return results;
}

function decodeEntities(s: string) {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

async function main() {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error("Usage: npx tsx scripts/import-opml.ts /path/to/engineering-blogs.opml");
    process.exit(1);
  }
  const xml = fs.readFileSync(filePath, "utf-8");
  const outlines = extractOutlines(xml);
  console.log(`Found ${outlines.length} feed entries.`);

  let inserted = 0;
  for (const o of outlines) {
    const existing = await db.select().from(sources).where(eq(sources.feedUrl, o.xmlUrl));
    if (existing.length > 0) continue;
    await db.insert(sources).values({
      id: crypto.randomUUID(),
      feedUrl: o.xmlUrl,
      name: o.title,
      sourceType: "technical-newsletter",
      active: true,
      addedFrom: "opml-bulk",
    });
    inserted++;
  }
  console.log(`Inserted ${inserted} new sources (${outlines.length - inserted} already present).`);
}

main().then(() => process.exit(0));
