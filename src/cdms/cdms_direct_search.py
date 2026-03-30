"""
Direct CDMS label discovery (HTML fetch + link extraction).

``product_name`` must be the trade / label name extracted from the user query
(see ``execute_cdms_label_tool`` → ``search_with_rag`` → ``CDMSLabelTool.search``).
Optional ``user_question`` adds extra seed URLs and token hints using the raw
question text.

Tries to find specimen-label PDF links on cdms.net before falling back to
Tavily / multi-source search. Sites change often — failures are expected;
the pipeline should always fall back to the existing Tavily path.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from urllib.parse import quote_plus, urljoin, urlparse

import requests

CDMS_NET = "cdms.net"
DEFAULT_TIMEOUT = 18
DEFAULT_MAX_PAGES = 14
DEFAULT_MAX_PDF_CANDIDATES = 12

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def _env_bool(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _product_tokens(name: str) -> List[str]:
    parts = re.split(r"[^\w]+", (name or "").lower())
    return [p for p in parts if len(p) > 2]


def _trim_question_for_url(text: str, max_len: int = 220) -> str:
    q = re.sub(r"\s+", " ", (text or "").strip())
    return q[:max_len]


def _is_cdms_pdf_url(url: str) -> bool:
    """True for label PDFs on cdms.net or CDMS/Telus CDN (e.g. cdms.telusagcg.com)."""
    try:
        p = urlparse(url)
        host = (p.netloc or "").lower()
        if CDMS_NET not in host and "telusagcg.com" not in host:
            return False
        path = (p.path or "").lower()
        return path.endswith(".pdf") or "/ldat/" in path
    except Exception:
        return False


def _normalize_pdf_url(base: str, href: str) -> Optional[str]:
    if not href or href.startswith("#") or href.lower().startswith("javascript:"):
        return None
    absolute = urljoin(base, href.strip())
    if not _is_cdms_pdf_url(absolute):
        return None
    return absolute.split("#")[0]


def _is_prodidx_url(url: str) -> bool:
    u = url.lower()
    return ("cdms.net" in u or "telusagcg.com" in u) and "prodidx" in u and "key=" in u


@dataclass
class _PdfHit:
    url: str
    title: str
    score: float


class CDMSDirectLabelSearch:
    """
    Fetch CDMS HTML pages and collect label PDF URLs (and follow prodidx pages).
    """

    def __init__(self):
        self.timeout = int(os.getenv("CDMS_DIRECT_TIMEOUT", str(DEFAULT_TIMEOUT)))
        self.max_pages = int(os.getenv("CDMS_DIRECT_MAX_PAGES", str(DEFAULT_MAX_PAGES)))
        self.max_pdf_hits = int(
            os.getenv("CDMS_DIRECT_MAX_PDFS", str(DEFAULT_MAX_PDF_CANDIDATES))
        )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _extra_seed_urls(self) -> List[str]:
        raw = os.getenv("CDMS_DIRECT_EXTRA_URLS", "").strip()
        if not raw:
            return []
        return [u.strip() for u in raw.split(",") if u.strip().startswith("http")]

    def _seed_urls(
        self,
        product_name: str,
        active_ingredient: Optional[str],
        user_question: Optional[str] = None,
    ) -> List[str]:
        """Build fetch queue: extracted label name first, then optional full question."""
        urls = self._extra_seed_urls()
        label_q = quote_plus(product_name.strip())
        ai = quote_plus(active_ingredient.strip()) if active_ingredient else ""

        # Primary: query params built from the extracted product / label name
        urls.extend(
            [
                f"https://www.cdms.net/Label-Database/Advanced-Search?search={label_q}",
                f"https://www.cdms.net/Label-Database/Advanced-Search?q={label_q}",
                f"https://www.cdms.net/Label-Database/Advanced-Search?SearchText={label_q}",
                f"https://www.cdms.net/Label-Database/Advanced-Search?term={label_q}",
                f"https://www.cdms.net/Label-Database/Advanced-Search?product={label_q}",
                f"https://www.cdms.net/Label-Database/Advanced-Search?label={label_q}",
            ]
        )
        # CDMS often matches hyphenated SKUs, not spaced names (e.g. hydrovant fa vs hydrovant-fa)
        if " " in product_name.strip():
            hyp_q = quote_plus(product_name.strip().replace(" ", "-"))
            urls.append(
                f"https://www.cdms.net/Label-Database/Advanced-Search?search={hyp_q}"
            )
        if ai:
            urls.insert(
                0,
                f"https://www.cdms.net/Label-Database/Advanced-Search?activeIngredient={ai}",
            )

        # Secondary: same site, but seeded from the raw user question (phrasing + context)
        uq_raw = _trim_question_for_url(user_question or "")
        if uq_raw and uq_raw.lower() != product_name.strip().lower():
            uq = quote_plus(uq_raw)
            urls.extend(
                [
                    f"https://www.cdms.net/Label-Database/Advanced-Search?keywords={uq}",
                    f"https://www.cdms.net/Label-Database/Advanced-Search?globalSearch={uq}",
                    f"https://www.cdms.net/Label-Database/Advanced-Search?query={uq}",
                ]
            )

        urls.extend(
            [
                "https://www.cdms.net/labelsSDS/home",
                "https://www.cdms.net/LabelsSDS/home",
            ]
        )

        seen: Set[str] = set()
        out: List[str] = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def _fetch_html(self, url: str) -> Optional[str]:
        try:
            r = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if r.status_code != 200:
                return None
            ct = (r.headers.get("content-type") or "").lower()
            if "html" not in ct and "text" not in ct:
                return None
            return r.text
        except requests.RequestException:
            return None

    def _snippet_around(self, html: str, needle: str) -> str:
        idx = html.lower().find(needle.lower())
        if idx < 0:
            return ""
        chunk = html[max(0, idx - 160) : idx + len(needle) + 160]
        return re.sub(r"<[^>]+>", " ", chunk, flags=re.IGNORECASE)

    def _score_match(self, text: str, tokens: List[str]) -> float:
        if not text or not tokens:
            return 0.0
        low = text.lower()
        hits = sum(1 for t in tokens if t in low)
        return hits / max(len(tokens), 1)

    def _extract_hrefs(self, html: str, base_url: str) -> List[str]:
        found: List[str] = []
        for m in _HREF_RE.finditer(html):
            found.append(urljoin(base_url, m.group(1).strip()))
        return found

    def _collect_from_page(
        self,
        html: str,
        page_url: str,
        tokens: List[str],
        pdf_hits: Dict[str, _PdfHit],
        queue: List[str],
        seen_pages: Set[str],
    ) -> None:
        for href in self._extract_hrefs(html, page_url):
            if _is_prodidx_url(href) and href not in seen_pages:
                queue.append(href)
            pdf_u = _normalize_pdf_url(page_url, href)
            if not pdf_u or pdf_u in pdf_hits:
                continue
            snippet = self._snippet_around(html, href) + " " + pdf_u
            title_guess = pdf_u.rsplit("/", 1)[-1].replace(".pdf", "").replace("_", " ")
            sc = 0.55 * self._score_match(snippet, tokens) + 0.45 * self._score_match(
                pdf_u, tokens
            )
            if not tokens:
                sc = 0.35
            pdf_hits[pdf_u] = _PdfHit(
                url=pdf_u, title=title_guess or "CDMS label PDF", score=sc
            )

    def search_labels(
        self,
        product_name: str,
        active_ingredient: Optional[str] = None,
        max_results: int = 5,
        user_question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Returns a dict shaped like Tavily's successful search payload when PDFs
        are found; otherwise ``success: False`` so callers can fall back.

        ``product_name`` is the label/trade name from query extraction; ``user_question``
        is the original user text for extra URL seeds and relevance scoring.
        """
        if not product_name or not product_name.strip():
            return {"success": False, "error": "empty_product_name", "results": []}

        print(
            f"🔗 CDMS direct: extracted label/product={product_name!r}"
            + (
                f", user_question_hint={len(user_question or '')} chars"
                if user_question
                else ""
            )
        )

        tokens = list(dict.fromkeys(_product_tokens(product_name)))
        if active_ingredient:
            tokens = list(dict.fromkeys(tokens + _product_tokens(active_ingredient)))
        if user_question:
            tokens = list(
                dict.fromkeys(tokens + _product_tokens(user_question))
            )[:24]

        queue: List[str] = self._seed_urls(
            product_name, active_ingredient, user_question=user_question
        )
        seen_pages: Set[str] = set()
        pdf_hits: Dict[str, _PdfHit] = {}
        pages_fetched = 0

        while queue and pages_fetched < self.max_pages:
            url = queue.pop(0)
            if url in seen_pages:
                continue
            seen_pages.add(url)
            html = self._fetch_html(url)
            pages_fetched += 1
            if not html:
                continue
            self._collect_from_page(html, url, tokens, pdf_hits, queue, seen_pages)

        if not pdf_hits:
            return {
                "success": False,
                "error": "cdms_direct_no_pdf_links",
                "results": [],
                "result_count": 0,
            }

        ranked = sorted(pdf_hits.values(), key=lambda h: h.score, reverse=True)[
            : max(max_results * 2, self.max_pdf_hits)
        ]

        if tokens:
            ranked = [h for h in ranked if h.score >= 0.2] or ranked[:3]

        ranked = ranked[:max_results]

        results: List[Dict[str, Any]] = []
        for h in ranked:
            results.append(
                {
                    "title": h.title,
                    "url": h.url,
                    "content": f"CDMS direct link (score={h.score:.2f})",
                    "score": min(1.0, 0.5 + h.score),
                }
            )

        return {
            "success": True,
            "result_count": len(results),
            "results": results,
            "answer": (
                f"Found {len(results)} CDMS label PDF(s) on cdms.net for “{product_name.strip()}” "
                f"(direct HTML fetch)."
            ),
            "query": product_name.strip(),
            "source": "CDMS (direct)",
            "sources_tried": ["CDMS (direct)"],
            "search_metadata": {
                "method": "cdms_html_fetch",
                "pages_fetched": pages_fetched,
            },
        }


