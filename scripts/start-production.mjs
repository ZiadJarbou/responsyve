import { spawn } from 'node:child_process';

// One external port remains 8080. The verifier is reachable only over loopback.
const websiteEnv = {...process.env};
for (const key of ['ENTITLEMENT_PRIVATE_KEY_B64', 'ENTITLEMENT_PRIVATE_KEY_FILE', 'GOOGLE_SERVICE_ACCOUNT_B64', 'GOOGLE_APPLICATION_CREDENTIALS', 'REVIEWER_CREDENTIAL_SHA256']) delete websiteEnv[key];
for (const key of Object.keys(websiteEnv)) if (key.startsWith('ENTITLEMENT_PRIVATE_KEY_B64')) delete websiteEnv[key];
const processes = [
  spawn('/opt/billing-venv/bin/gunicorn', ['--chdir', '/app/billing', '--bind', '127.0.0.1:9001', '--workers', '1', '--threads', '2', '--timeout', '45', '--access-logfile', '/dev/null', 'app:create_app()'], {stdio: 'inherit', env: process.env}),
  spawn(process.execPath, ['.output/server/index.mjs'], {stdio: 'inherit', env: websiteEnv}),
];
let stopping = false;
function stop(code) {
  if (stopping) return;
  stopping = true;
  for (const child of processes) child.kill('SIGTERM');
  const timer = setTimeout(() => { for (const child of processes) child.kill('SIGKILL'); process.exit(code); }, 5000);
  Promise.all(processes.map(child => child.exitCode !== null ? Promise.resolve() : new Promise(resolve => child.once('exit', resolve))))
    .then(() => { clearTimeout(timer); process.exit(code); });
}
for (const child of processes) {
  child.on('error', () => { console.error('Production service could not start'); stop(1); });
  child.on('exit', code => { if (!stopping) stop(code === 0 ? 1 : code || 1); });
}
process.on('SIGTERM', () => stop(0));
process.on('SIGINT', () => stop(0));
