# news.folding-os.com

A Google News–style aggregator that pulls articles from multiple sources and uses
AI to summarize and research each one.

## Stack
- **Backend:** Node.js + Express
- **Frontend:** Vite + React + Tailwind CSS
- **AI:** OpenAI (swappable behind an interface)
- **Data:** LRU cache + JSON file store (persisted AI results)

## Features
- Multi-source news feed (RSS) with category filters and search
- AI **summary** per article (short summary + key points)
- AI **research** per article (entities, claims, context, related topics)
- Caching so repeated views don't re-call the model
- Responsive, mobile-first UI

## Architecture
```
React UI ──▶ Express API ──▶ NewsSource(s)  (RSS, pluggable)
                  │
                  └──────▶ AI service (summarize / research)
                              └── LRU cache + JSON file store
```

## Getting started
```bash
cp .env.example .env          # add OPENAI_API_KEY
npm install                   # installs workspaces (server + client)
npm run dev                   # runs server + client concurrently
```
- API: http://localhost:4000/api
- UI: http://localhost:5173

## API
| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/news?category=&q=&limit=` | List articles |
| GET | `/api/news/:id` | Single article |
| GET | `/api/news/:id/summarize` | AI summary |
| GET | `/api/news/:id/research` | AI research |

## Project layout
```
server/   Express API, news sources, AI service, cache, JSON store
client/   Vite + React + Tailwind UI
```

## Roadmap
- [x] Plan
- [x] Repo scaffolding (workspaces, env, gitignore)
- [x] Express skeleton + health check
- [x] RSS news source + feed/search endpoints
- [x] AI summarize + research endpoints (cached)
- [x] React UI: feed, filters, search, article view
- [x] Polish: error states, rate limiting, responsive pass
