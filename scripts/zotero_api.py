#!/usr/bin/env python3
"""Zotero Local API helper — query items, collections, notes, and attachments."""

import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "http://localhost:23119/api"
OPENALEX_BASE = "https://api.openalex.org"
# user id 0 is an alias for the current local user
USER_PATH = f"{BASE}/users/0"
ALIASES_PATH = os.path.join(os.path.dirname(__file__), "bilingual_aliases.json")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "toward",
    "via", "with", "we", "our", "using", "used", "based", "study", "towards",
    "through", "can", "than", "more", "less", "new", "approach", "method", "methods",
    "model", "models", "analysis", "system", "systems", "论文", "方法", "研究", "模型",
    "一个", "一种", "基于", "面向", "用于", "相关", "问题", "系统", "方法研究"
}


def _get(url: str):
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _url(path: str, params: dict | None = None) -> str:
    url = f"{USER_PATH}/{path}"
    if params:
        params = {k: v for k, v in params.items() if v is not None}
        if params:
            url += "?" + urllib.parse.urlencode(params)
    return url


def _fetch_item(key: str):
    return _get(_url(f"items/{key}"))


def _fetch_children(key: str):
    return _get(_url(f"items/{key}/children"))


def _fetch_collections():
    return _get(_url("collections"))


def _fetch_openalex_works(search_query: str, per_page: int = 10, mailto: str | None = None):
    params = {
        "search": search_query,
        "per-page": str(per_page),
        "select": "id,display_name,publication_year,authorships,primary_location,locations,best_oa_location,doi,biblio,abstract_inverted_index",
    }
    if mailto:
        params["mailto"] = mailto
    return _get(f"{OPENALEX_BASE}/works?{urllib.parse.urlencode(params)}")


def _strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _truncate(text: str, limit: int) -> str:
    text = text.strip()
    if limit <= 0 or len(text) <= limit:
        return text
    return text[: max(limit - 3, 0)].rstrip() + "..."


def _creator_name(creator: dict) -> str:
    if creator.get("name"):
        return creator["name"]
    first = creator.get("firstName", "").strip()
    last = creator.get("lastName", "").strip()
    return f"{first} {last}".strip()


def _authors_line(item_data: dict) -> str:
    creators = item_data.get("creators", [])
    names = [_creator_name(c) for c in creators if _creator_name(c)]
    return ", ".join(names)


def _first_author_label(item_data: dict) -> str:
    creators = item_data.get("creators", [])
    names = [_creator_name(c) for c in creators if _creator_name(c)]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return f"{names[0]} et al."


def _item_year(item_data: dict) -> str:
    date = item_data.get("date") or ""
    match = re.search(r"\b(19|20)\d{2}\b", date)
    return match.group(0) if match else ""


def _resolve_attachment_path(child: dict) -> str | None:
    data = child.get("data", {})
    filename = data.get("filename")
    key = child.get("key")
    if filename and key:
        candidate = os.path.join(os.path.expanduser("~/Zotero/storage"), key, filename)
        if os.path.exists(candidate):
            return candidate

    href = child.get("links", {}).get("enclosure", {}).get("href", "")
    if href.startswith("file://"):
        return urllib.parse.unquote(href[7:])
    return None


def _format_item_card(item: dict, long: bool = False, abstract_limit: int = 280) -> str:
    data = item["data"]
    lines = []
    author = _first_author_label(data)
    year = _item_year(data)
    title = data.get("title", "?")
    item_type = data.get("itemType", "?")
    lines.append(f'[{item["key"]}] ({item_type}) {author} ({year}) {title}'.replace("  ", " ").strip())

    if long:
        authors_line = _authors_line(data)
        if authors_line:
            lines.append(f"  authors: {authors_line}")
        venue = data.get("publicationTitle") or data.get("proceedingsTitle") or data.get("bookTitle")
        if venue:
            lines.append(f"  venue: {venue}")
        if data.get("date"):
            lines.append(f"  date: {data['date']}")
        abstract = _strip_html(data.get("abstractNote", ""))
        if abstract:
            lines.append(f"  abstract: {_truncate(abstract, abstract_limit)}")
        tags = [tag["tag"] for tag in data.get("tags", []) if tag.get("tag")]
        if tags:
            lines.append(f"  tags: {', '.join(tags)}")
    return "\n".join(lines)


