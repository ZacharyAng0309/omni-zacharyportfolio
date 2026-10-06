import fs from 'node:fs';
import { spawnSync } from 'node:child_process';

const files = fs.globSync('src/**/*.{ts,tsx}');
if (files.length === 0) {
  console.log('No files found to lint.');
  process.exit(0);
}

const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const res = spawnSync(npx, ['oxlint', '--no-ignore', ...files], { stdio: 'inherit', shell: true });
process.exit(res.status ?? 0);
