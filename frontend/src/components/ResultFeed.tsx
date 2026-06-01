import ResultCard from "./ResultCard";

export default function ResultFeed({ results }: { results: any[] }) {
  const validResults = results.filter((r) => r.url?.startsWith("http"));

  if (!validResults.length) return <p className="text-zinc-500">No results found.</p>;

  return (
    <div className="flex flex-col gap-4">
      {validResults.map((r) => (
        <ResultCard key={r.id || r.rank} result={r} />
      ))}
    </div>
  );
}