def _print_items(items, long: bool = False, abstract_limit: int = 280):
    for item in items:
        print(_format_item_card(item, long=long, abstract_limit=abstract_limit))


def _render_note(note_item: dict, limit: int = 800, full: bool = False) -> str:
    data = note_item["data"]
    text = _strip_html(data.get("note", ""))
    if not full:
        text = _truncate(text, limit)
    if not text:
        text = "(empty)"
    return text


def _collection_name_map():
    collections = _fetch_collections()
    return {collection["key"]: collection["data"]["name"] for collection in collections}


def _normalize_alias_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _load_aliases() -> dict[str, list[str]]:
    if not os.path.exists(ALIASES_PATH):
        return {}
    with open(ALIASES_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    aliases = {}
    for key, values in raw.items():
        normalized_key = _normalize_alias_text(key)
        normalized_values = []
        for value in values:
            normalized_value = _normalize_alias_text(value)
            if normalized_value and normalized_value != normalized_key:
                normalized_values.append(value.strip())
        if normalized_key and normalized_values:
            aliases[key.strip()] = normalized_values
    return aliases


def _expand_query(query: str) -> list[str]:
    normalized_query = _normalize_alias_text(query)
    variants = [query.strip()]
    seen = {_normalize_alias_text(query)}
    aliases = _load_aliases()

    for alias_key, mapped_values in aliases.items():
        normalized_key = _normalize_alias_text(alias_key)
        normalized_values = [_normalize_alias_text(value) for value in mapped_values]

        matched = normalized_query == normalized_key or normalized_query in normalized_values
        if not matched:
            continue

        candidates = [alias_key] + mapped_values
        for candidate in candidates:
            normalized_candidate = _normalize_alias_text(candidate)
            if normalized_candidate and normalized_candidate not in seen:
                variants.append(candidate)
                seen.add(normalized_candidate)

    return variants


def _fetch_search_items(query: str, args) -> list[dict]:
    params = {
        "q": query,
        "itemType": "-attachment",
        "limit": str(args.limit),
        "sort": args.sort or "dateModified",
        "direction": "desc",
    }
    if args.collection:
        path = f"collections/{args.collection}/items"
    else:
        path = "items"
    return _get(_url(path, params))


def _dedupe_items(items: list[dict]) -> list[dict]:
    deduped = []
    seen = set()
    for item in items:
        key = item.get("key") or item.get("data", {}).get("key")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _filter_list_items(items: list[dict], include_notes: bool = False) -> list[dict]:
    filtered = []
    for item in items:
        item_type = item.get("data", {}).get("itemType")
        if item_type == "attachment":
            continue
        if item_type == "note" and not include_notes:
            continue
        filtered.append(item)
    return filtered


def _text_matches_query(text: str, query: str) -> bool:
    normalized_text = _normalize_alias_text(_strip_html(text))
    normalized_query = _normalize_alias_text(query)
    return bool(normalized_query) and normalized_query in normalized_text


def _filter_items_by_abstract(items: list[dict], queries: list[str]) -> list[dict]:
    filtered = []
    for item in items:
        abstract = item.get("data", {}).get("abstractNote", "")
        if any(_text_matches_query(abstract, query) for query in queries):
            filtered.append(item)
    return filtered


def _extract_tokens(text: str) -> list[str]:
    cleaned = _normalize_alias_text(_strip_html(text))
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9][a-z0-9\-]{2,}", cleaned)
    return [token for token in tokens if token not in STOPWORDS]


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = _normalize_alias_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return result


