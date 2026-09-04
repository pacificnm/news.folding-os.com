const OpenAI = require('openai');
const config = require('../config');

const MAX_INPUT_CHARS = 12000;

function truncate(text, max = MAX_INPUT_CHARS) {
  const s = String(text || '');
  return s.length > max ? s.slice(0, max) + '…' : s;
}

function buildClient() {
  if (!config.openaiApiKey) return null;
  return new OpenAI({ apiKey: config.openaiApiKey });
}

function notConfigured() {
  return { error: 'AI_NOT_CONFIGURED', message: 'Set OPENAI_API_KEY to enable AI features.' };
}

function parseJson(text) {
  // Strip possible code fences and parse.
  const cleaned = String(text || '')
    .replace(/^```(?:json)?/i, '')
    .replace(/```$/i, '')
    .trim();
  return JSON.parse(cleaned);
}

/**
 * Summarize an article.
 * @param {{ title:string, description?:string, contentHtml?:string }} article
 * @returns {Promise<{summary:string, keyPoints:string[]}|{error:string}>}
 */
async function summarize(article) {
  const client = buildClient();
  if (!client) return notConfigured();

  const input = truncate(
    `Title: ${article.title}\n\n${article.description || ''}\n\n${article.contentHtml || ''}`
  );

  const res = await client.chat.completions.create({
    model: config.openaiModel,
    temperature: 0.3,
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content:
          'You are a news analyst. Return JSON with fields: "summary" (2-3 sentence summary) and "keyPoints" (array of 3-5 short strings).',
      },
      { role: 'user', content: input },
    ],
  });

  const data = parseJson(res.choices[0].message.content);
  return {
    summary: data.summary || '',
    keyPoints: Array.isArray(data.keyPoints) ? data.keyPoints : [],
  };
}

/**
 * Research an article: entities, claims, context, related topics, open questions.
 * @param {{ title:string, description?:string, contentHtml?:string }} article
 * @returns {Promise<object>}
 */
async function research(article) {
  const client = buildClient();
  if (!client) return notConfigured();

  const input = truncate(
    `Title: ${article.title}\n\n${article.description || ''}\n\n${article.contentHtml || ''}`
  );

  const res = await client.chat.completions.create({
    model: config.openaiModel,
    temperature: 0.4,
    response_format: { type: 'json_object' },
    messages: [
      {
        role: 'system',
        content:
          'You are a research analyst. Return JSON with fields: "entities" (array of {name, type}), ' +
          '"claims" (array of short strings), "context" (string), ' +
          '"relatedTopics" (array of strings), "openQuestions" (array of strings).',
      },
      { role: 'user', content: input },
    ],
  });

  const data = parseJson(res.choices[0].message.content);
  return {
    entities: Array.isArray(data.entities) ? data.entities : [],
    claims: Array.isArray(data.claims) ? data.claims : [],
    context: data.context || '',
    relatedTopics: Array.isArray(data.relatedTopics) ? data.relatedTopics : [],
    openQuestions: Array.isArray(data.openQuestions) ? data.openQuestions : [],
  };
}

module.exports = { summarize, research, notConfigured, truncate };
