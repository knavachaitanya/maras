"use client";
import { useEffect, useState } from "react";
import { getLogs } from "@/lib/api";

const AGENTS = ["Orchestrator", "Research", "Analysis", "QA", "UIFormatter"];
const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export default function AgentStatusBar({ jobId }: { jobId: string }) {
  const [statuses, setStatuses] = useState<Record<string, string>>({});

  useEffect(() => {
    let closed = false;
    let interval: ReturnType<typeof setInterval> | null = null;
    const wsUrl = buildWsUrl();
    const socket = new WebSocket(`${wsUrl}/ws/agent-stream`);

    socket.onopen = () => {
      socket.send(JSON.stringify({ session_id: jobId }));
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "agent_status" && data.agent) {
          setStatuses((current) => ({
            ...current,
            [data.agent]: data.status || statusFromEvent(data.event),
          }));
        }
      } catch (error) {
        console.error("Error parsing agent status event:", error);
      }
    };

    socket.onerror = () => {
      if (!interval) {
        interval = setInterval(async () => {
          try {
            const data = await getLogs(jobId);
            const next: Record<string, string> = {};
            for (const log of data.logs || []) {
              next[log.agent] = statusFromEvent(log.event);
            }
            setStatuses(next);
          } catch (error) {
            console.error("Error fetching logs:", error);
          }
        }, 2000);
      }
    };

    socket.onclose = () => {
      if (!closed && !interval) {
        interval = setInterval(async () => {
          try {
            const data = await getLogs(jobId);
            const next: Record<string, string> = {};
            for (const log of data.logs || []) {
              next[log.agent] = statusFromEvent(log.event);
            }
            setStatuses(next);
          } catch (error) {
            console.error("Error fetching logs:", error);
          }
        }, 2000);
      }
    };

    return () => {
      closed = true;
      socket.close();
      if (interval) clearInterval(interval);
    };
  }, [jobId]);

  const getStatus = (name: string) => {
    return statuses[name] || "pending";
  };

  const statusColor: Record<string, string> = { 
    complete: "bg-emerald-500", 
    active: "bg-orange-400 animate-pulse",
    running: "bg-orange-400 animate-pulse",
    error: "bg-red-500",
    pending: "bg-zinc-700" 
  };

  return (
    <div className="flex gap-3 mb-6 flex-wrap">
      {AGENTS.map((agent) => {
        const s = getStatus(agent);
        return (
          <div key={agent} className="flex items-center gap-2 text-xs text-zinc-400">
            <span className={`w-2 h-2 rounded-full ${statusColor[s]}`} />
            {agent}
          </div>
        );
      })}
    </div>
  );
}

function buildWsUrl() {
  if (API_URL.startsWith("https://")) return API_URL.replace("https://", "wss://");
  if (API_URL.startsWith("http://")) return API_URL.replace("http://", "ws://");
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.hostname}:8000`;
  }
  return "ws://127.0.0.1:8000";
}

function statusFromEvent(event: string) {
  if (event === "complete") return "complete";
  if (event === "error") return "error";
  if (event === "start" || event === "handoff" || event === "info") return "active";
  return "pending";
}