def _item_tags(item_data: dict) -> list[str]:
    return [tag["tag"] for tag in item_data.get("tags", []) if tag.get("tag")]


def _author_tokens(item_data: dict) -> list[str]:
    tokens = []
    for creator in item_data.get("creators", []):
        name = _creator_name(creator)
        if name:
            tokens.extend(_extract_tokens(name))
    return _unique_preserve_order(tokens)


def _keywords_from_item(item_data: dict, limit: int = 8) -> list[str]:
    title_tokens = _extract_tokens(item_data.get("title", ""))
    abstract_tokens = _extract_tokens(item_data.get("abstractNote", ""))
    tag_tokens = []
    for tag in _item_tags(item_data):
        tag_tokens.extend(_extract_tokens(tag))

    weighted = title_tokens * 3 + tag_tokens * 2 + abstract_tokens
    counts = {}
    first_seen = {}
    for index, token in enumerate(weighted):
        counts[token] = counts.get(token, 0) + 1
        first_seen.setdefault(token, index)

    ranked = sorted(counts, key=lambda token: (-counts[token], first_seen[token], -len(token)))
    return ranked[:limit]


def _candidate_queries_from_item(item_data: dict, limit: int = 6) -> list[str]:
    queries = []
    tags = _item_tags(item_data)
    queries.extend(tags[:2])

    title = item_data.get("title", "").strip()
    if title:
        queries.append(title)

    queries.extend(_keywords_from_item(item_data, limit=limit))
    return _unique_preserve_order(queries)[:limit]


def _jaccard_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _similarity_score(source_data: dict, candidate_data: dict) -> tuple[float, list[str]]:
    reasons = []
    score = 0.0

    source_tags = set(_normalize_alias_text(tag) for tag in _item_tags(source_data))
    candidate_tags = set(_normalize_alias_text(tag) for tag in _item_tags(candidate_data))
    shared_tags = source_tags & candidate_tags
    if shared_tags:
        score += 4.0 * len(shared_tags)
        reasons.append(f"shared tags: {', '.join(sorted(shared_tags)[:3])}")

    source_title_tokens = set(_extract_tokens(source_data.get("title", "")))
    candidate_title_tokens = set(_extract_tokens(candidate_data.get("title", "")))
    title_overlap = source_title_tokens & candidate_title_tokens
    if title_overlap:
        score += 6.0 * _jaccard_score(source_title_tokens, candidate_title_tokens)
        reasons.append(f"title overlap: {', '.join(sorted(title_overlap)[:4])}")

    source_abstract_tokens = set(_extract_tokens(source_data.get("abstractNote", "")))
    candidate_abstract_tokens = set(_extract_tokens(candidate_data.get("abstractNote", "")))
    abstract_overlap = source_abstract_tokens & candidate_abstract_tokens
    if abstract_overlap:
        score += 5.0 * _jaccard_score(source_abstract_tokens, candidate_abstract_tokens)
        reasons.append(f"abstract overlap: {', '.join(sorted(abstract_overlap)[:4])}")

    source_authors = set(_author_tokens(source_data))
    candidate_authors = set(_author_tokens(candidate_data))
    shared_authors = source_authors & candidate_authors
    if shared_authors:
        score += 2.5
        reasons.append(f"shared authors: {', '.join(sorted(shared_authors)[:3])}")

    source_venue = _normalize_alias_text(
        source_data.get("publicationTitle") or source_data.get("proceedingsTitle") or source_data.get("bookTitle") or ""
    )
    candidate_venue = _normalize_alias_text(
        candidate_data.get("publicationTitle") or candidate_data.get("proceedingsTitle") or candidate_data.get("bookTitle") or ""
    )
    if source_venue and candidate_venue and source_venue == candidate_venue:
        score += 1.5
        reasons.append("same venue")

    return score, reasons


