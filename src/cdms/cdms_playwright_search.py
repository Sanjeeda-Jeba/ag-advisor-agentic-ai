"""
CDMS label discovery via the real Advanced Search UI (Playwright).

Drives https://www.cdms.net/Label-Database/Advanced-Search: product name →
resolve tiles → pick best-matching product(s) → specimen label download URLs
(actual PDFs are on cdms.telusagcg.com).
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

CDMS_ADVANCED_SEARCH = "https://www.cdms.net/Label-Database/Advanced-Search"


def _cdms_product_query_variants(name: str) -> List[str]:
    """
    CDMS Advanced Search is picky: e.g. "hydrovant fa" → no hits, "hydrovant-fa" → hits.
    Try several spellings (space vs hyphen, concatenated) in order.
    """
    s = re.sub(r"\s+", " ", (name or "").strip())[:120]
    if len(s) < 2:
        return []
    out: List[str] = []
    seen: set[str] = set()

    def add(x: str) -> None:
        x = x.strip()
        if len(x) < 2:
            return
        k = x.lower()
        if k in seen:
            return
        seen.add(k)
        out.append(x)

    add(s)
    if " " in s:
        add(s.replace(" ", "-"))
        add(s.replace(" ", ""))
    parts = s.split()
    if len(parts) >= 2:
        add("-".join(parts))
    return out


def _poll_resolve_tile_count(page, timeout_ms: int) -> int:
    """After clicking Next on product name, wait for tiles or explicit no-results."""
    deadline = time.monotonic() + timeout_ms / 1000.0
    while time.monotonic() < deadline:
        n = page.locator("label.tile-child").count()
        if n > 0:
            page.wait_for_timeout(400)
            return page.locator("label.tile-child").count()
        try:
            no_hit = page.get_by_text("No Product Names", exact=False)
            if no_hit.count() > 0 and no_hit.first.is_visible():
                return 0
        except Exception:
            pass
        page.wait_for_timeout(200)
    return 0


def _match_tokens(*texts: str) -> List[str]:
    """Tokens for scoring tiles; keeps 2-char alphanumerics (e.g. 4f, 2d)."""
    out: List[str] = []
    for s in texts:
        if not s:
            continue
        parts = re.split(r"[^\w]+", s.lower())
        for p in parts:
            if len(p) >= 2 and p not in out:
                out.append(p)
    return out


def _tile_score(product_name: str, user_question: Optional[str], tile_text: str) -> float:
    tokens = _match_tokens(product_name, user_question or "")
    if not tokens:
        return 0.0
    tl = re.sub(r"[®™©]", "", tile_text.lower())
    hits = sum(1 for t in tokens if t in tl)
    return hits / max(len(tokens), 1)


def _rank_tiles(
    product_name: str, user_question: Optional[str], tile_texts: List[str]
) -> List[Tuple[int, float]]:
    scored = [
        (i, _tile_score(product_name, user_question, txt))
        for i, txt in enumerate(tile_texts)
    ]
    scored.sort(key=lambda x: (-x[1], x[0]))
    return scored


def _append_specimen(page, title_line: str, collected: List[Dict[str, str]]) -> None:
    try:
        with page.expect_download(timeout=20000) as dl_info:
            page.locator("a", has_text="Specimen Label").first.click()
        d = dl_info.value
        if d.url:
            collected.append({"title": title_line[:220], "url": d.url})
    except Exception as e:
        print(f"⚠️ CDMS Playwright specimen: {e}")


def playwright_search_labels(
    product_name: str,
    active_ingredient: Optional[str] = None,
    max_results: int = 5,
    user_question: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return Tavily-shaped dict with PDF URLs, or None if Playwright is unavailable
    or the flow fails (caller may fall back to HTML scrape / Tavily).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    if not product_name or not str(product_name).strip():
        return None

    max_results = max(1, min(int(max_results or 3), 5))
    nav_timeout = int(os.getenv("CDMS_PLAYWRIGHT_TIMEOUT_MS", "25000"))
    step_sleep_ms = int(os.getenv("CDMS_PLAYWRIGHT_STEP_MS", "500"))

    name = re.sub(r"[®™©]", "", str(product_name).strip())[:120]
    if len(name) < 2:
        return None

    collected: List[Dict[str, str]] = []
    pick_indices: List[int] = []
    resolved_query = name
    resolve_wait_ms = min(nav_timeout, 18000)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            variants = _cdms_product_query_variants(name)
            vseen = {v.lower() for v in variants}
            if user_question:
                uq = re.sub(r"[®™©]", "", user_question.strip())[:120]
                for v in _cdms_product_query_variants(uq):
                    if v.lower() not in vseen:
                        vseen.add(v.lower())
                        variants.append(v)

            n = 0
            tiles = page.locator("label.tile-child")
            for cand in variants:
                page.goto(
                    CDMS_ADVANCED_SEARCH,
                    wait_until="domcontentloaded",
                    timeout=nav_timeout,
                )
                page.wait_for_timeout(800)
                page.fill("#productName", cand)
                if active_ingredient and str(active_ingredient).strip():
                    try:
                        page.fill("#commonName", str(active_ingredient).strip()[:120])
                    except Exception:
                        pass
                page.wait_for_timeout(step_sleep_ms)
                page.get_by_role("button", name="Next").first.click()
                n = _poll_resolve_tile_count(page, resolve_wait_ms)
                if n > 0:
                    resolved_query = cand
                    print(f"🔗 CDMS Playwright: matched query {cand!r} ({n} product row(s))")
                    break

            if n == 0:
                print(
                    f"⚠️ CDMS Playwright: no product rows for variants {variants[:5]}…"
                )
                return None

            page.wait_for_timeout(1200)

            tile_texts = [tiles.nth(i).inner_text() for i in range(n)]
            ranked = _rank_tiles(name, user_question, tile_texts)
            pick_indices = []
            for idx, sc in ranked:
                if len(pick_indices) >= max_results:
                    break
                if sc > 0 or len(ranked) == 1:
                    pick_indices.append(idx)
                elif len(pick_indices) == 0:
                    pick_indices.append(idx)
            if not pick_indices:
                pick_indices = [ranked[0][0]]

            for i in range(n):
                cb = tiles.nth(i).locator('input[type="checkbox"]')
                if i in pick_indices:
                    cb.check()
                else:
                    try:
                        cb.uncheck()
                    except Exception:
                        pass

            page.wait_for_timeout(step_sleep_ms)
            page.locator('button.btn-primary[title="Next"]').last.click()
            page.wait_for_timeout(4000)

            h = page.evaluate("() => location.hash")

            # One product: land directly on detail view
            if "Result-product/" in h and "Result-products" not in h:
                line = tile_texts[pick_indices[0]].split("\n")[0].strip()
                _append_specimen(page, line, collected)

            # Several: intermediate product list
            elif "Result-products" in h:
                lines_to_visit = [
                    tile_texts[i].split("\n")[0].strip() for i in pick_indices
                ]
                for line in lines_to_visit:
                    if len(collected) >= max_results:
                        break
                    try:
                        page.get_by_text(line, exact=True).first.click()
                    except Exception:
                        page.get_by_text(line, exact=False).first.click()
                    page.wait_for_timeout(3500)
                    page.wait_for_function(
                        "() => location.hash.includes('Result-product/')",
                        timeout=nav_timeout,
                    )
                    _append_specimen(page, line, collected)
                    if len(collected) >= max_results:
                        break
                    page.go_back()
                    page.wait_for_timeout(2500)
                    page.wait_for_function(
                        "() => location.hash.includes('Result-products')",
                        timeout=nav_timeout,
                    )
            else:
                # Hash not ready — try specimen if detail UI is already visible
                if page.locator("a", has_text="Specimen Label").count():
                    line = tile_texts[pick_indices[0]].split("\n")[0].strip()
                    _append_specimen(page, line, collected)

        except Exception as e:
            print(f"⚠️ CDMS Playwright: {e}")
            collected = []
        finally:
            context.close()
            browser.close()

    if not collected:
        return None

    results: List[Dict[str, Any]] = []
    for i, item in enumerate(collected[:max_results]):
        results.append(
            {
                "title": item["title"],
                "url": item["url"],
                "content": "CDMS Advanced Search — specimen label (Playwright)",
                "score": 0.95 - i * 0.03,
            }
        )

    return {
        "success": True,
        "result_count": len(results),
        "results": results,
        "answer": (
            f"Found {len(results)} specimen label PDF(s) via CDMS Advanced Search "
            f"for “{name}” (search box used: “{resolved_query}”)."
        ),
        "query": resolved_query,
        "source": "CDMS (Playwright)",
        "sources_tried": ["CDMS (Playwright)"],
        "search_metadata": {
            "method": "cdms_playwright_advanced_search",
            "picked_tile_indices": pick_indices,
            "cdms_query_used": resolved_query,
            "extracted_product_name": name,
        },
    }
