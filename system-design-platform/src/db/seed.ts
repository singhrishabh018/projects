/**
 * One-time primer + pilot-topic ingestion (PRD Section 10, step 1).
 *
 * Sourcing honesty notes (read before editing):
 * - system-design-primer's README has NO standalone "Consistent Hashing" or
 *   "Rate Limiter" section. Consistent hashing gets one sentence inside
 *   "Sharding" (used here, quoted). Rate limiting appears only as a link to
 *   Stripe's blog in the interview-questions appendix, not as primer prose.
 *   conceptFacts below is written as short mechanical/structural labels (ring
 *   position, algorithm parameters), not authored explanatory prose, and
 *   contentNote says exactly what is/isn't primer text. This is a real gap
 *   against the PRD's Section 8 framing ("in the primer") worth knowing about.
 * - This sandbox's outbound network only reaches github.com and the Firecrawl
 *   search index (no general web fetch/scrape). So `cachedExcerpt` below holds
 *   the real short excerpt Firecrawl's search index returned for each source
 *   -- not a full-text local cache. Section 9's "cache full article text
 *   locally" requires the real n8n + Firecrawl scrape pipeline (Section 10)
 *   running with unrestricted network access, which this build environment
 *   does not have. Every example still links to its real, verifiable source.
 * - Quiz questions: this session has no access to the primer's actual Anki
 *   deck (.apkg, not fetchable here), so consistent-hashing/rate-limiter
 *   questions are honestly marked source: 'UNSOURCED-gap' rather than
 *   mislabeled as primer-anki-deck. The RAG pilot's questions are sourced
 *   from Exponent's published AI-engineer interview guide (real Q&A pairs,
 *   cached per Section 9's local-caching allowance), marked
 *   'cached-interview-guide'.
 */
import { db } from "./index";
import { topics, realWorldExamples, quizQuestions, interviewFormatNotes, userProgress } from "./schema";