def _print_similar_items(items: list[dict], long: bool = False, abstract_limit: int = 280):
    for item in items:
        print(f"# score={item['similarity_score']:.2f}")
        if item.get("similarity_reasons"):
            print(f"# why: {'; '.join(item['similarity_reasons'])}")
        print(_format_item_card(item, long=long, abstract_limit=abstract_limit))


def _openalex_authors_line(work: dict) -> str:
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name")
        if name:
            authors.append(name)
    return ", ".join(authors)


def _openalex_abstract(work: dict) -> str:
    inverted = work.get("abstract_inverted_index") or {}
    if not inverted:
        return ""
    pairs = []
    for token, positions in inverted.items():
        for position in positions:
            pairs.append((position, token))
    pairs.sort(key=lambda pair: pair[0])
    return " ".join(token for _, token in pairs)


def _print_openalex_items(items: list[dict], abstract_limit: int = 280):
    for item in items:
        print(f"# source=web provider=openalex")
        print(f"# score={item['similarity_score']:.2f}")
        if item.get("similarity_reasons"):
            print(f"# why: {'; '.join(item['similarity_reasons'])}")
        title = item.get("display_name", "?")
        year = item.get("publication_year") or ""
        authors = _openalex_authors_line(item)
        doi = item.get("doi") or ""
        print(f"[{item.get('id', '?')}] {authors} ({year}) {title}".strip())
        if doi:
            print(f"  doi: {doi}")
        abstract = _openalex_abstract(item)
        if abstract:
            print(f"  abstract: {_truncate(abstract, abstract_limit)}")


# ── Commands ──────────────────────────────────────────────


def cmd_search(args):
    """Search items by keyword."""
    queries = [args.query]
    if args.bilingual:
        queries = _expand_query(args.query)

    items = []
    for query in queries[: args.max_queries]:
        items.extend(_fetch_search_items(query, args))
    items = _filter_list_items(_dedupe_items(items), include_notes=args.include_notes)[: args.limit]

    if args.bilingual and len(queries) > 1:
        print(f"# bilingual query expansion: {' | '.join(queries[: args.max_queries])}")
    _print_items(items, long=args.long, abstract_limit=args.abstract_limit)


def cmd_abstract_search(args):
    """Search items by abstract content only."""
    queries = [args.query]
    if args.bilingual:
        queries = _expand_query(args.query)

    items = []
    for query in queries[: args.max_queries]:
        items.extend(_fetch_search_items(query, args))
    items = _filter_list_items(_dedupe_items(items), include_notes=False)
    items = _filter_items_by_abstract(items, queries[: args.max_queries])[: args.limit]

    if args.bilingual and len(queries) > 1:
        print(f"# bilingual query expansion: {' | '.join(queries[: args.max_queries])}")
    print("# filtered by abstract only")
    _print_items(items, long=args.long, abstract_limit=args.abstract_limit)


def cmd_similar(args):
    """Find similar articles for a given Zotero item."""
    source_item = _fetch_item(args.key)
    source_data = source_item["data"]
    queries = _candidate_queries_from_item(source_data, limit=args.query_count)

    search_args = argparse.Namespace(
        limit=args.candidate_limit,
        sort="dateModified",
        collection=args.collection,
    )
    candidates = []
    for query in queries:
        candidates.extend(_fetch_search_items(query, search_args))
    candidates = _filter_list_items(_dedupe_items(candidates), include_notes=False)

    ranked = []
    for candidate in candidates:
        candidate_key = candidate.get("key") or candidate.get("data", {}).get("key")
        if candidate_key == args.key:
            continue
        score, reasons = _similarity_score(source_data, candidate["data"])
        if score < args.min_score:
            continue
        candidate["similarity_score"] = score
        candidate["similarity_reasons"] = reasons
        ranked.append(candidate)

    ranked.sort(key=lambda item: (-item["similarity_score"], item["data"].get("date", ""), item["data"].get("title", "")))
    ranked = ranked[: args.limit]

    print(f"# source: {source_data.get('title', '')}")
    if queries:
        print(f"# candidate queries: {' | '.join(queries)}")
    if not ranked:
        print("No similar items found.")
        return
    _print_similar_items(ranked, long=args.long, abstract_limit=args.abstract_limit)


