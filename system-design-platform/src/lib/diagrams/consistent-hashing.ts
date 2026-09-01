import type { DiagramDef } from "./types";

// A hash ring laid out as a literal circle: node angle = hash position (0-360deg).
// Virtual nodes (vA0, vA1, vB0...) let each physical server (A, B, C) own several
// ring positions, which is the actual mechanism the primer's Sharding section
// gestures at ("a sharding function based on consistent hashing") without
// spelling out virtual nodes.
const R = 220;
const CENTER = { x: 300, y: 260 };
function pointOnRing(deg: number) {
  const rad = (deg * Math.PI) / 180;
  return { x: CENTER.x + R * Math.sin(rad), y: CENTER.y - R * Math.cos(rad) };
}

const virtualNodes: { id: string; deg: number; server: "A" | "B" | "C" }[] = [
  { id: "vA0", deg: 10, server: "A" },
  { id: "vB0", deg: 55, server: "B" },
  { id: "vA1", deg: 95, server: "A" },
  { id: "vC0", deg: 140, server: "C" },
  { id: "vB1", deg: 190, server: "B" },
  { id: "vA2", deg: 230, server: "A" },
  { id: "vC1", deg: 275, server: "C" },
  { id: "vB2", deg: 320, server: "B" },
];

const serverColor: Record<string, string> = {
  A: "#34d399",
  B: "#60a5fa",
  C: "#f472b6",
};

const keys = [
  { id: "key1", label: "key: user_842", deg: 30 },
  { id: "key2", label: "key: user_119", deg: 165 },
  { id: "key3", label: "key: user_501", deg: 300 },
];

export const consistentHashingDiagram: DiagramDef = {
  nodes: [
    {
      id: "ring-circle",
      position: { x: CENTER.x - R - 24, y: CENTER.y - R - 24 },
      data: { label: "" },
      selectable: false,
      draggable: false,
      style: {
        width: (R + 24) * 2,
        height: (R + 24) * 2,
        borderRadius: "50%",
        background: "transparent",
        border: "1.5px dashed #ffffff30",
      },
    },
    {
      id: "ring-label",
      position: { x: CENTER.x - 70, y: CENTER.y - 10 },
      data: { label: "hash ring: 0 .. 2^32-1" },
      selectable: false,
      draggable: false,
      style: {
        width: 140,
        background: "transparent",
        border: "none",
        color: "#ffffff50",
        fontSize: 10,
        textAlign: "center" as const,
      },
    },
    ...virtualNodes.map((v) => {
      const p = pointOnRing(v.deg);
      return {
        id: v.id,
        position: { x: p.x - 30, y: p.y - 18 },
        data: { label: `Server ${v.server}\n${v.id}` },
        style: {
          width: 60,
          height: 36,
          fontSize: 10,
          background: `${serverColor[v.server]}22`,
          border: `1.5px solid ${serverColor[v.server]}`,
          color: serverColor[v.server],
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          whiteSpace: "pre-line",
        },
      };
    }),
    ...keys.map((k) => {
      const p = pointOnRing(k.deg);
      // pull keys slightly inside the ring so they read as "landing" on it
      const inward = 0.72;
      const x = CENTER.x + (p.x - CENTER.x) * inward;
      const y = CENTER.y + (p.y - CENTER.y) * inward;
      return {
        id: k.id,
        position: { x: x - 45, y: y - 12 },
        data: { label: k.label },
        style: {
          width: 90,
          height: 24,
          fontSize: 9,
          background: "#ffffff10",
          border: "1px dashed #ffffff50",
          color: "#fff",
          borderRadius: 6,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        },
      };
    }),
  ],
  edges: keys.map((k) => {
    // route each key to the next virtual node clockwise (the actual consistent-
    // hashing lookup rule: walk clockwise from the key's hash to the first node).
    const target = [...virtualNodes].sort((a, b) => a.deg - b.deg).find((v) => v.deg >= k.deg) ?? virtualNodes[0];
    return {
      id: `${k.id}-${target.id}`,
      source: k.id,
      target: target.id,
      animated: true,
      style: { stroke: serverColor[target.server], strokeWidth: 1.5 },
      label: "clockwise lookup",
      labelStyle: { fontSize: 9, fill: "#ffffff80" },
      labelShowBg: false,
    };
  }),
};
