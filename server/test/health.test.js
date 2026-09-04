const request = require('supertest');
const { createApp } = require('../src/app');

describe('health', () => {
  test('GET /api/health returns ok', async () => {
    const app = createApp();
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.ok).toBe(true);
  });
});
