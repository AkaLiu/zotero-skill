# Zotero Local API Reference

Base URL: `http://localhost:23119/api`
User path: `/users/0` (alias for current local user)

## Endpoints

### Items

| Endpoint | Description |
|---|---|
| `GET /users/0/items?q=KEYWORD&itemType=-attachment&limit=N` | Search items by keyword (exclude attachments) |
| `GET /users/0/items?itemType=-attachment&sort=dateModified&direction=desc&limit=N` | List recent items |
| `GET /users/0/items/KEY` | Get single item metadata |
| `GET /users/0/items/KEY/children` | Get attachments and notes for an item |

### Collections

| Endpoint | Description |
|---|---|
| `GET /users/0/collections` | List all collections |
| `GET /users/0/collections/KEY/items?itemType=-attachment` | List items in a collection |

### Tags

| Endpoint | Description |
|---|---|
| `GET /users/0/tags` | List all tags |

## Query Parameters

- `q` — Full-text search keyword
- `itemType` — Filter by type. Prefix `-` to exclude (e.g., `-attachment`)
- `limit` — Max results (default 25, max 100)
- `sort` — Sort field: `dateModified`, `dateAdded`, `title`, `creator`, `date`
- `direction` — `asc` or `desc`

## Item Data Fields

Key fields in `item.data`:
- `key`, `itemType`, `title`, `abstractNote`
- `creators` — Array of `{firstName, lastName, creatorType}`
- `date`, `DOI`, `url`, `language`, `publicationTitle`
- `tags` — Array of `{tag, type}`
- `collections` — Array of collection keys

Attachment-specific: `filename`, `contentType`, `linkMode`, `md5`

## PDF Storage

Zotero stores imported PDFs at: `~/Zotero/storage/<ATTACHMENT_KEY>/<filename>`

To find a PDF for item KEY:
1. `GET /users/0/items/KEY/children`
2. Find child where `contentType == "application/pdf"`
3. Path: `~/Zotero/storage/<child.key>/<child.data.filename>`
