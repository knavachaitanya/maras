"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AgentStatusBar from "@/components/AgentStatusBar";
import ResultCard from "@/components/ResultCard";
import { getLogs, getResults } from "@/lib/api";

function ResultsContent() {
  const params = useSearchParams();
  const jobId = params.get("job");
  const query = params.get("q") || "";
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [html, setHtml] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const validResults = results.filter((result) => result.url?.startsWith("http"));

  useEffect(() => {
    if (!jobId) return;
    let failedPollCount = 0;
    let stopped = false;

    const poll = async () => {
      try {
        const [resultData, logData] = await Promise.allSettled([
          getResults(jobId),
          getLogs(jobId),
        ]);

        if (logData.status === "fulfilled") {
          setLogs(logData.value.logs || []);
        }

        if (resultData.status !== "fulfilled") {
          throw resultData.reason;
        }

        const data = resultData.value;
        const session = data.session || data;
        const validResults = (data.results || []).filter((item: any) =>
          item.url?.startsWith("http")
        );

        setStatus(session.status || data.status);
        setHtml(data.output || "");
        failedPollCount = 0;

        if (session.status === "complete") {
          setResults(validResults);
          stopped = true;
          clearInterval(interval);
        } else if (session.status === "failed" || session.status === "error") {
          const currentLogs = logData.status === "fulfilled" ? logData.value.logs || [] : [];
          const errorLog = currentLogs.find((l: any) => l.event === "error");
          setError(errorLog?.message || data.error || "Pipeline failed");
          stopped = true;
          clearInterval(interval);
        }
      } catch (error: any) {
        failedPollCount += 1;
        
        if (error?.message?.includes("429") || error?.message?.includes("503")) {
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
        if (failedPollCount >= 3) {
          setStatus("failed");
          setError("Failed to connect to server after multiple attempts");
          stopped = true;
          clearInterval(interval);
        }
      }
    };

    const interval = setInterval(() => {
      if (!stopped) void poll();
    }, 2000);
    void poll();

    const timeout = setTimeout(() => {
      if (!stopped) {
        clearInterval(interval);
        setStatus("failed");
        setError("Request timeout");
      }
    }, 180000);

    return () => {
      stopped = true;
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [jobId]);

  return (
    <main className="min-h-screen bg-zinc-950 text-white py-8">
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "0 24px 24px" }}>
        <h2 className="text-2xl font-semibold mb-1">Results for</h2>
        <p className="text-zinc-400 text-lg mb-6">&quot;{query}&quot;</p>
        <AgentStatusBar jobId={jobId!} />
      </div>
      {status === "loading" && (
        <div style={{ maxWidth: "860px", margin: "0 auto", padding: "0 24px" }}>
          <p className="text-zinc-500 animate-pulse mt-8">Agent pipeline running...</p>
        </div>
      )}
      <div style={{ maxWidth: "860px", margin: "0 auto", padding: "0 24px 48px" }}>
        {status === "complete" && (
          <p style={{ color: "#6b7280", fontSize: "14px", marginBottom: "20px" }}>
            {validResults.length} results for <strong style={{ color: "#e2e8f0" }}>&quot;{query}&quot;</strong>
          </p>
        )}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {validResults.map((result) => <ResultCard key={result.id || result.url} result={result} />)}
        </div>
        {status === "complete" && validResults.length === 0 && (
          <div style={{ textAlign: "center", padding: "80px 0", color: "#6b7280" }}>
            <p style={{ fontSize: "18px", marginBottom: "8px" }}>No relevant results found</p>
            <p style={{ fontSize: "14px" }}>Try rephrasing your query to be more specific</p>
          </div>
        )}
      </div>
      {status === "complete" && !validResults.length && !html && (
        <div className="mt-8 p-4 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
          <p className="text-yellow-400 font-semibold mb-2">Pipeline completed but no results were generated.</p>
          {logs.length > 0 && (
            <div className="mt-3 text-sm text-zinc-400">
              <p className="font-semibold mb-1">Pipeline logs:</p>
              {logs.slice(-5).map((log: any, i: number) => (
                <div key={i} className={log.event === "error" ? "text-red-400" : ""}>
                  [{log.agent}] {log.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {status === "failed" && (
        <div className="mt-8 p-4 bg-red-900/20 border border-red-700/30 rounded-lg">
          <p className="text-red-400 font-semibold mb-2">Error: {error || "Something went wrong"}</p>
          {logs.length > 0 && (
            <div className="mt-3 text-sm text-zinc-300">
              <p className="font-semibold mb-1">Error details:</p>
              {logs.filter((l: any) => l.event === "error").map((log: any, i: number) => (
                <div key={i} className="text-red-300 mb-1">
                  [{log.agent}] {log.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-zinc-950 text-white px-4 py-8">Loading...</main>}>
      <ResultsContent />
    </Suspense>
  );
}

