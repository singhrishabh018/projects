# Content pipeline (n8n)

Implements PRD Section 10. Four workflows, in run order:

1. **`workflows/discovery.json`** -- daily, 6am. Pulls the active feed list from
   the app (`GET /api/pipeline/sources`), reads each RSS feed, keeps items from
   roughly the last day, and lands them in the app's `discovered_items` table
   (`POST /api/pipeline/discovered-items`) with `classificationStatus: pending`.
2. **`workflows/classification.json`** -- daily, 7am (after Discovery). Pulls
   pending items, asks an LLM to map each to the app's live taxonomy
   (`GET /api/pipeline/taxonomy`) and extract structured facts only --
   company, scale numbers, tech named -- never article prose. Confidence
   >= 0.6 writes a `real_world_examples` row and marks the item `classified`;
   below that, the item is marked `low-confidence` for the weekly Refresh pass
   to retry.
3. **`workflows/notification.json`** -- daily, 8am. Calls
   `POST /api/push/notify` so the PWA's service worker fires "today's topic is
   ready" (Section 10 step 4 -- push, not a chat-channel digest).
4. **`workflows/refresh.json`** -- weekly, Sunday 5am. Re-runs classification
   over anything still `pending` or `low-confidence`, so a source having a bad
   day doesn't permanently drop content on the floor.

## Why these call the app's API instead of writing SQLite directly

`data/app.db` is a local file the Next.js app owns; n8n runs as a separate
process/container. Every workflow reads/writes through small Next.js route
handlers under `src/app/api/pipeline/*` (guarded by a shared bearer token) --
this also gives the app one place to enforce "extraction, not authored prose"
regardless of which workflow or LLM prompt is calling in.

## Setup

1. **Bring up n8n:**

   ```bash
   cd n8n
   cp .env.example .env   # fill in the values below
   docker compose up -d
   ```

   Required env vars (`.env`):
   - `APP_BASE_URL` -- where the Next.js app is reachable from the n8n
     container (its Tailscale MagicDNS name if n8n and the app run on
     different machines, or `http://host.docker.internal:3000` if n8n runs in
     Docker on the same machine as `npm run dev`).
   - `PIPELINE_TOKEN` -- any random string; set the same value as
     `PIPELINE_TOKEN` in the app's `.env`.
   - `NOTIFY_TOKEN` -- same idea, matching the app's `NOTIFY_TOKEN`.
   - `ANTHROPIC_API_KEY` -- for the Classification/Refresh LLM step. Swap the
     `Classify (LLM)` node's URL/headers/body if you'd rather use a different
     provider; the JSON-only extraction contract is what matters, not the
     specific API.

2. **Import the four workflow files** in the n8n UI (`Workflows` -> `Import
   from File`), or via the CLI: `n8n import:workflow --input=./workflows`.
   Toggle each one active once imported.

3. **Seed the source list** (PRD Section 10 step 2 -- "seeded in bulk from the
   `kilimchoi/engineering-blogs` OPML file"):

   ```bash
   # From the app directory, with a normal (non-sandboxed) internet connection:
   # download the .opml file from https://github.com/kilimchoi/engineering-blogs
   npm run pipeline:import-opml -- /path/to/engineering-blogs.opml
   ```

   Every imported source defaults to `sourceType: "technical-newsletter"`.
   Re-tag the ones you know are `company-official` or `named-practitioner`
   (PRD Section 10's "source governance" rule) -- there's no admin UI for this
   yet, so it's a direct SQLite update against `data/app.db`'s `sources` table
   for now. Cursor (no traditional engineering blog) is exactly the kind of
   gap the PRD calls out filling via a vetted `technical-newsletter` source
   (e.g. Pragmatic Engineer) instead.

## What wasn't testable in this build

This was built in a sandboxed environment with no Docker daemon and heavily
restricted outbound network access (most hosts other than `github.com` and an
internal search index were egress-blocked). That means:

- These four workflow JSON files were validated for well-formed JSON and
  correct node/connection references, but **never actually imported into a
  running n8n instance or executed**. Import them and run each manually
  once before trusting the daily schedule.
- The `kilimchoi/engineering-blogs` OPML file could not be downloaded here,
  so `scripts/import-opml.ts` is written and ready but untested against the
  real file -- run it once and sanity-check a handful of the imported feed
  URLs actually resolve.
- The RSS feed URLs in that OPML file are a mix of native RSS, Medium
  (`/feed`), and Substack (`/feed`) endpoints; n8n's RSS Feed Read node
  handles all three natively, but a few entries may be dead links needing
  manual pruning from the `sources` table.
