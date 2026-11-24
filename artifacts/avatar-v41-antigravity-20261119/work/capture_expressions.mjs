import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(__dirname, '../../..');
const distDir = path.join(projectDir, 'dist');
const outWork = __dirname;

const MIME = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.glb': 'model/gltf-binary',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json',
};

function findBrowser() {
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
  ];
  const pwRoot = `${process.env.LOCALAPPDATA}\\ms-playwright`;
  if (fs.existsSync(pwRoot)) {
    for (const d of fs.readdirSync(pwRoot).filter((x) => /^chromium-\d+$/.test(x)).sort().reverse()) {
      candidates.push(path.join(pwRoot, d, 'chrome-win64', 'chrome.exe'));
    }
  }
  return candidates.find((c) => c && fs.existsSync(c)) ?? null;
}

const browserPath = findBrowser();
if (!browserPath) {
  console.error('No Chrome browser found');
  process.exit(1);
}

const server = http.createServer((req, res) => {
  let reqPath = (req.url || '/').split('?')[0];
  if (reqPath === '/') reqPath = '/index.html';
  const fp = path.join(distDir, reqPath);
  if (fs.existsSync(fp) && fs.statSync(fp).isFile()) {
    const ext = path.extname(fp).toLowerCase();
    if (reqPath === '/index.html') {
      const html = fs.readFileSync(fp, 'utf8').replace(/<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>/gi, '');
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(html);
    } else {
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
      fs.createReadStream(fp).pipe(res);
    }
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

const port = 4237;
await new Promise((r) => server.listen(port, '127.0.0.1', r));
const tempDir = fs.mkdtempSync(path.join(projectDir, '.tmp_cdp_expr_'));
const cdpPort = 9547;
const proc = spawn(
  browserPath,
  [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu-sandbox',
    '--enable-unsafe-swiftshader',
    '--disable-features=RendererCodeIntegrity',
    `--user-data-dir=${tempDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--window-size=900,900',
    `--remote-debugging-port=${cdpPort}`,
    'about:blank',
  ],
  { stdio: 'ignore' }
);

try {
  let connected = false;
  for (let i = 0; i < 80; i++) {
    await new Promise((r) => setTimeout(r, 200));
    try {
      const res = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
      if (res.ok) {
        connected = true;
        break;
      }
    } catch {}
  }
  if (!connected) throw new Error('CDP timeout');

  const tabRes = await fetch(`http://127.0.0.1:${cdpPort}/json/new?about:blank`, { method: 'PUT' });
  const tab = await tabRes.json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = rej;
  });

  let mid = 1;
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      const id = mid++;
      const h = (ev) => {
        const d = JSON.parse(ev.data);
        if (d.id === id) {
          ws.removeEventListener('message', h);
          resolve(d.result);
        }
      };
      ws.addEventListener('message', h);
      ws.send(JSON.stringify({ id, method, params }));
    });

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 900, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: `http://127.0.0.1:${port}/index.html` });

  // Wait for GLTF avatar loaded
  const t0 = Date.now();
  while (Date.now() - t0 < 25000) {
    const r = await send('Runtime.evaluate', {
      expression: `(() => { const sc = window.__sceneController; return Boolean(sc && sc.getGLTFFaceMesh() && (sc.getRenderer()?.info?.render?.frame ?? 0) >= 25); })()`,
      returnByValue: true,
    });
    if (r?.result?.value === true) break;
    await new Promise((r) => setTimeout(r, 200));
  }

  // Hide HUD overlays cleanly so we see unobstructed portrait close-ups across expressions & angles
  await send('Runtime.evaluate', {
    expression: `(() => {
      document.querySelectorAll('header, [data-testid="cinema-timeline-hud"], [data-testid="whisper-stage-hud"], [data-testid="spatial-stage-control-dock"], [data-testid="diegetic-hotspot-layer"]').forEach(el => { el.style.display = 'none'; });
      const sc = window.__sceneController;
      sc.setReducedMotion(true);
      sc.updateScroll(0.0);
      for (let i = 0; i < 6; i++) sc.animateTick(0.016);
      // Pause animation loop during deterministic static expression snapshot rendering so rAF does not overwrite injected morphs
      sc.getRenderer().setAnimationLoop(null);
    })()`,
  });

  const views = [
    { name: 'expr_front_neutral', yawDeg: 0, pitchDeg: 0, morphs: {} },
    { name: 'expr_full_blink', yawDeg: 0, pitchDeg: 0, morphs: { eyeBlinkLeft: 1.0, eyeBlinkRight: 1.0 } },
    { name: 'expr_speech_aa', yawDeg: 0, pitchDeg: 0, morphs: { jawOpen: 0.45, viseme_aa: 0.65, mouthOpen: 0.35 } },
    { name: 'expr_smile_yaw', yawDeg: -14, pitchDeg: 0, morphs: { mouthSmileLeft: 0.35, mouthSmileRight: 0.35, browInnerUp: 0.20 }, headYaw: 0.14 },
    { name: 'expr_quarter_34', yawDeg: -34, pitchDeg: 2, morphs: {} },
    { name: 'expr_side_profile', yawDeg: -82, pitchDeg: 0, morphs: {} },
  ];

  for (const v of views) {
    await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        const rig = sc.getAvatarRig();
        const neckBone = rig.getObjectByName('Neck');
        const headBone = rig.getObjectByName('Head');
        const neckWorld = new THREE.Vector3();
        neckBone.getWorldPosition(neckWorld);
        const target = neckWorld.clone().add(new THREE.Vector3(0, 0.15, 0));
        const forward = new THREE.Vector3(0, 0, 1).applyQuaternion(rig.quaternion).normalize();
        const right = new THREE.Vector3(1, 0, 0).applyQuaternion(rig.quaternion).normalize();
        const rad = ${(v.yawDeg * Math.PI) / 180};
        const pRad = ${(v.pitchDeg * Math.PI) / 180};
        const dist = 1.48;
        const camDir = forward.clone().multiplyScalar(Math.cos(rad) * Math.cos(pRad))
          .addScaledVector(right, Math.sin(rad) * Math.cos(pRad))
          .add(new THREE.Vector3(0, Math.sin(pRad), 0)).normalize();
        const camPos = target.clone().addScaledVector(camDir, dist);
        sc.getCameraRig().setFocusTarget({
          actIndex: 0,
          subTargetId: 'expr-review',
          camPos,
          lookAt: target,
          fov: 22,
        });
        sc.animateTick(0.016);
        if (headBone && ${v.headYaw !== undefined ? 'true' : 'false'}) {
          headBone.rotation.y = ${v.headYaw ?? 0};
        }
        const morphs = ${JSON.stringify(v.morphs)};
        for (const m of sc.getGLTFFacialMorphMeshes()) {
          const dict = m.morphTargetDictionary;
          const infl = m.morphTargetInfluences;
          if (!dict || !infl) continue;
          for (let i = 0; i < infl.length; i++) infl[i] = 0;
          for (const [k, val] of Object.entries(morphs)) {
            if (dict[k] !== undefined) infl[dict[k]] = val;
          }
        }
        sc.getRenderer().render(sc.getScene(), sc.getCamera());
      })()`,
    });
    await new Promise((r) => setTimeout(r, 80));
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(outWork, `${v.name}.png`), Buffer.from(shot.data, 'base64'));
    console.log('Captured', v.name);
  }
  ws.close();
} finally {
  try { proc.kill(); } catch {}
  server.close();
  await new Promise((r) => setTimeout(r, 400));
  try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch {}
}
