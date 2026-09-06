import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
const digest = data => createHash('sha256').update(data).digest('hex');
const manifest = JSON.parse(await readFile(resolve(root, 'packed-assets/manifest.json'), 'utf8'));
for (const asset of manifest) {
  const target = resolve(root, asset.path);
  try { if (digest(await readFile(target)) === asset.sha256) continue; } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const compressed = Buffer.concat(await Promise.all(asset.parts.map(part => readFile(resolve(root, part)))));
  const data = gunzipSync(compressed);
  if (digest(data) !== asset.sha256) throw new Error('Asset checksum mismatch: ' + asset.path);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, data);
  console.log('Restored ' + asset.path);
}
