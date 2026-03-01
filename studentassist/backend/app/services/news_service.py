"""
News Service
- fetch_articles: Fetches headlines from NewsAPI, then expands each with Groq IN PARALLEL
- _expand_with_groq: Expands a short title+summary into a full ~500-word article
- expand_article_with_groq: Public wrapper
"""

import re
import json
import httpx
from groq import Groq
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models.schemas import NewsResponse, ArticleSummary
from app.core.config import settings


def _client() -> Groq:
    return Groq(api_key=settings.groq_api_key, timeout=60.0)


def _expand_with_groq(title: str, summary: str) -> str:
    """
    Expand a headline + short snippet into a full ~500-word article using Groq.
    NewsAPI free tier truncates content to ~200 chars, so we expand with Groq.
    """
    prompt = (
        f'You are an experienced journalist. Write a complete, detailed news article '
        f'of at least 500 words based on the following headline and summary.\n\n'
        f'Headline: {title}\n'
        f'Summary: {summary}\n\n'
        f'Requirements:\n'
        f'- Write in a clear, factual journalistic style\n'
        f'- Include background context, key facts, and implications\n'
        f'- Do NOT include a headline, byline, or any metadata — only the article body\n'
        f'- Write at least 500 words\n'
    )
    try:
        resp = _client().chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.5,
        )
        expanded = resp.choices[0].message.content.strip()
        print(f"[Groq expand] '{title[:50]}' → {len(expanded.split())} words")
        return expanded
    except Exception as e:
        print(f"[Groq expand ERROR] {title[:50]} | {e}")
        return summary if summary else title


def expand_article_with_groq(title: str, summary: str) -> str:
    """Public wrapper for _expand_with_groq."""
    return _expand_with_groq(title, summary)


# ── Category → NewsAPI query map ──────────────────────────────────────────────
CATEGORY_QUERY = {
    "editorial":   "India editorial opinion",
    "top_stories": "India top news today",
    "india":       "India news",
    "world":       "world news international",
    "business":    "business economy finance",
    "technology":  "technology AI science",
    "education":   "education schools universities India",
    "sports":      "sports cricket IPL",
}


def _expand_one(art: dict) -> ArticleSummary:
    """Expand a single raw article dict into an ArticleSummary. Runs in a thread."""
    title   = art["title"]
    snippet = art["snippet"]

    # Skip Groq if already substantial content
    if len(snippet.split()) >= 200:
        full_content = snippet
    else:
        full_content = _expand_with_groq(title, snippet)

    return ArticleSummary(
        title=title,
        summary=full_content,
        url=art["url"],
        source=art["source"],
        published_at=art["published_at"],
        category=art["category"],
    )


def fetch_articles(category: str = "editorial", max_articles: int = 8) -> NewsResponse:
    """
    1. Fetch headlines + short snippets from NewsAPI
    2. Expand ALL articles in PARALLEL with Groq (cuts wait time from ~60s to ~10s)
    3. Return NewsResponse with full content in the summary field
    """
    raw_articles = []

    # ── Step 1: Fetch from NewsAPI ────────────────────────────────────────────
    news_api_key = getattr(settings, "news_api_key", None)
    if news_api_key:
        try:
            q = CATEGORY_QUERY.get(category.lower(), category)
            r = httpx.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        q,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "pageSize": max_articles,
                    "apiKey":   news_api_key,
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()

            for item in data.get("articles", []):
                title   = item.get("title") or ""
                snippet = item.get("description") or ""
                content = item.get("content") or ""
                # Strip NewsAPI's "[+XXXX chars]" truncation marker
                content = re.sub(r'\[\+\d+ chars\]$', '', content).strip()
                best_snippet = content if len(content) > len(snippet) else snippet

                raw_articles.append({
                    "title":        title,
                    "snippet":      best_snippet,
                    "url":          item.get("url", ""),
                    "source":       item.get("source", {}).get("name", ""),
                    "published_at": item.get("publishedAt", ""),
                    "category":     category,
                })

            print(f"[NewsAPI] fetched {len(raw_articles)} articles for '{category}'")

        except Exception as e:
            print(f"[NewsAPI ERROR] {e}")

    # ── Fallback: Groq-generated stubs ───────────────────────────────────────
    if not raw_articles:
        print("[News] Falling back to Groq-generated article stubs")
        try:
            prompt = (
                f'Generate {max_articles} realistic, recent news article headlines and summaries '
                f'for the category: "{category}".\n'
                f'Return ONLY a JSON array, nothing else:\n'
                f'[{{"title":"...","summary":"2-3 sentence summary...","source":"Publisher Name",'
                f'"published_at":"2025-01-20"}}]'
            )
            resp = _client().chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.6,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                raw = match.group(0)
            items = json.loads(raw)
            for item in items:
                raw_articles.append({
                    "title":        item.get("title", ""),
                    "snippet":      item.get("summary", ""),
                    "url":          "",
                    "source":       item.get("source", "AI Generated"),
                    "published_at": item.get("published_at", ""),
                    "category":     category,
                })
        except Exception as e:
            print(f"[News Groq stub ERROR] {e}")

    # ── Step 2: Expand all articles IN PARALLEL ───────────────────────────────
    # Use up to 5 threads — Groq handles concurrent requests fine.
    # This cuts total wait from (N * ~8s) sequential → (~8s) parallel.
    articles: List[ArticleSummary] = []

    if not raw_articles:
        return NewsResponse(articles=[], total=0)

    print(f"[News] Expanding {len(raw_articles)} articles in parallel...")
    # Preserve original order using index
    results = [None] * len(raw_articles)

    with ThreadPoolExecutor(max_workers=min(5, len(raw_articles))) as executor:
        future_to_idx = {
            executor.submit(_expand_one, art): i
            for i, art in enumerate(raw_articles)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                print(f"[Expand thread ERROR] article {idx}: {e}")
                # Fall back to snippet only
                art = raw_articles[idx]
                results[idx] = ArticleSummary(
                    title=art["title"],
                    summary=art["snippet"],
                    url=art["url"],
                    source=art["source"],
                    published_at=art["published_at"],
                    category=art["category"],
                )

    articles = [a for a in results if a is not None]
    print(f"[News] Done — {len(articles)} articles ready")
    return NewsResponse(articles=articles, total=len(articles))