def cmd_web_similar(args):
    """Find similar articles on the web using public scholarly APIs."""
    source_item = _fetch_item(args.key)
    source_data = source_item["data"]
    title = source_data.get("title", "").strip()
    keywords = _keywords_from_item(source_data, limit=max(args.query_count - 1, 0))
    query_parts = [title] if title else []
    query_parts.extend(keywords[: max(args.query_count - len(query_parts), 0)])
    search_query = " ".join(query_parts).strip()
    if not search_query:
        print("Source item does not have enough metadata to build a web query.", file=sys.stderr)
        sys.exit(1)

    response = _fetch_openalex_works(search_query, per_page=args.candidate_limit, mailto=args.mailto)
    works = response.get("results", [])
    ranked = []
    for work in works:
        candidate_data = {
            "title": work.get("display_name", ""),
            "abstractNote": _openalex_abstract(work),
            "creators": [
                {
                    "name": authorship.get("author", {}).get("display_name", "")
                }
                for authorship in work.get("authorships", [])
                if authorship.get("author", {}).get("display_name")
            ],
            "date": str(work.get("publication_year") or ""),
            "DOI": work.get("doi") or "",
            "publicationTitle": work.get("primary_location", {}).get("source", {}).get("display_name", ""),
            "tags": [],
        }
        score, reasons = _similarity_score(source_data, candidate_data)
        if score < args.min_score:
            continue
        work["similarity_score"] = score
        work["similarity_reasons"] = reasons
        ranked.append(work)

    ranked.sort(key=lambda work: (-work["similarity_score"], str(work.get("publication_year") or ""), work.get("display_name", "")))
    ranked = ranked[: args.limit]

    print(f"# source: {source_data.get('title', '')}")
    print(f"# web query: {search_query}")
    if not ranked:
        print("No web-similar items found.")
        return
    _print_openalex_items(ranked, abstract_limit=args.abstract_limit)


def cmd_collections(args):
    """List all collections."""
    cols = _fetch_collections()
    if args.tree:
        by_parent = {}
        for collection in cols:
            parent = collection["data"].get("parentCollection") or None
            by_parent.setdefault(parent, []).append(collection)
        for siblings in by_parent.values():
            siblings.sort(key=lambda c: c["data"]["name"].lower())

        def walk(parent: str | None, indent: int):
            for collection in by_parent.get(parent, []):
                data = collection["data"]
                meta = collection["meta"]
                prefix = "  " * indent + "- "
                print(f'{prefix}[{collection["key"]}] {data["name"]} ({meta["numItems"]} items)')
                walk(collection["key"], indent + 1)

        walk(None, 0)
        return

    for collection in cols:
        data = collection["data"]
        meta = collection["meta"]
        parent = data.get("parentCollection") or "—"
        print(f'[{collection["key"]}] {data["name"]}  ({meta["numItems"]} items, parent: {parent})')


def cmd_item(args):
    """Get full metadata for a single item."""
    item = _fetch_item(args.key)
    data = item["data"]

    print(f"Key:      {data['key']}")
    print(f"Type:     {data['itemType']}")
    print(f"Title:    {data.get('title', '')}")

    authors = _authors_line(data)
    if authors:
        print(f"Authors:  {authors}")

    extra_fields = (
        ("date", "Date"),
        ("publicationTitle", "Venue"),
        ("proceedingsTitle", "Proceedings"),
        ("bookTitle", "Book"),
        ("DOI", "DOI"),
        ("url", "URL"),
        ("language", "Language"),
    )
    for field, label in extra_fields:
        value = data.get(field)
        if value:
            print(f"{label}:  {value}")

    abstract = _strip_html(data.get("abstractNote", ""))
    if abstract:
        print(f"Abstract:  {abstract}")

    tags = [tag["tag"] for tag in data.get("tags", []) if tag.get("tag")]
    if tags:
        print(f"Tags:     {', '.join(tags)}")

    collections = data.get("collections", [])
    if collections:
        print(f"Collections: {', '.join(collections)}")

    print(f"Added:    {data.get('dateAdded', '?')}")
    print(f"Modified: {data.get('dateModified', '?')}")


