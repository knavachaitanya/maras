MIN_RELEVANCE = 1


async def run_qa(job_id: str, analyzed_results: list, query: str, result_store, intent: dict | None = None) -> list:
    print(f"[QA] received {len(analyzed_results)} results from Analysis", flush=True)
    result_store.add_log(job_id, "QA", "start", f"QA checking {len(analyzed_results)} results")

    if not analyzed_results:
        result_store.add_log(job_id, "QA", "error", "No results to QA check")
        print("[QA] No results received from Analysis agent", flush=True)
        return []

    valid = [
        r for r in analyzed_results
        if (r.get("url") or "").startswith("http")
        and (r.get("title") or "").strip()
        and float(r.get("relevance_score") or 0) >= 20
        and has_enough_visible_keyword_matches(r, intent)
    ][:20]

    # Add rank to each result
    for i, r in enumerate(valid):
        r["rank"] = i + 1
        r["is_verified"] = True

    if len(valid) == 0:
        result_store.add_log(job_id, "QA", "error", "No results passed URL validation")
        print("[QA] No results passed URL validation", flush=True)
    else:
        print(f"[QA] {len(valid)} results passed validation", flush=True)

    result_store.add_log(
        job_id,
        "QA",
        "info",
        f"{len(valid)} valid results (removed {len(analyzed_results) - len(valid)})",
    )
    result_store.add_log(job_id, "QA", "complete", f"QA complete: {len(valid)} valid results")
    return valid


def has_enough_visible_keyword_matches(result: dict, intent: dict | None) -> bool:
    if not intent or not intent.get("keywords"):
        return True
    keywords = [
        str(keyword).lower()
        for keyword in intent.get("keywords", [])
        if str(keyword).lower() not in {"best", "top", "good", "review", "reviews", "under"}
    ]
    text = f"{result.get('title', '')} {result.get('description', '')} {result.get('snippet', '')}".lower()
    matches = [keyword for keyword in keywords if keyword in text]
    simple_keywords = [keyword for keyword in keywords if " " not in keyword]
    simple_matches = [keyword for keyword in simple_keywords if keyword in text]
    required = min(2, len(simple_keywords) or len(keywords))
    boundary_keywords = [keyword for keyword in simple_keywords[:1] + simple_keywords[-1:] if keyword]
    boundary_matched = not boundary_keywords or any(keyword in text for keyword in boundary_keywords)
    instruction_terms = [keyword for keyword in simple_keywords if keyword in {"learn", "tutorial", "course", "beginner", "beginners", "guide"}]
    instruction_matched = not instruction_terms or any(keyword in str(result.get("title", "")).lower() for keyword in instruction_terms)
    return instruction_matched and boundary_matched and (len(simple_matches) >= required or len(matches) >= required)
