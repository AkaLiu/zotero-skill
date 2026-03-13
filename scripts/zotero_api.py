#!/usr/bin/env python3
"""Zotero Local API helper — query items, collections, and locate PDFs."""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import os

BASE = "http://localhost:23119/api"
# user id 0 is an alias for the current local user
USER_PATH = f"{BASE}/users/0"


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


# ── Commands ──────────────────────────────────────────────


def cmd_search(args):
    """Search items by keyword."""
    params = {
        "q": args.query,
        "itemType": "-attachment",
        "limit": str(args.limit),
        "sort": args.sort or "dateModified",
        "direction": "desc",
    }
    if args.collection:
        path = f"collections/{args.collection}/items"
    else:
        path = "items"
    items = _get(_url(path, params))
    _print_items(items)


def cmd_collections(args):
    """List all collections."""
    cols = _get(_url("collections"))
    for c in cols:
        d = c["data"]
        m = c["meta"]
        parent = d.get("parentCollection") or "—"
        print(f'[{c["key"]}] {d["name"]}  ({m["numItems"]} items, parent: {parent})')


def cmd_item(args):
    """Get full metadata for a single item."""
    item = _get(_url(f"items/{args.key}"))
    d = item["data"]
    meta = item.get("meta", {})

    print(f"Key:      {d['key']}")
    print(f"Type:     {d['itemType']}")
    print(f"Title:    {d['title']}")

    creators = d.get("creators", [])
    if creators:
        names = [f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() for c in creators]
        print(f"Authors:  {', '.join(names)}")

    for field in ("date", "DOI", "url", "abstractNote", "publicationTitle", "language"):
        val = d.get(field)
        if val:
            label = field[0].upper() + field[1:]
            if field == "abstractNote":
                label = "Abstract"
            print(f"{label}:  {val}")

    tags = [t["tag"] for t in d.get("tags", [])]
    if tags:
        print(f"Tags:     {', '.join(tags)}")

    cols = d.get("collections", [])
    if cols:
        print(f"Collections: {', '.join(cols)}")

    print(f"Added:    {d.get('dateAdded', '?')}")


def cmd_children(args):
    """List children (attachments/notes) of an item."""
    children = _get(_url(f"items/{args.key}/children"))
    for ch in children:
        d = ch["data"]
        print(f'[{ch["key"]}] {d["itemType"]}: {d.get("title", d.get("filename", "?"))}')
        if d.get("filename"):
            print(f"  filename: {d['filename']}")
        if d.get("contentType"):
            print(f"  type: {d['contentType']}")
        if d["itemType"] == "note":
            note = d.get("note", "")
            # strip HTML
            import re
            note_text = re.sub(r"<[^>]+>", "", note)
            if len(note_text) > 500:
                note_text = note_text[:500] + "..."
            print(f"  note: {note_text}")


def cmd_pdf(args):
    """Find local PDF path for an item."""
    children = _get(_url(f"items/{args.key}/children"))
    for ch in children:
        d = ch["data"]
        if d.get("contentType") == "application/pdf" and d.get("filename"):
            storage_key = ch["key"]
            # Zotero stores attachments at ~/Zotero/storage/<KEY>/<filename>
            zotero_dir = os.path.expanduser("~/Zotero/storage")
            pdf_path = os.path.join(zotero_dir, storage_key, d["filename"])
            if os.path.exists(pdf_path):
                print(pdf_path)
            else:
                # try enclosure link
                enc = ch.get("links", {}).get("enclosure", {})
                href = enc.get("href", "")
                if href.startswith("file://"):
                    fpath = urllib.parse.unquote(href[7:])
                    print(fpath)
                else:
                    print(f"PDF not found locally for {storage_key}", file=sys.stderr)
            return
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
    _print_items(items)


def cmd_collection_items(args):
    """List items in a specific collection."""
    params = {
        "itemType": "-attachment",
        "limit": str(args.limit),
        "sort": "dateModified",
        "direction": "desc",
    }
    items = _get(_url(f"collections/{args.key}/items", params))
    _print_items(items)


# ── Helpers ───────────────────────────────────────────────


def _print_items(items):
    for item in items:
        d = item["data"]
        creators = d.get("creators", [])
        first_author = ""
        if creators:
            first_author = creators[0].get("lastName", "")
            if len(creators) > 1:
                first_author += " et al."
        year = (d.get("date") or "")[:4]
        title = d.get("title", "?")
        itype = d.get("itemType", "?")
        print(f'[{item["key"]}] ({itype}) {first_author} ({year}) {title}')


# ── Main ──────────────────────────────────────────────────


def main():
    p = argparse.ArgumentParser(description="Zotero local API helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Search items by keyword")
    s.add_argument("query")
    s.add_argument("-n", "--limit", type=int, default=10)
    s.add_argument("-c", "--collection", default=None, help="Collection key to search within")
    s.add_argument("-s", "--sort", default=None)

    sub.add_parser("collections", help="List all collections")

    s = sub.add_parser("item", help="Get item metadata")
    s.add_argument("key")

    s = sub.add_parser("children", help="List attachments/notes of an item")
    s.add_argument("key")

    s = sub.add_parser("pdf", help="Get local PDF path for an item")
    s.add_argument("key")

    s = sub.add_parser("recent", help="List recently modified items")
    s.add_argument("-n", "--limit", type=int, default=10)

    s = sub.add_parser("collection-items", help="List items in a collection")
    s.add_argument("key")
    s.add_argument("-n", "--limit", type=int, default=20)

    args = p.parse_args()
    {
        "search": cmd_search,
        "collections": cmd_collections,
        "item": cmd_item,
        "children": cmd_children,
        "pdf": cmd_pdf,
        "recent": cmd_recent,
        "collection-items": cmd_collection_items,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