def try_direct_cdms_search(
    product_name: str,
    active_ingredient: Optional[str] = None,
    max_results: int = 5,
    user_question: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    If enabled via env, run direct CDMS search. Returns None when disabled or
    when no PDFs were found (caller should use Tavily).

    ``product_name`` comes from ``execute_cdms_label_tool`` extraction; pass the
    same ``user_question`` you send to RAG so CDMS pages can be seeded with it.
    """
    if not _env_bool("CDMS_DIRECT_SEARCH", True):
        return None

    if _env_bool("CDMS_DIRECT_USE_PLAYWRIGHT", True):
        try:
            from src.cdms.cdms_playwright_search import playwright_search_labels

            pw = playwright_search_labels(
                product_name=product_name,
                active_ingredient=active_ingredient,
                max_results=max_results,
                user_question=user_question,
            )
            if pw and pw.get("success") and pw.get("result_count"):
                return pw
        except Exception as e:
            print(f"⚠️ CDMS Playwright failed, trying HTML fetch: {e}")

    client = CDMSDirectLabelSearch()
    out = client.search_labels(
        product_name=product_name,
        active_ingredient=active_ingredient,
        max_results=max_results,
        user_question=user_question,
    )
    if not out.get("success") or not out.get("result_count"):
        return None
    return out
