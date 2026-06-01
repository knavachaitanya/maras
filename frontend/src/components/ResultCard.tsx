"use client";

export default function ResultCard({ result }: { result: any }) {
  const handleClick = () => {
    if (!result.url || !result.url.startsWith("http")) return;
    window.open(result.url, "_blank", "noopener,noreferrer");
  };

  const score = Math.min(100, Math.max(0, Number(result.relevance_score) || 0));
  const scoreColor = score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#94a3b8";
  const domain =
    result.source_domain ||
    result.url?.replace(/https?:\/\/(www\.)?/, "").split("/")[0] ||
    "";

  return (
    <div
      onClick={handleClick}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        padding: "20px 24px",
        background: "#111827",
        border: "1px solid #1f2937",
        borderRadius: "12px",
        cursor: "pointer",
        transition: "border-color 0.2s, background 0.2s",
      }}
      onMouseEnter={(event) => {
        event.currentTarget.style.borderColor = "#3b82f6";
        event.currentTarget.style.background = "#131e2e";
      }}
      onMouseLeave={(event) => {
        event.currentTarget.style.borderColor = "#1f2937";
        event.currentTarget.style.background = "#111827";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: 0 }}>
          <span style={{ fontSize: "13px", color: "#6b7280", fontWeight: 500 }}>#{result.rank}</span>
          {domain && (
            <img
              src={`https://www.google.com/s2/favicons?domain=${domain}&sz=16`}
              width={16}
              height={16}
              alt=""
              style={{ borderRadius: "3px", flexShrink: 0 }}
              onError={(event) => {
                event.currentTarget.style.display = "none";
              }}
            />
          )}
          <span style={{ fontSize: "13px", color: "#6b7280", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {domain}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexShrink: 0 }}>
          {result.price && (
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "#22c55e",
                background: "#22c55e18",
                padding: "2px 10px",
                borderRadius: "20px",
              }}
            >
              {result.price}
            </span>
          )}
          <span
            style={{
              fontSize: "12px",
              fontWeight: 600,
              color: scoreColor,
              background: scoreColor + "18",
              padding: "2px 10px",
              borderRadius: "20px",
            }}
          >
            {score}% match
          </span>
          <span
            style={{
              fontSize: "11px",
              color: "#4b5563",
              background: "#1f2937",
              padding: "2px 8px",
              borderRadius: "20px",
            }}
          >
            {result.category || "article"}
          </span>
        </div>
      </div>

      <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600, color: "#e2e8f0", lineHeight: 1.4 }}>
        {result.title}
      </h3>

      <p
        style={{
          margin: 0,
          fontSize: "14px",
          color: "#94a3b8",
          lineHeight: 1.6,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {result.description}
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" }}>
        <div style={{ flex: 1, height: "3px", background: "#1f2937", borderRadius: "2px" }}>
          <div
            style={{
              width: `${score}%`,
              height: "100%",
              background: scoreColor,
              borderRadius: "2px",
              transition: "width 0.6s ease",
            }}
          />
        </div>
      </div>
    </div>
  );
}
