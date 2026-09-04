const express = require('express');
const rateLimit = require('express-rate-limit');
const { listAll } = require('../services/newsSource');
const { createCache } = require('../cache');
const { summarize, research } = require('../services/ai');
const { getAiResult, setAiResult } = require('../services/store');

const router = express.Router();

const feedCache = createCache({ ttlMs: 60000, max: 200 });
const aiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
});

function cacheKey(params) {
  return JSON.stringify({
    category: params.category || '',
    q: params.q || '',
    limit: params.limit || '',
  });
}

// GET /api/news?category=&q=&limit=
router.get('/', async (req, res, next) => {
  try {
    const { category, q } = req.query;
    const limit = Math.min(parseInt(req.query.limit, 10) || 100, 500);
    const key = cacheKey({ category, q, limit });

    let articles = feedCache.get(key);
    if (!articles) {
      articles = await listAll({ category, q, limit });
      feedCache.set(key, articles);
    }
    res.json({ articles });
  } catch (err) {
    next(err);
  }
});

// GET /api/news/:id
router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const articles = await listAll({ limit: 500 });
    const article = articles.find((a) => a.id === id || a.url === id);
    if (!article) {
      return res.status(404).json({ error: 'NOT_FOUND', message: 'Article not found.' });
    }
    res.json(article);
  } catch (err) {
    next(err);
  }
});

// GET /api/news/:id/summarize
router.get('/:id/summarize', aiLimiter, async (req, res, next) => {
  try {
    const { id } = req.params;
    const cached = getAiResult(id, 'summary');
    if (cached) return res.json(cached);

    const articles = await listAll({ limit: 500 });
    const article = articles.find((a) => a.id === id || a.url === id);
    if (!article) {
      return res.status(404).json({ error: 'NOT_FOUND', message: 'Article not found.' });
    }

    const result = await summarize(article);
    if (result.error) {
      return res.status(503).json(result);
    }
    setAiResult(id, 'summary', result);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

// GET /api/news/:id/research
router.get('/:id/research', aiLimiter, async (req, res, next) => {
  try {
    const { id } = req.params;
    const cached = getAiResult(id, 'research');
    if (cached) return res.json(cached);

    const articles = await listAll({ limit: 500 });
    const article = articles.find((a) => a.id === id || a.url === id);
    if (!article) {
      return res.status(404).json({ error: 'NOT_FOUND', message: 'Article not found.' });
    }

    const result = await research(article);
    if (result.error) {
      return res.status(503).json(result);
    }
    setAiResult(id, 'research', result);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

module.exports = router;
