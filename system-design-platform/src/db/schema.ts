import { sqliteTable, text, integer } from "drizzle-orm/sqlite-core";

/**
 * Topic.source: 'primer' means the taxonomy slot + as much concept content as
 * exists comes from system-design-primer (CC BY 4.0). It does NOT guarantee the
 * primer has full prose for the topic — e.g. Rate Limiter is only linked from the
 * primer's interview-question appendix, not written up in the primer body. Where
 * that's true, contentNote says so and the page leans on the real-world-examples
 * feed + a mechanical diagram instead of primer prose that doesn't exist.
 * 'curated-exception' = not in primer at all (the AI/GenAI override, Section 5).
 */
export const topics = sqliteTable("topics", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  source: text("source", { enum: ["primer", "curated-exception"] }).notNull(),
  primerSectionUrl: text("primer_section_url"),
  contentNote: text("content_note"),
  conceptFacts: text("concept_facts", { mode: "json" }).$type<string[]>().notNull(),
  conceptDiagramKey: text("concept_diagram_key").notNull(),
  difficulty: text("difficulty", { enum: ["beginner", "intermediate", "advanced"] }).notNull(),
  relatedCompanies: text("related_companies", { mode: "json" }).$type<string[]>().notNull(),
  order: integer("order").notNull(),
});

export const realWorldExamples = sqliteTable("real_world_examples", {
  id: text("id").primaryKey(),
  topicIds: text("topic_ids", { mode: "json" }).$type<string[]>().notNull(),
  title: text("title").notNull(),
  sourceName: text("source_name").notNull(),
  sourceType: text("source_type", {
    enum: ["company-official", "named-practitioner", "technical-newsletter"],
  }).notNull(),
  sourceUrl: text("source_url").notNull(),
  extractedFacts: text("extracted_facts", { mode: "json" }).$type<{
    company: string;
    scaleNumbers: string[];
    techNamed: string[];
    facts: string[];
  }>().notNull(),
  cachedExcerpt: text("cached_excerpt"),
  publishedDate: text("published_date"),
});

/**
 * QuizQuestion.source extends the PRD's enum with 'cached-interview-guide' to
 * honestly represent Section 9's Pilot-3 resolution (archiving a published
 * Q&A guide as reference instead of a purpose-built CC deck) as distinct from
 * a true CC-licensed deck. 'UNSOURCED-gap' is used wherever the real primer
 * Anki deck content wasn't reachable in this build — flagged, not hidden.
 */
export const quizQuestions = sqliteTable("quiz_questions", {
  id: text("id").primaryKey(),
  topicId: text("topic_id").notNull(),
  question: text("question").notNull(),
  answer: text("answer").notNull(),
  source: text("source", {
    enum: ["primer-anki-deck", "other-cc-licensed-deck", "cached-interview-guide", "UNSOURCED-gap"],
  }).notNull(),
  sourceUrl: text("source_url"),
});

export const interviewFormatNotes = sqliteTable("interview_format_notes", {
  id: text("id").primaryKey(),
  company: text("company").notNull(),
  topicId: text("topic_id"),
  formatDescription: text("format_description").notNull(),
  sourceUrl: text("source_url"),
});

export const userProgress = sqliteTable("user_progress", {
  id: text("id").primaryKey(),
  topicId: text("topic_id").notNull().unique(),
  unlockedAt: text("unlocked_at").notNull(),
  quizPassed: integer("quiz_passed", { mode: "boolean" }).notNull().default(false),
  quizAttempts: integer("quiz_attempts").notNull().default(0),
  quizPassedAt: text("quiz_passed_at"),
  confidenceScore: integer("confidence_score"),
});

/**
 * Discovery source list (PRD Section 10, step 2). Bulk-seeded from the
 * kilimchoi/engineering-blogs OPML file via scripts/import-opml.ts, then the
 * n8n Discovery workflow reads this table (GET /api/pipeline/sources) instead
 * of hardcoding feed URLs inside the workflow JSON, so adding/retagging a
 * source never requires re-importing the workflow.
 */
export const sources = sqliteTable("sources", {
  id: text("id").primaryKey(),
  feedUrl: text("feed_url").notNull().unique(),
  name: text("name").notNull(),
  sourceType: text("source_type", {
    enum: ["company-official", "named-practitioner", "technical-newsletter"],
  }).notNull(),
  active: integer("active", { mode: "boolean" }).notNull().default(true),
  addedFrom: text("added_from", { enum: ["opml-bulk", "manual"] }).notNull(),
});

/**
 * Raw items landed by the n8n Discovery workflow before Classification runs
 * (PRD Section 10, steps 2-3). Keeps Discovery and Classification decoupled:
 * Discovery just lands normalized RSS items, Classification (and the weekly
 * Refresh pass) pulls whatever is 'pending' or 'low-confidence' and either
 * promotes it into `real_world_examples` or leaves a status explaining why.
 */
export const discoveredItems = sqliteTable("discovered_items", {
  id: text("id").primaryKey(),
  sourceId: text("source_id").notNull(),
  title: text("title").notNull(),
  link: text("link").notNull().unique(),
  publishedDate: text("published_date"),
  rawSnippet: text("raw_snippet"),
  classificationStatus: text("classification_status", {
    enum: ["pending", "classified", "low-confidence", "irrelevant"],
  }).notNull().default("pending"),
  discoveredAt: text("discovered_at").notNull(),
});

export const pushSubscriptions = sqliteTable("push_subscriptions", {
  id: text("id").primaryKey(),
  endpoint: text("endpoint").notNull().unique(),
  p256dh: text("p256dh").notNull(),
  auth: text("auth").notNull(),
  createdAt: text("created_at").notNull(),
});