async function seed() {
  await db.insert(topics).values([
    {
      id: "consistent-hashing",
      title: "Consistent Hashing",
      source: "primer",
      primerSectionUrl:
        "https://github.com/donnemartin/system-design-primer#sharding",
      contentNote:
        "The primer covers this in one line under \"Sharding\": \"A sharding function based on consistent hashing can reduce the amount of data transferred when a node is added or removed.\" There is no dedicated primer write-up beyond that sentence -- the diagram and structural facts below are a mechanical rendering of the algorithm itself, not primer prose.",
      conceptFacts: [
        "Primer quote (Sharding): \"Rebalancing adds additional complexity. A sharding function based on consistent hashing can reduce the amount of data transferred when a node is added or removed.\"",
        "Nodes and keys are hashed onto the same ring (typically 0 to 2^32-1)",
        "A key is owned by the first node reached walking clockwise from the key's hash position",
        "Each physical server is assigned multiple virtual nodes on the ring to smooth out uneven load",
        "Adding/removing one node only remaps the keys between it and its ring neighbors -- not the whole keyspace",
        "Used in practice for: sharded caches, DynamoDB-style key-value stores, and process/PID distribution (see Discord example below)",
      ],
      conceptDiagramKey: "consistent-hashing-ring",
      difficulty: "intermediate",
      relatedCompanies: ["Amazon (DynamoDB)", "Discord", "Cassandra", "Akamai"],
      order: 1,
    },
    {
      id: "rate-limiter",
      title: "Rate Limiter",
      source: "primer",
      primerSectionUrl:
        "https://github.com/donnemartin/system-design-primer#additional-system-design-interview-questions",
      contentNote:
        "The primer itself doesn't write up rate limiting -- it appears only as a linked interview question (\"Design an API rate limiter\") pointing to Stripe's engineering blog in the appendix table. This topic leans on that linked source plus the Real-World Lessons feed rather than primer prose that doesn't exist.",
      conceptFacts: [
        "Primer's own coverage is a single appendix link: \"Design an API rate limiter\" -> Stripe's rate-limiters blog post",
        "Token bucket: bucket holds up to N tokens, refills at R tokens/sec, each request consumes 1 token",
        "Sliding window log/counter: tracks request timestamps in a moving window instead of a fixed reset boundary",
        "Fixed window counter: simplest, but allows up to 2x burst at window boundaries",
        "Leaky bucket: requests processed at a constant outflow rate regardless of burst inflow",
        "Distributed enforcement needs a shared, atomically-updated counter store (e.g. Redis INCR + EXPIRE, or Redis+Lua for atomicity)",
        "Standard response contract: 429 Too Many Requests with a Retry-After header; soft limits surface via X-RateLimit-* headers",
      ],
      conceptDiagramKey: "rate-limiter-flow",
      difficulty: "intermediate",
      relatedCompanies: ["Stripe", "Cloudflare"],
      order: 2,
    },
    {
      id: "rag-pipeline-design",
      title: "RAG Pipeline Design",
      source: "curated-exception",
      primerSectionUrl: null,
      contentNote:
        "Not in system-design-primer at all -- kept in v1 scope per PRD Section 5 as a deliberate, flagged override because it's core to the AI-engineering career track driving this project. Sourced the same way as everything else: structured facts + links, plus a cached published interview guide for the quiz (see Section 9).",
      conceptFacts: [
        "Ingest: chunk source documents (fixed-size or semantic) and embed each chunk into a vector store with metadata",
        "Retrieve: embed the incoming query, run similarity search for the top-k chunks (hybrid keyword+vector search optional)",
        "Augment: insert retrieved chunks into the prompt with an instruction to answer only from provided context",
        "Generate: produce the answer, ideally with citations back to source chunks",
        "Key interview tradeoff: chunk size -- small chunks retrieve precisely but lose surrounding context; large chunks do the reverse",
        "Retrieval and generation are evaluated separately: retrieval quality (did we surface the right chunk?) vs. answer/decision quality",
        "Cost controls seen in production: cache embeddings, keep top-k tight, route easy queries to a cheaper/smaller model, cap tokens per call",
        "Agentic RAG adds: tool use/function calling, guardrails (confidence/cost thresholds, human fallback), and observability/tracing",
      ],
      conceptDiagramKey: "rag-pipeline-flow",
      difficulty: "advanced",
      relatedCompanies: ["Uber", "DoorDash", "Sierra", "Scale AI"],
      order: 3,
    },
  ]);

  await db.insert(realWorldExamples).values([
    {
      id: "ex-cloudflare-nov2025",
      topicIds: ["rate-limiter"],
      title: "Cloudflare outage on November 18, 2025",
      sourceName: "Cloudflare Blog",
      sourceType: "company-official",
      sourceUrl: "https://blog.cloudflare.com/18-november-2025-outage/",
      extractedFacts: {
        company: "Cloudflare",
        scaleNumbers: ["Global outage, Nov 18, 2025", "Config regenerated on a 5-minute cycle"],
        techNamed: ["Bot Management feature file", "ClickHouse (query underpinning feature generation)"],
        facts: [
          "Outage traced to a bot-management configuration/feature file that grew past an internal size limit",
          "Cloudflare published a detailed public postmortem within hours (widely noted as unusually transparent)",
          "Independently covered by Pragmatic Engineer's \"The Pulse\" as a case study in incident-response transparency",
        ],
      },
      cachedExcerpt:
        "\"Normally this should be very low, and it was right up until the start of the outage. As a result, every five minutes there was a chance of either a good or a bad set of configuration files being generated and rapidly propagated across the network.\" -- blog.cloudflare.com/18-november-2025-outage/ (short excerpt via search index; full article not locally cached in this build, see seed.ts header)",
      publishedDate: "2025-11-18",
    },
    {
      id: "ex-stripe-rate-limiters",
      topicIds: ["rate-limiter"],
      title: "Scaling your API with rate limiters",
      sourceName: "Stripe Engineering Blog",
      sourceType: "company-official",
      sourceUrl: "https://stripe.com/blog/rate-limiters",
      extractedFacts: {
        company: "Stripe",
        scaleNumbers: [],
        techNamed: ["Request rate limiter", "Concurrent-requests limiter", "GCRA / token-bucket style algorithm", "Redis"],
        facts: [
          "Stripe layers multiple limiter types rather than a single global limit (per API key, per endpoint tiers)",
          "Enforced close to the edge of the request path so rejected requests cost minimal backend work",
        ],
      },
      cachedExcerpt:
        "\"At Stripe, we've found that carefully implementing a few rate limiting strategies helps keep the API available for everyone.\" -- stripe.com/blog/rate-limiters (short excerpt via search index)",
      publishedDate: null,
    },
    {
      id: "ex-stripe-webhooks",
      topicIds: ["rate-limiter"],
      title: "Stay within limits: API rate-limit-friendly pattern for Stripe webhooks",
      sourceName: "Stripe Developer Blog",
      sourceType: "company-official",
      sourceUrl: "https://stripe.dev/blog/stay-within-limits-api-rate-limit-friendly-pattern-for-stripe-webhooks",
      extractedFacts: {
        company: "Stripe",
        scaleNumbers: [],
        techNamed: ["Webhooks", "Idempotency keys"],
        facts: ["Addresses rate-limit-safe patterns specifically for webhook delivery/consumption at scale"],
      },
      cachedExcerpt:
        "\"At scale, these problems aren't just possibilities - they're guarantees.\" -- stripe.dev (short excerpt via search index)",
      publishedDate: null,
    },
    {
      id: "ex-discord-elixir",
      topicIds: ["consistent-hashing"],
      title: "How Discord Scaled Elixir to 5,000,000 Concurrent Users",
      sourceName: "Discord Engineering Blog",
      sourceType: "company-official",
      sourceUrl: "https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users",
      extractedFacts: {
        company: "Discord",
        scaleNumbers: ["5,000,000 concurrent users"],
        techNamed: ["Elixir", "Erlang", ":erlang.phash2/2", "Manifold (message fanout)"],
        facts: [
          "Message fanout: a partitioner consistently hashes process PIDs using :erlang.phash2/2",
          "Hashed PIDs are grouped by number of CPU cores and routed to child worker processes",
        ],
      },
      cachedExcerpt:
        "\"The partitioner then consistently hashes the PIDs using :erlang.phash2/2, groups them by number of cores, and sends them to child workers.\" -- discord.com/blog (short excerpt via search index)",
      publishedDate: null,
    },
    {
      id: "ex-uber-genie-rag",
      topicIds: ["rag-pipeline-design"],
      title: "Enhanced Agentic RAG for Uber's internal on-call copilot (\"Genie\")",
      sourceName: "ZenML LLMOps Database (aggregating Uber Engineering)",
      sourceType: "technical-newsletter",
      sourceUrl: "https://www.zenml.io/llmops-database/enhanced-agentic-rag-for-internal-on-call-support-copilot",
      extractedFacts: {
        company: "Uber",
        scaleNumbers: ["+27% relative increase in acceptable answers", "-60% relative reduction in incorrect advice"],
        techNamed: ["Genie (on-call copilot)", "Enhanced Agentic RAG (EAg-RAG)", "Custom Google Docs loaders"],
        facts: [
          "Moved from traditional RAG to an agentic RAG architecture with pre/post-processing steps for query optimization and source identification",
          "Applied to the engineering security & privacy on-call support domain",
        ],
      },
      cachedExcerpt:
        "\"...resulted in a 27% relative increase in acceptable answers and a 60% relative reduction in incorrect advice, enabling production deployment and reducing subject matter expert support load.\" -- zenml.io LLMOps database entry (short excerpt via search index; aggregator, not Uber's own blog -- link out for the primary account)",
      publishedDate: null,
    },
    {
      id: "ex-doordash-hrag",
      topicIds: ["rag-pipeline-design"],
      title: "Bridging behavioral silos in multi-vertical recommendations with a hierarchical RAG pipeline",
      sourceName: "ZenML LLMOps Database (aggregating DoorDash Engineering)",
      sourceType: "technical-newsletter",
      sourceUrl: "https://www.zenml.io/llmops-database/bridging-behavioral-silos-in-multi-vertical-recommendations-with-llms",
      extractedFacts: {
        company: "DoorDash",
        scaleNumbers: ["+4-5% relative improvement in AUC-ROC and MRR (offline and online)"],
        techNamed: ["Hierarchical RAG (H-RAG)", "Multi-task ranking models"],
        facts: [
          "Translates user behavior from data-rich verticals into cross-vertical semantic affinity features via an LLM-powered H-RAG pipeline",
          "Particularly benefited cold-start users while maintaining cost efficiency via model selection and prompt optimization",
        ],
      },
      cachedExcerpt:
        "\"...delivered approximately 4-5% relative improvements in AUC-ROC and MRR both offline and online, particularly benefiting cold-start users, while maintaining cost efficiency...\" -- zenml.io LLMOps database entry (short excerpt via search index; aggregator, link out for DoorDash's own account)",
      publishedDate: null,
    },
  ]);

  await db.insert(quizQuestions).values([
    // Consistent Hashing -- UNSOURCED-gap: this sandbox has no path to the
    // primer's real Anki deck (.apkg isn't network-fetchable here). Written as
    // single-fact recall questions grounded in the mechanism itself, flagged
    // honestly rather than mislabeled as primer-anki-deck.
    {
      id: "q-ch-1",
      topicId: "consistent-hashing",
      question: "In consistent hashing, when a node is added to the ring, roughly what fraction of keys need to move?",
      answer: "Only the keys between the new node and its counter-clockwise neighbor -- not the whole keyspace (ideally ~1/N of keys for N nodes).",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    {
      id: "q-ch-2",
      topicId: "consistent-hashing",
      question: "Why does consistent hashing use virtual nodes instead of mapping each physical server to one ring position?",
      answer: "One position per server can create very uneven load distribution; multiple virtual nodes per server spread its share of the keyspace more evenly across the ring.",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    {
      id: "q-ch-3",
      topicId: "consistent-hashing",
      question: "Given a key's hash position on the ring, which node owns that key?",
      answer: "The first node encountered walking clockwise from the key's hash position.",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    // Rate Limiter -- same gap, same honesty.
    {
      id: "q-rl-1",
      topicId: "rate-limiter",
      question: "What's the main weakness of a fixed-window counter rate limiter?",
      answer: "It can allow up to ~2x the intended limit in a short burst that straddles the window boundary (e.g. end of one window + start of the next).",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    {
      id: "q-rl-2",
      topicId: "rate-limiter",
      question: "In a token-bucket limiter, what two parameters define its behavior?",
      answer: "Bucket capacity (max burst size) and refill rate (steady-state throughput allowed).",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    {
      id: "q-rl-3",
      topicId: "rate-limiter",
      question: "What HTTP status code and header does a well-behaved rate limiter return when it rejects a request?",
      answer: "429 Too Many Requests, with a Retry-After header telling the client when to try again.",
      source: "UNSOURCED-gap",
      sourceUrl: null,
    },
    // RAG Pipeline -- sourced from Exponent's published AI-engineer interview
    // guide (cached per Section 9's local-caching allowance for personal use).
    {
      id: "q-rag-1",
      topicId: "rag-pipeline-design",
      question: "Explain how RAG works.",
      answer:
        "Four stages: (1) ingest source documents by chunking and embedding each chunk into a vector store; (2) retrieve by embedding the query and running similarity search for the top-k chunks; (3) augment the prompt by inserting those chunks with instructions to answer only from context; (4) generate the answer, ideally with citations. Used over fine-tuning for freshness -- update knowledge by re-indexing, not retraining. Retrieval and generation should be evaluated and debugged separately, since they fail independently.",
      source: "cached-interview-guide",
      sourceUrl: "https://www.tryexponent.com/questions/5877/explain-rag",
    },
    {
      id: "q-rag-2",
      topicId: "rag-pipeline-design",
      question: "Design an insurance-claims agent that ingests claims and outputs an approval decision using RAG, while controlling LLM/token cost. (Asked at Scale AI)",
      answer:
        "Scope inputs (claim + supporting docs) and output (approve/deny/escalate + reason). Pipeline: index policy docs and claim history into a vector store; retrieve relevant policy clauses per claim; pass claim + clauses to the model with a structured-output instruction. Three things this tests: guardrails (route anything above a confidence/dollar threshold to a human, since a wrong auto-approval is expensive), cost control (cache embeddings, tight top-k retrieval, route easy claims to a cheaper model, cap tokens per call), and evaluation (measure retrieval accuracy and decision accuracy separately, log every decision with citations for appeal).",
      source: "cached-interview-guide",
      sourceUrl: "https://www.tryexponent.com/questions/5996/design-insurance-claim-agent",
    },
    {
      id: "q-rag-3",
      topicId: "rag-pipeline-design",
      question: "What's the core interview tradeoff around chunk size in a RAG pipeline?",
      answer: "Small chunks retrieve precisely but lose surrounding context; large chunks preserve context but retrieve less precisely and dilute similarity search.",
      source: "cached-interview-guide",
      sourceUrl: "https://www.tryexponent.com/blog/ai-engineer-interview-questions",
    },
  ]);

  await db.insert(interviewFormatNotes).values([
    { id: "if-google", company: "Google", topicId: null, formatDescription: "Single 45-min round; database selection and distributed-systems depth. NALSD format (scale an existing system) used for SRE roles.", sourceUrl: null },
    { id: "if-amazon", company: "Amazon", topicId: null, formatDescription: "Leadership Principles are embedded in every round, including coding rounds.", sourceUrl: null },
    { id: "if-meta", company: "Meta", topicId: null, formatDescription: "Product-sense + scale framing. AI-enabled coding round added Oct 2025 alongside the classic system design round.", sourceUrl: null },
    { id: "if-netflix", company: "Netflix", topicId: null, formatDescription: "Open-ended 60-min round, no fixed framework, often no shared diagramming tool.", sourceUrl: null },
    { id: "if-stripe", company: "Stripe", topicId: "rate-limiter", formatDescription: "Financial-invariants focus: ledger consistency, idempotency, webhook delivery, notification-at-scale.", sourceUrl: null },
    { id: "if-genai", company: "AI/GenAI (Anthropic, OpenAI, increasingly Google/Apple/Meta)", topicId: "rag-pipeline-design", formatDescription: "Tests design around non-determinism: hallucination mitigation, evaluation-as-infrastructure, provider fallback. Real questions surfaced: LLM query batching systems, GPU credit management, RAG-based agents under cost constraints.", sourceUrl: null },
  ]);

  // Day 1: unlock the first topic immediately.
  await db.insert(userProgress).values([
    {
      id: "up-1",
      topicId: "consistent-hashing",
      unlockedAt: new Date().toISOString(),
      quizPassed: false,
      quizAttempts: 0,
      quizPassedAt: null,
      confidenceScore: null,
    },
  ]);

  console.log("Seed complete.");
}

seed()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
