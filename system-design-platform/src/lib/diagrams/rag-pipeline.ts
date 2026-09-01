import type { DiagramDef } from "./types";

function nodeStyle(color: string) {
  return {
    width: 180,
    fontSize: 11,
    padding: 8,
    background: `${color}1a`,
    border: `1.5px solid ${color}`,
    color,
    borderRadius: 8,
    whiteSpace: "pre-line" as const,
    textAlign: "center" as const,
  };
}
function e(source: string, target: string, label?: string) {
  return {
    id: `${source}-${target}`,
    source,
    target,
    label,
    labelStyle: { fontSize: 9, fill: "#ffffff80" },
    labelShowBg: false,
    style: { stroke: "#ffffff40" },
  };
}

export const ragPipelineDiagram: DiagramDef = {
  nodes: [
    { id: "docs", position: { x: 0, y: 20 }, data: { label: "Source documents" }, style: nodeStyle("#94a3b8") },
    { id: "chunk", position: { x: 220, y: 20 }, data: { label: "Chunking\n(fixed size / semantic)" }, style: nodeStyle("#60a5fa") },
    { id: "embed", position: { x: 440, y: 20 }, data: { label: "Embedding model" }, style: nodeStyle("#60a5fa") },
    { id: "vecdb", position: { x: 660, y: 20 }, data: { label: "Vector store\n+ metadata" }, style: nodeStyle("#a78bfa") },

    { id: "query", position: { x: 0, y: 200 }, data: { label: "User query" }, style: nodeStyle("#94a3b8") },
    { id: "qembed", position: { x: 220, y: 200 }, data: { label: "Embed query" }, style: nodeStyle("#60a5fa") },
    { id: "retrieve", position: { x: 440, y: 200 }, data: { label: "Similarity search\ntop-k (hybrid optional)" }, style: nodeStyle("#f59e0b") },
    { id: "rerank", position: { x: 660, y: 200 }, data: { label: "Rerank / filter" }, style: nodeStyle("#f59e0b") },

    { id: "prompt", position: { x: 440, y: 340 }, data: { label: "Augment prompt\nquery + retrieved chunks" }, style: nodeStyle("#34d399") },
    { id: "llm", position: { x: 660, y: 340 }, data: { label: "LLM generation" }, style: nodeStyle("#34d399") },
    { id: "answer", position: { x: 880, y: 340 }, data: { label: "Answer + citations" }, style: nodeStyle("#34d399") },

    { id: "guard", position: { x: 660, y: 460 }, data: { label: "Guardrails\nconfidence / cost threshold" }, style: nodeStyle("#f87171") },
    { id: "human", position: { x: 880, y: 460 }, data: { label: "Human fallback" }, style: nodeStyle("#f87171") },
    { id: "eval", position: { x: 220, y: 460 }, data: { label: "Evaluation\nretrieval vs. answer quality (separate)" }, style: nodeStyle("#a78bfa") },
  ],
  edges: [
    e("docs", "chunk"),
    e("chunk", "embed"),
    e("embed", "vecdb", "index"),
    e("query", "qembed"),
    e("qembed", "retrieve"),
    e("vecdb", "retrieve", "top-k lookup"),
    e("retrieve", "rerank"),
    e("rerank", "prompt"),
    e("query", "prompt"),
    e("prompt", "llm"),
    e("llm", "answer"),
    e("llm", "guard"),
    e("guard", "human", "above threshold"),
    e("answer", "eval"),
    e("retrieve", "eval", "retrieval quality"),
  ],
};
