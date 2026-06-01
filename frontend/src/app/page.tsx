"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import SearchBar from "@/components/SearchBar";
import { searchQuery } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const result = await searchQuery(query);
      router.push(`/results?job=${result.job_id}&q=${encodeURIComponent(query)}`);
    } catch (error) {
      console.error("Search error:", error);
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-zinc-950 px-4">
      <h1 className="text-5xl font-bold text-white mb-2 tracking-tight">MARAS</h1>
      <p className="text-zinc-400 mb-10 text-lg">MultiAgent Research & Aggregation</p>
      <SearchBar onSearch={handleSearch} loading={loading} />
      <div className="mt-12 text-zinc-600 text-sm">
        AI Agent Mode - Research to Analysis to QA to Results
      </div>
    </main>
  );
}

