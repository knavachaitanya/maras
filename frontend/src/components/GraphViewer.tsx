"use client";
import { useEffect, useRef, useState } from "react";

export default function GraphViewer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && containerRef.current) {
      const loadGraph = async () => {
        try {
          const graphifyModule = await import("graphify-codebase/viewer").catch(() => null);
          if (!graphifyModule) {
            setError(true);
            return;
          }
          
          const response = await fetch("/graph-data.json");
          const data = await response.json();
          
          if (containerRef.current) {
            graphifyModule.renderGraph(containerRef.current, data, {
              theme: "dark",
              width: window.innerWidth,
              height: window.innerHeight - 160,
            });
          }
        } catch {
          setError(true);
        }
      };
      loadGraph();
    }
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-500">
        <div className="text-center">
          <p className="text-lg mb-2">Graph data not available</p>
          <p className="text-sm">Run: <code className="bg-zinc-800 px-2 py-1 rounded">npm run graph</code></p>
        </div>
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" style={{ height: "calc(100vh - 160px)" }} />;
}
