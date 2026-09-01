"use client";

import { ReactFlow, Background, Controls, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { consistentHashingDiagram } from "@/lib/diagrams/consistent-hashing";
import { rateLimiterDiagram } from "@/lib/diagrams/rate-limiter";
import { ragPipelineDiagram } from "@/lib/diagrams/rag-pipeline";

const registry: Record<string, { nodes: Node[]; edges: Edge[] }> = {
  "consistent-hashing-ring": consistentHashingDiagram,
  "rate-limiter-flow": rateLimiterDiagram,
  "rag-pipeline-flow": ragPipelineDiagram,
};

export function TopicDiagram({ diagramKey }: { diagramKey: string }) {
  const def = registry[diagramKey];
  if (!def) return null;

  return (
    <div className="h-[520px] w-full overflow-hidden rounded-xl border border-white/10 bg-[#0a0a0a]">
      <ReactFlow
        nodes={def.nodes}
        edges={def.edges}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
      >
        <Background color="#ffffff20" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
      <style>{`
        .react-flow__handle { opacity: 0; }
        .react-flow__node-default {
          background: transparent;
          border: none;
          padding: 0;
          border-radius: 0;
          width: auto;
        }
        .react-flow__node-default.selected {
          box-shadow: none;
        }
      `}</style>
    </div>
  );
}
