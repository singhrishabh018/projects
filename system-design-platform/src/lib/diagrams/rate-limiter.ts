import type { DiagramDef } from "./types";

// Two mechanical views side by side: token-bucket state machine, and where the
// limiter sits in the request path. Node labels are algorithm-parameter labels
// (mechanical), not explanatory prose.
export const rateLimiterDiagram: DiagramDef = {
  nodes: [
    { id: "client", position: { x: 0, y: 120 }, data: { label: "Client" }, style: nodeStyle("#94a3b8") },
    { id: "gateway", position: { x: 180, y: 120 }, data: { label: "API Gateway" }, style: nodeStyle("#94a3b8") },
    {
      id: "limiter",
      position: { x: 400, y: 120 },
      data: { label: "Rate Limiter\n(checks before forwarding)" },
      style: nodeStyle("#f59e0b"),
    },
    { id: "service", position: { x: 640, y: 40 }, data: { label: "Backend service\n(request allowed)" }, style: nodeStyle("#34d399") },
    { id: "reject", position: { x: 640, y: 200 }, data: { label: "HTTP 429\nRetry-After header" }, style: nodeStyle("#f87171") },

    { id: "bucket", position: { x: 380, y: 320 }, data: { label: "Token bucket\ncapacity: N tokens" }, style: nodeStyle("#60a5fa") },
    { id: "refill", position: { x: 200, y: 320 }, data: { label: "Refill process\nrate: R tokens/sec" }, style: nodeStyle("#60a5fa") },
    { id: "store", position: { x: 400, y: 440 }, data: { label: "Shared counter store\n(e.g. Redis, atomic incr)" }, style: nodeStyle("#a78bfa") },
  ],
  edges: [
    e("client", "gateway"),
    e("gateway", "limiter"),
    e("limiter", "service", "tokens available"),
    e("limiter", "reject", "tokens exhausted"),
    e("refill", "bucket", "+R tokens/sec"),
    e("limiter", "bucket", "consume 1 token"),
    e("bucket", "store", "persisted count"),
  ],
};

function nodeStyle(color: string) {
  return {
    width: 170,
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
