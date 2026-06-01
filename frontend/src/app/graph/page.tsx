"use client";
import dynamic from "next/dynamic";

const GraphViewer = dynamic(() => import("@/components/GraphViewer"), { ssr: false });

export default function GraphPage() {
  return (
    <main className="min-h-screen bg-zinc-950">
      <div className="p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Codebase Graph</h1>
        <p className="text-zinc-400 text-sm mb-6">
          Visual dependency map of all modules and agents.
        </p>
      </div>
      <GraphViewer />
    </main>
  );
}
