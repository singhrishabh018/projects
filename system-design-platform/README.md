# System Design Loop

A visual, interactive, daily-habit version of
[`system-design-primer`](https://github.com/donnemartin/system-design-primer)
(CC BY 4.0), grounded in continuously-refreshed real production examples.
Built per the project PRD -- see "Design decisions vs. the PRD" below for the
handful of places this build had to make an honest call the PRD didn't fully
anticipate.

Single-user, local-first, never published (PRD Sections 2 & 12). No AI-written
or human-authored explanatory prose anywhere in the content: concept pages
reuse `system-design-primer`'s own CC BY 4.0 text/structure, real-world
examples are extracted structured facts that link out to their sources, and
quiz questions are sourced or honestly flagged as a gap.

## Stack

Next.js 16 (App Router) + TypeScript + Tailwind v4 + hand-rolled shadcn/ui-style
primitives, `@xyflow/react` for diagrams, Drizzle ORM + `better-sqlite3` (local
file, zero hosting), a hand-written service worker for PWA install + push
notifications, and an n8n content pipeline (see `n8n/README.md`).

## Getting started

```bash
npm install
npm run db:push    # creates data/app.db from src/db/schema.ts
npm run db:seed    # seeds the 3 pilot topics + real-world examples + quizzes
npm run dev
```

Open http://localhost:3000. Day 1 (Consistent Hashing) is unlocked
immediately; passing its quiz unlocks Rate Limiter the next calendar day, and
so on (PRD Section 7: "one topic unlocked per day").

Useful scripts:
- `npm run db:reset` -- wipe and reseed the local database.
- `npm run pipeline:import-opml -- /path/to/file.opml` -- bulk-seed RSS
  sources for the content pipeline (see `n8n/README.md`).

### Push notifications

```bash
npx web-push generate-vapid-keys
```

Put the keys in `.env` (see `.env.example`), restart `npm run dev`, then click
"Enable notifications" in the nav. `POST /api/push/notify` (bearer-token
protected via `NOTIFY_TOKEN`) is what the n8n Notification workflow calls
daily to fire "today's topic is ready."

### Phone access

Per PRD Section 11/12: run this app (and n8n) on a machine that's on when you
want phone access, and reach it over [Tailscale](https://tailscale.com) rather
than a public deployment -- Tailscale also covers the PWA's HTTPS requirement
via its built-in cert support. Picking that always-on machine is flagged in
the PRD (Section 13) as a decision to make in the first week, not something
this build can decide for you.

## Architecture

```
src/
  db/schema.ts, seed.ts     Topic, RealWorldExample, QuizQuestion,
                             InterviewFormatNote, UserProgress, Source,
                             DiscoveredItem (PRD Section 6 + pipeline support)
  lib/diagrams/*.ts         React Flow node/edge definitions per topic
  lib/progress.ts           daily-unlock + quiz-gate logic
  app/                      dashboard, topic pages, quiz, progress heatmap,
                             manifest.ts, and the API routes the n8n
                             pipeline + push notifications call into
n8n/                        4 importable workflow JSON files + docker-compose
scripts/import-opml.ts      bulk-seeds RSS sources from an OPML file
```

## Design decisions vs. the PRD

The PRD is detailed and mostly directly buildable, but a few things surfaced
during the build that are worth knowing about rather than papering over --
consistent with the project's own "sourced, not authored" ethos.

**Rate Limiter isn't actually written up in `system-design-primer`.** Section
8 frames it as an "in the primer" pilot; in reality the primer's README has no
Rate Limiter section at all -- it only appears as one link to Stripe's
engineering blog inside the "Additional interview questions" appendix table.
(Consistent Hashing fares slightly better: one real sentence, under
"Sharding.") The Rate Limiter topic page is built around that link plus a
mechanical diagram of the algorithms themselves (token bucket, sliding
window, etc. -- structural facts, not prose) and leans more heavily on its
Real-World Lessons feed, which is exactly where Section 8 says this pilot's
strength should be anyway.

**Quiz sourcing has an honest gap for two of the three pilots.** This sandbox
had no way to fetch and parse the primer's actual Anki `.apkg` deck, so
Consistent Hashing and Rate Limiter quiz questions are marked
`source: "UNSOURCED-gap"` in the schema and flagged with an amber badge in the
UI -- exactly the escape hatch the PRD's own data model (Section 6) built in
for this. They're still real, single-fact recall questions grounded in the
undisputed mechanics of each algorithm, not fabricated trivia. RAG's quiz
*is* properly sourced, from Exponent's published AI-engineer interview guide
(Section 9's suggested fallback), with a `cached-interview-guide` source tag
distinct from a true CC-licensed deck.

**"Cache full article text locally" (Section 9) isn't implemented as literal
full-text caching.** This build environment's outbound network only reaches
github.com and an internal search index -- no general web fetching. Every
`RealWorldExample.cachedExcerpt` holds a real short excerpt from that search
index (attributed, quoted) rather than a full-page scrape, and every example
still links to its original source. Full local caching needs the actual n8n +
Firecrawl pipeline (Section 10) running with normal network access, which is
what `n8n/workflows/discovery.json` and `classification.json` are built for --
they were authored and JSON-validated here but never run against a live n8n
instance (no Docker daemon in this sandbox either). Import and test them
before trusting the daily schedule.

**Quiz grading is self-graded, Anki-style**, not exact-text matching: reveal
the answer, honestly mark "got it" / "missed it," >=70% passes. The PRD
doesn't specify a grading mechanism, and free-text answer matching for
system-design questions is a worse experience than the primer's own Anki deck
uses.

## What's genuinely done vs. deferred

Done: 3 pilot topics end-to-end (concept page, diagram, real-world feed,
interview notes where applicable, quiz gate), daily-unlock loop, confidence
heatmap, installable PWA with a working push-notification round trip (subscribe
-> service worker -> notification), and 4 n8n pipeline workflows + bulk source
importer.

Deferred, per the PRD itself: AI tutor (Section 7, explicitly out of v1),
incident-response mode and capacity-math widget (Section 7 "should have,"
post-pilot), frontend system design / broader case studies (Section 5, later
track), and an admin UI for retagging pipeline sources (Section 10's source
governance is enforced by the schema/API today, applied by hand for now).