def cmd_children(args):
    """List children (attachments/notes) of an item."""
    children = _fetch_children(args.key)
    for child in children:
        data = child["data"]
        title = data.get("title") or data.get("filename") or "?"
        print(f'[{child["key"]}] {data["itemType"]}: {title}')
        if data.get("filename"):
            print(f"  filename: {data['filename']}")
        if data.get("contentType"):
            print(f"  type: {data['contentType']}")
        if data.get("linkMode"):
            print(f"  linkMode: {data['linkMode']}")
        if data["itemType"] == "note":
            print(f"  note: {_render_note(child, limit=args.note_limit, full=args.full_notes)}")


def cmd_pdf(args):
    """Find local PDF path for an item."""
    children = _fetch_children(args.key)
    for child in children:
        data = child["data"]
        if data.get("contentType") == "application/pdf":
            path = _resolve_attachment_path(child)
            if path:
                print(path)
                return
            print(f'PDF attachment found but local path is unavailable for [{child["key"]}]', file=sys.stderr)
            sys.exit(1)
    print("No PDF attachment found.", file=sys.stderr)
    sys.exit(1)


def cmd_recent(args):
    """List recently added/modified items."""
    params = {
        "itemType": "-attachment",
        "limit": str(args.limit),
        "sort": "dateModified",
        "direction": "desc",
    }
    items = _get(_url("items", params))
    items = _filter_list_items(items, include_notes=args.include_notes)
    _print_items(items, long=args.long, abstract_limit=args.abstract_limit)


def cmd_collection_items(args):
    """List items in a specific collection."""
    params = {
        "itemType": "-attachment",
        "limit": str(args.limit),
        "sort": args.sort,
        "direction": args.direction,
    }
    items = _get(_url(f"collections/{args.key}/items", params))
    items = _filter_list_items(items, include_notes=args.include_notes)
    _print_items(items, long=args.long, abstract_limit=args.abstract_limit)


def cmd_notes(args):
    """Print clean note contents for an item."""
    children = _fetch_children(args.key)
    notes = [child for child in children if child["data"]["itemType"] == "note"]
    if not notes:
        print("No notes found.")
        return

    for note in notes:
        title = note["data"].get("title") or "(untitled note)"
        print(f'[{note["key"]}] {title}')
        print(_render_note(note, limit=args.limit, full=args.full))
        print()


def cmd_attachments(args):
    """List attachments with resolved local paths when available."""
    children = _fetch_children(args.key)
    attachments = [child for child in children if child["data"]["itemType"] == "attachment"]
    if not attachments:
        print("No attachments found.")
        return

    for attachment in attachments:
        data = attachment["data"]
        title = data.get("title") or data.get("filename") or "(untitled attachment)"
        print(f'[{attachment["key"]}] {title}')
        if data.get("filename"):
            print(f"  filename: {data['filename']}")
        if data.get("contentType"):
            print(f"  type: {data['contentType']}")
        if data.get("linkMode"):
            print(f"  linkMode: {data['linkMode']}")
        path = _resolve_attachment_path(attachment)
        if path:
            print(f"  path: {path}")
        else:
            print("  path: (unavailable)")


def cmd_abstract(args):
    """Print abstract only."""
    item = _fetch_item(args.key)
    abstract = _strip_html(item["data"].get("abstractNote", ""))
    if not abstract:
        print("No abstract found.")
        return
    if not args.full:
        abstract = _truncate(abstract, args.limit)
    print(abstract)


