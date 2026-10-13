const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const ts = require('typescript');

const source = fs.readFileSync(path.join(__dirname, '../src/lib/vote-events.ts'), 'utf8');
const code = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const api = {};
new Function('exports', 'require', code)(api, (id) => {
  if (id === 'react') return { cache: (fn) => fn };
  if (id === './city.config') return { getCityConfig: (city) => ({ dataBase: `https://data.test/${city}/analyses` }) };
  throw new Error(`Unexpected dependency: ${id}`);
});

const event = { id: 'bratislava:vote-event:example', votes: [{ voter_id: 'person:1', option: 'yes' }] };
function responses(routes) {
  const calls = [];
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    const value = routes[url];
    return { ok: value !== undefined, status: value === undefined ? 404 : 200, json: async () => value };
  };
  return calls;
}

test('one vote request fetches exactly one cacheable artifact', async () => {
  const calls = responses({ 'https://data.test/bratislava/data/dashboard/vote-events/example.json': event });
  assert.deepEqual(await api.getCityVoteEvent('bratislava', event.id), event);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].options.next.revalidate, 3600);
  assert.ok(!calls[0].url.endsWith('votes.csv'));
});

test('short and encoded canonical IDs resolve the same event', async () => {
  responses({ 'https://data.test/bratislava/data/dashboard/vote-events/example.json': event });
  assert.deepEqual(await api.getCityVoteEvent('bratislava', 'example'), event);
  assert.deepEqual(await api.getCityVoteEvent('bratislava', encodeURIComponent(event.id)), event);
});

test('invalid, cross-city and traversal IDs cause no network requests', async () => {
  const calls = responses({});
  for (const id of ['../example', '%2fexample', '..', '.', '%', 'kosice:vote-event:example']) {
    assert.equal(await api.getCityVoteEvent('bratislava', id), null);
  }
  assert.equal(calls.length, 0);
});

test('missing and mismatched records return a 404 result', async () => {
  responses({ 'https://data.test/bratislava/data/dashboard/vote-events/example.json': { ...event, id: 'wrong' } });
  assert.equal(await api.getCityVoteEvent('bratislava', 'missing'), null);
  assert.equal(await api.getCityVoteEvent('bratislava', 'example'), null);
});

test('index reads only small summary shards, never full ballots', async () => {
  const base = 'https://data.test/bratislava/data/dashboard';
  const calls = responses({
    [`${base}/index.json`]: { version: 1, count: 2, pages: ['summaries/0000.json', 'summaries/0001.json'] },
    [`${base}/summaries/0000.json`]: [{ id: 'one' }],
    [`${base}/summaries/0001.json`]: [{ id: 'two' }],
  });
  assert.deepEqual(await api.getCityVoteEvents('bratislava'), [{ id: 'one' }, { id: 'two' }]);
  assert.equal(calls.length, 3);
  assert.ok(calls.every((call) => call.options.next.revalidate === 3600));
});

test('upstream failures and unsafe index paths fail visibly', async () => {
  global.fetch = async () => ({ ok: false, status: 503 });
  await assert.rejects(api.getCityVoteEvent('bratislava', 'example'), /503/);
  await assert.rejects(api.getCityVoteEvents('bratislava'), /503/);
  responses({ 'https://data.test/bratislava/data/dashboard/index.json': { version: 1, pages: ['../votes.csv'] } });
  await assert.rejects(api.getCityVoteEvents('bratislava'), /Invalid/);
});
