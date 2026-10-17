const ROUTES = new Map([
  ['/v1/subscription/verify', ['POST', '/v1/subscription/verify']],
  ['/billing/health', ['GET', '/health']],
  ['/billing/ready', ['GET', '/ready']],
]);
const headers = {'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'};
/** @param {number} status @param {string} message */
function error(status, message) { return new Response(JSON.stringify({error: message}), {status, headers}); }
/** @param {ReadableStream<Uint8Array> | null} stream @param {number} maximum @param {number} timeoutMs */
async function boundedBody(stream, maximum, timeoutMs) {
  if (!stream) return new Uint8Array();
  const reader = stream.getReader();
  let timer;
  const timeout = new Promise((_, reject) => { timer = setTimeout(() => { reader.cancel().catch(() => {}); reject(new Error('timeout')); }, timeoutMs); });
  const chunks = []; let size = 0;
  try {
    while (true) {
      const {done, value} = await Promise.race([reader.read(), timeout]);
      if (done) break;
      size += value.byteLength;
      if (size > maximum) { await reader.cancel(); throw new RangeError('body size'); }
      chunks.push(value);
    }
    return Buffer.concat(chunks, size);
  } finally { clearTimeout(timer); reader.releaseLock(); }
}

/** Fixed loopback destination; no client headers, query strings or cookies are forwarded.
 * @param {Request} request
 * @param {typeof fetch} transport
 */
export async function billingResponse(request, transport = fetch) {
  const url = new URL(request.url);
  const route = ROUTES.get(url.pathname);
  if (!route) return null;
  if (request.method !== route[0]) {
    const response = error(405, 'Method not allowed'); response.headers.set('Allow', route[0]); return response;
  }
  if (url.search) return error(400, 'Query parameters are not supported');
  let body;
  if (request.method === 'POST') {
    if (request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') return error(415, 'JSON required');
    const length = request.headers.get('content-length');
    if (length && (!/^\d+$/.test(length) || Number(length) > 8192)) return error(413, 'Request too large');
    try { body = await boundedBody(request.body, 8192, 5000); }
    catch (e) { return error(e instanceof RangeError ? 413 : 408, 'Request body rejected'); }
  }
  try {
    const upstream = await transport('http://127.0.0.1:9001' + route[1], {
      method: request.method, body, headers: request.method === 'POST' ? {'Content-Type': 'application/json'} : {},
      signal: AbortSignal.timeout(35000), redirect: 'error',
    });
    if (![200, 400, 413, 429, 503].includes(upstream.status)) return error(503, 'Verification temporarily unavailable');
    const bytes = await boundedBody(upstream.body, 32768, 35000);
    try { JSON.parse(new TextDecoder().decode(bytes)); } catch { return error(503, 'Verification temporarily unavailable'); }
    return new Response(bytes, {status: upstream.status, headers});
  } catch { return error(503, 'Verification temporarily unavailable'); }
}
