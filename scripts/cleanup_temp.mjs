import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const entries = fs.readdirSync(root, { withFileTypes: true });

for (const entry of entries) {
  if (entry.isDirectory() && (entry.name.startsWith('.tmp_cdp_') || entry.name === '.tmp_chrome_profile')) {
    const fullPath = path.join(root, entry.name);
    try {
      fs.rmSync(fullPath, { recursive: true, force: true });
      console.log('Removed:', entry.name);
    } catch (err) {
      console.warn('Could not remove:', entry.name, err.message);
    }
  }
}

const extractedImg = path.join(root, 'extracted_body_color.webp');
if (fs.existsSync(extractedImg)) {
  try {
    fs.unlinkSync(extractedImg);
    console.log('Removed extracted_body_color.webp');
  } catch (err) {
    console.warn('Could not remove extracted_body_color.webp', err.message);
  }
}
