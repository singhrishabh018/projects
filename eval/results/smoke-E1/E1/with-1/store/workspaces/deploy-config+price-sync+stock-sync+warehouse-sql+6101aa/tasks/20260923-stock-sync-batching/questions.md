# Questions — stock-sync batching

## Q1 (for the partner, via the account manager) — 25 items per call and 15 minutes cannot both hold

Context: ticket 131 asks for batches of at least 25 items, and for stock to arrive within 15
minutes of a change.

**Can the partner accept batches smaller than 25 items when that is all the stock that
changed in the window — or would they rather we hold items and miss the 15-minute window?**

Why it matters: we send about 6,000 stock changes a day, and production runs eight
independent workers. In a 15-minute window one worker sees roughly 13 changes at peak and
about one overnight. Waiting for 25 items would mean holding stock updates for around 28
minutes at peak and several hours overnight — exactly the wrong-availability problem they
want to avoid. There is no arrangement of our side that satisfies both numbers at this
volume.

My recommendation: send whatever has accumulated when the timer expires, capped at 500. This
is what I have built. It still removes ~90% of their request volume and eliminates the
one-item calls that are hitting their rate limit, and it never misses the 15-minute promise.

1. You know the answer → tell me (or say "go with your recommendation").
2. You have access → ask on the existing thread with the partner's integration team; the
   forwarded note of 2026-09-10 in ticket 131 is the thread to reply to.
3. You know who would know → send the account manager (ticket 131's author):

   > On the batching request: we can batch, and it will cut our request volume by roughly
   > 90% and remove the single-item calls that are tripping your rate limits. But at our
   > volume we can't hit 25 items per call *and* the 15-minute freshness window — in 15
   > minutes one of our eight workers sees about 13 stock changes at peak and about one
   > overnight. Our plan is to send whatever has accumulated when the 15-minute clock runs
   > out (capped at 500 per call), so batches will often be smaller than 25. Can you confirm
   > that's acceptable, or would you prefer we prioritise the 25-item minimum and accept
   > later updates?

4. None of these → the code ships as built (deadline wins, best-effort 25) and the partner
   keeps receiving sub-25 batches. Reversible: `BATCH_TARGET_ITEMS` and
   `BATCH_MAX_AGE_SECONDS` are environment variables, so the trade-off can be re-tuned
   without a code change.

**No-answer default:** safely reversible and flagged.

## Q2 (for whoever owns the broker client) — can the consumer wake up while idle?

Context: `stock_sync/consumer.py` receives its broker client by injection; that client is not
in any repo in this workspace, so I could not read what it supports.

**Does the broker client we inject in production offer a poll with a timeout — a call that
returns `None` after N seconds when no message is waiting — or only the blocking
`subscribe()` iterator?**

Why it matters: the timed flush is what keeps the 15-minute promise. With only a blocking
iterator, a worker holding three items overnight would not wake up until the next event
arrived, which could be an hour later — worse than not batching at all. The code therefore
checks for `poll` at startup and, if it is missing, logs an error and sends unbatched.
Batching switches itself on as soon as a client with `poll` is injected; nothing else changes.

My recommendation: confirm the method name and signature before rollout. If the client has a
poll under a different name, it is a one-line change in `stock_sync/broker.py:14-25`.

1. You know the answer → tell me the method name and signature.
2. You have access → in the repo that builds the client injected into `consumer.run()`, run
   `grep -rn "def poll\|def subscribe" .` and paste the matching lines.
3. You know who would know → send the service owner:

   > Quick one for stock-sync batching: does our broker client expose a poll with a timeout
   > (returns None when nothing is waiting), or only the blocking subscribe() iterator? I
   > need a way for the consumer loop to regain control while idle so a part-full batch can
   > be flushed on a timer. If there's no such call, stock-sync will keep sending unbatched
   > until there is.

4. None of these → stock-sync ships with batching code in place but running unbatched in any
   environment whose client lacks `poll`; everything else in this change is unaffected.

**No-answer default:** safely reversible and flagged (fails to today's behaviour, visible as
an ERROR log line at startup).
