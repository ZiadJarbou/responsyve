import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {EventEmitter} from 'node:events';

test('signing key names stay in billing child and are removed from website child', () => {
  const env = {APPLICATION_PORT:'8080', REVIEWER_CREDENTIAL_SHA256:'test-hash', PLAY_HELPER_SHARED_SECRET:'synthetic-gateway-secret'};
  for (let i=1;i<=4;i++) {
    env['ENTITLEMENT_PRIVATE_KEY_B64_'+i]='test-canonical-'+i;
    env['ENTITLEMENT_PRIVATE_KEY_B64'+i]='test-saved-name-'+i;
  }
  const children=[];
  const source=readFileSync(new URL('./start-production.mjs',import.meta.url),'utf8').replace("import { spawn } from 'node:child_process';",'');
  runInNewContext(source, {
    process:{env,execPath:'/node',on(){},exit(){}}, console,
    spawn(command,args,options){children.push({command,args,options});return new EventEmitter();},
    setTimeout,clearTimeout,
  });
  assert.equal(children.length,2);
  assert.deepEqual(children[0].options.env,env);
  const website=children[1].options.env;
  assert.equal(website.APPLICATION_PORT,'8080');
  assert.equal(website.REVIEWER_CREDENTIAL_SHA256,undefined);
  assert.equal(website.PLAY_HELPER_SHARED_SECRET,undefined);
  for (const name of Object.keys(env).filter(name=>name.startsWith('ENTITLEMENT_PRIVATE_KEY_B64'))) assert.equal(website[name],undefined);
});
