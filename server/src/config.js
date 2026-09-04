require('dotenv').config();

function int(value, fallback) {
  const n = parseInt(value, 10);
  return Number.isFinite(n) ? n : fallback;
}

const config = {
  port: int(process.env.PORT, 4000),
  openaiApiKey: process.env.OPENAI_API_KEY || '',
  openaiModel: process.env.OPENAI_MODEL || 'gpt-4o-mini',
  cacheTtlMs: int(process.env.CACHE_TTL_MS, 60000),
  dbPath: process.env.DB_PATH || './data/news.db',
};

module.exports = config;