def cmd_overview(args):
    """Human-friendly overview for a single item."""
    item = _fetch_item(args.key)
    data = item["data"]
    children = _fetch_children(args.key)
    collection_names = _collection_name_map()

    print(f"Title:     {data.get('title', '')}")
    authors = _authors_line(data)
    if authors:
        print(f"Authors:   {authors}")
    year = _item_year(data)
    if year:
        print(f"Year:      {year}")
    venue = data.get("publicationTitle") or data.get("proceedingsTitle") or data.get("bookTitle")
    if venue:
        print(f"Venue:     {venue}")
    if data.get("DOI"):
        print(f"DOI:       {data['DOI']}")
    if data.get("url"):
        print(f"URL:       {data['url']}")

    collections = [collection_names.get(key, key) for key in data.get("collections", [])]
    if collections:
        print(f"Collections: {', '.join(collections)}")

    tags = [tag["tag"] for tag in data.get("tags", []) if tag.get("tag")]
    if tags:
        print(f"Tags:      {', '.join(tags)}")

    abstract = _strip_html(data.get("abstractNote", ""))
    if abstract:
        print()
        print("Abstract")
        print(abstract if args.full_abstract else _truncate(abstract, args.abstract_limit))

    attachments = [child for child in children if child["data"]["itemType"] == "attachment"]
    notes = [child for child in children if child["data"]["itemType"] == "note"]

    if attachments:
        print()
        print("Attachments")
        for attachment in attachments:
            attachment_data = attachment["data"]
            parts = [
                f'[{attachment["key"]}]',
                attachment_data.get("filename") or attachment_data.get("title") or "(unnamed)",
            ]
            if attachment_data.get("contentType"):
                parts.append(attachment_data["contentType"])
            path = _resolve_attachment_path(attachment)
            if path:
                parts.append(path)
            print(" | ".join(parts))

    if notes:
        print()
        print("Notes")
        for note in notes[: args.note_count]:
            print(f'[{note["key"]}] {_render_note(note, limit=args.note_limit, full=args.full_notes)}')


