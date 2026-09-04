const express = require('express');
const cors = require('cors');
const newsRouter = require('./routes/news');
const { createRssSource } = require('./services/rssSource');
const { register } = require('./services/newsSource');

// Register the default RSS source once.
register(createRssSource());

function createApp() {
  const app = express();

  app.use(cors());
  app.use(express.json());

  app.get('/api/health', (req, res) => {
    res.json({ ok: true, service: 'news.folding-os.com' });
  });

  app.use('/api/news', newsRouter);

  // 404
  app.use((req, res) => {
    res.status(404).json({ error: 'NOT_FOUND', message: 'Route not found.' });
  });

  // Error handler
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ error: 'INTERNAL_ERROR', message: 'Something went wrong.' });
  });

  return app;
}

module.exports = { createApp };
