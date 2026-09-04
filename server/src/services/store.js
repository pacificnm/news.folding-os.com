const fs = require('fs');
const path = require('path');

let dbPath = null;
let cache = null; // in-memory map: `${articleId}|${kind}` -> payload

function load(dbPathArg) {
  const p = dbPathArg || './data/ai-results.json';
  dbPath = p;
  const dir = path.dirname(p);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (fs.existsSync(p)) {
    try {
      cache = JSON.parse(fs.readFileSync(p, 'utf8'));
    } catch {
      cache = {};
    }
  } else {
    cache = {};
  }
  return cache;
}

function persist() {
  if (!dbPath) return;
  const dir = path.dirname(dbPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(dbPath, JSON.stringify(cache, null, 2));
}

function getAiResult(articleId, kind) {
  if (!cache) load();
  return cache[`${articleId}|${kind}`] || null;
}

function setAiResult(articleId, kind, payload) {
  if (!cache) load();
  cache[`${articleId}|${kind}`] = { payload, createdAt: new Date().toISOString() };
  persist();
}

function closeDb() {
  // Nothing to close for a file-backed store; data is already persisted on write.
}

module.exports = { getAiResult, setAiResult, closeDb };