# ── Main ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Zotero local API helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    search = sub.add_parser("search", help="Search items by keyword")
    search.add_argument("query")
    search.add_argument("-n", "--limit", type=int, default=10)
    search.add_argument("-c", "--collection", default=None, help="Collection key to search within")
    search.add_argument("-s", "--sort", default=None)
    search.add_argument("--long", action="store_true", help="Show richer item cards")
    search.add_argument("--abstract-limit", type=int, default=280)
    search.add_argument("--no-bilingual", dest="bilingual", action="store_false", help="Disable bilingual query expansion")
    search.add_argument("--max-queries", type=int, default=4, help="Max bilingual query variants to issue")
    search.add_argument("--include-notes", action="store_true", help="Include note items in search results")
    search.set_defaults(bilingual=True)

    abstract_search = sub.add_parser("abstract-search", help="Search items by abstract content only")
    abstract_search.add_argument("query")
    abstract_search.add_argument("-n", "--limit", type=int, default=10)
    abstract_search.add_argument("-c", "--collection", default=None, help="Collection key to search within")
    abstract_search.add_argument("-s", "--sort", default=None)
    abstract_search.add_argument("--long", action="store_true", help="Show richer item cards")
    abstract_search.add_argument("--abstract-limit", type=int, default=280)
    abstract_search.add_argument("--no-bilingual", dest="bilingual", action="store_false", help="Disable bilingual query expansion")
    abstract_search.add_argument("--max-queries", type=int, default=4, help="Max bilingual query variants to issue")
    abstract_search.set_defaults(bilingual=True)

    similar = sub.add_parser("similar", help="Find similar articles for a given item")
    similar.add_argument("key")
    similar.add_argument("-n", "--limit", type=int, default=5)
    similar.add_argument("-c", "--collection", default=None, help="Collection key to search within")
    similar.add_argument("--candidate-limit", type=int, default=20, help="How many candidates to fetch per seed query")
    similar.add_argument("--query-count", type=int, default=6, help="How many seed queries to derive from the source item")
    similar.add_argument("--min-score", type=float, default=1.0, help="Minimum similarity score to keep")
    similar.add_argument("--long", action="store_true", help="Show richer item cards")
    similar.add_argument("--abstract-limit", type=int, default=280)

    web_similar = sub.add_parser("web-similar", help="Find similar articles on the web with OpenAlex")
    web_similar.add_argument("key")
    web_similar.add_argument("-n", "--limit", type=int, default=5)
    web_similar.add_argument("--candidate-limit", type=int, default=10, help="How many web candidates to fetch")
    web_similar.add_argument("--query-count", type=int, default=6, help="How many seed keywords to derive from the source item")
    web_similar.add_argument("--min-score", type=float, default=1.0, help="Minimum similarity score to keep")
    web_similar.add_argument("--abstract-limit", type=int, default=280)
    web_similar.add_argument("--mailto", default=None, help="Optional contact email for OpenAlex polite pool")

    collections = sub.add_parser("collections", help="List all collections")
    collections.add_argument("--tree", action="store_true", help="Render collections as a tree")

    item = sub.add_parser("item", help="Get item metadata")
    item.add_argument("key")

    children = sub.add_parser("children", help="List attachments/notes of an item")
    children.add_argument("key")
    children.add_argument("--full-notes", action="store_true", help="Print full note content")
    children.add_argument("--note-limit", type=int, default=500)

    pdf = sub.add_parser("pdf", help="Get local PDF path for an item")
    pdf.add_argument("key")

    recent = sub.add_parser("recent", help="List recently modified items")
    recent.add_argument("-n", "--limit", type=int, default=10)
    recent.add_argument("--long", action="store_true", help="Show richer item cards")
    recent.add_argument("--abstract-limit", type=int, default=280)
    recent.add_argument("--include-notes", action="store_true", help="Include note items in results")

    collection_items = sub.add_parser("collection-items", help="List items in a collection")
    collection_items.add_argument("key")
    collection_items.add_argument("-n", "--limit", type=int, default=20)
    collection_items.add_argument("-s", "--sort", default="dateModified")
    collection_items.add_argument("-d", "--direction", default="desc", choices=("asc", "desc"))
    collection_items.add_argument("--long", action="store_true", help="Show richer item cards")
    collection_items.add_argument("--abstract-limit", type=int, default=280)
    collection_items.add_argument("--include-notes", action="store_true", help="Include note items in results")

    notes = sub.add_parser("notes", help="Show cleaned note content for an item")
    notes.add_argument("key")
    notes.add_argument("--full", action="store_true", help="Show full notes")
    notes.add_argument("--limit", type=int, default=1200)

    attachments = sub.add_parser("attachments", help="List attachments and resolved local paths")
    attachments.add_argument("key")

    abstract = sub.add_parser("abstract", help="Show abstract only")
    abstract.add_argument("key")
    abstract.add_argument("--full", action="store_true", help="Show full abstract")
    abstract.add_argument("--limit", type=int, default=2000)

    overview = sub.add_parser("overview", help="Show a human-friendly article overview")
    overview.add_argument("key")
    overview.add_argument("--full-abstract", action="store_true", help="Show full abstract")
    overview.add_argument("--abstract-limit", type=int, default=1600)
    overview.add_argument("--full-notes", action="store_true", help="Show full note excerpts")
    overview.add_argument("--note-limit", type=int, default=500)
    overview.add_argument("--note-count", type=int, default=3)

    args = parser.parse_args()
    {
        "search": cmd_search,
        "abstract-search": cmd_abstract_search,
        "similar": cmd_similar,
        "web-similar": cmd_web_similar,
        "collections": cmd_collections,
        "item": cmd_item,
        "children": cmd_children,
        "pdf": cmd_pdf,
        "recent": cmd_recent,
        "collection-items": cmd_collection_items,
        "notes": cmd_notes,
        "attachments": cmd_attachments,
        "abstract": cmd_abstract,
        "overview": cmd_overview,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
