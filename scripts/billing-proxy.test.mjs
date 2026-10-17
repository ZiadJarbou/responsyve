import {test} from 'node:test';
import assert from 'node:assert/strict';
import {billingResponse} from './billing-proxy.mjs';
const url = 'https://responsyve.co/v1/subscription/verify';
test('fixed destination and stripped client headers; uncached JSON response', async () => {
  const response = await billingResponse(new Request(url, {method:'POST',headers:{'Content-Type':'application/json','Cookie':'private','Authorization':'secret'},body:'{}'}), async (target, options) => {
    assert.equal(target,'http://127.0.0.1:9001/v1/subscription/verify');
    assert.deepEqual(options.headers,{'Content-Type':'application/json'});
    assert.equal(options.redirect,'error');
    return Response.json({active:false});
  });
  assert.equal(response.status,200);assert.equal(response.headers.get('cache-control'),'no-store');
  assert.deepEqual(await response.json(),{active:false});
});
test('wrong methods, query tokens and oversized bodies never reach upstream', async () => {
  const transport = () => {throw new Error('must not call');};
  assert.equal((await billingResponse(new Request(url),transport)).status,405);
  assert.equal((await billingResponse(new Request(url+'?token=secret',{method:'POST'}),transport)).status,400);
  assert.equal((await billingResponse(new Request(url,{method:'POST',body:'{}'}),transport)).status,415);
  assert.equal((await billingResponse(new Request(url,{method:'POST',headers:{'Content-Type':'application/json'},body:'x'.repeat(8193)}),transport)).status,413);
});
test('unavailable, redirects and malformed upstream never grant access', async () => {
  for (const transport of [async()=>{throw new Error('private error');},async()=>new Response('secret',{status:302}),async()=>new Response('<html>private error</html>')]) {
    const response=await billingResponse(new Request(url,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),transport);
    assert.equal(response.status,503);assert.equal((await response.text()).includes('private'),false);
  }
});
test('only mapped paths are intercepted; readiness preserves disabled status', async () => {
  assert.equal(await billingResponse(new Request('https://responsyve.co/')),null);
  const response=await billingResponse(new Request('https://responsyve.co/billing/ready'),async target=>{
    assert.equal(target,'http://127.0.0.1:9001/ready');return Response.json({configured:false},{status:503});
  });
  assert.equal(response.status,503);assert.deepEqual(await response.json(),{configured:false});
});
