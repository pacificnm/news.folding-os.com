const config = require('./config');
const { createApp } = require('./app');
const { closeDb } = require('./services/store');

const app = createApp();

const server = app.listen(config.port, () => {
  console.log(`[server] listening on http://localhost:${config.port}`);
});

function shutdown(signal) {
  console.log(`[server] ${signal} received, shutting down`);
  server.close(() => {
    closeDb();
    process.exit(0);
  });
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

module.exports = { server };
