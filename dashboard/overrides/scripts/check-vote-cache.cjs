// Run against a local production server or the deployed app. Supply at least
// one default-language and one prefixed-language vote URL.
const assert = require('node:assert/strict');

async function main() {
  const urls = process.argv.slice(2);
  assert.ok(urls.length >= 2, 'Supply a default-language vote URL and a prefixed-language vote URL');
  for (const value of urls) {
    const url = new URL(value);
    for (const layout of [null, 'party-first']) {
      if (layout) url.searchParams.set('layout', layout);
      const responses = [];
      for (let i = 0; i < 3; i++) {
        const response = await fetch(url);
        await response.arrayBuffer();
        assert.equal(response.status, 200, `${url}: expected a published vote`);
        responses.push(response);
      }
      const last = responses.at(-1);
      const nextCache = last.headers.get('x-nextjs-cache');
      const edgeCache = last.headers.get('x-vercel-cache');
      const control = last.headers.get('cache-control') || '';
      assert.ok(nextCache === 'HIT' || edgeCache === 'HIT', `${url}: no cache hit after warming`);
      assert.ok(!/private|no-store/.test(control), `${url}: uncached response (${control})`);
      console.log(JSON.stringify({ url: String(url), nextCache, edgeCache, cacheControl: control }));
    }
  }
}

main().catch((error) => { console.error(error.message); process.exitCode = 1; });
