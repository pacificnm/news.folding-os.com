const { LRUCache } = require('lru-cache');

/**
 * Small LRU + TTL cache wrapper.
 * @param {{ ttlMs?: number, max?: number }} options
 */
function createCache({ ttlMs = 60000, max = 1000 } = {}) {
  const cache = new LRUCache({ max, ttl: ttlMs });
  return {
    get(key) {
      return cache.get(key);
    },
    set(key, value) {
      cache.set(key, value);
    },
    has(key) {
      return cache.has(key);
    },
    delete(key) {
      cache.delete(key);
    },
    clear() {
      cache.clear();
    },
  };
}

module.exports = { createCache };
