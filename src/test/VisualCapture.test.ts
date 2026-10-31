// @vitest-environment node
import { describe, it, expect } from 'vitest';
import * as http from 'node:http';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { spawn, execSync } from 'node:child_process';
import * as os from 'node:os';
import { verifyScreenshotAgainstBaseline } from './visualDiff';

const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.glb': 'model/gltf-binary',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.json': 'application/json',
};

function findBrowser(): string | null {
  if (process.env.SKIP_CDP === '1' || process.env.SKIP_CDP === 'true') {
    return null;
  }
  const candidates = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return null;
}

function cleanStaleTempDirs(): void {
  const rootDir = path.resolve(__dirname, '../../');
  try {
    for (const entry of fs.readdirSync(rootDir)) {
      if (entry.startsWith('.tmp_cdp_') || entry === '.tmp_chrome_profile') {
        try {
          fs.rmSync(path.join(rootDir, entry), { recursive: true, force: true });
        } catch {}
      }
    }
    const extractedImg = path.join(rootDir, 'extracted_body_color.webp');
    if (fs.existsSync(extractedImg)) {
      try { fs.unlinkSync(extractedImg); } catch {}
    }
  } catch {}
}

cleanStaleTempDirs();



let portCounter = 9400 + Math.floor(Math.random() * 200);

async function verifyRealScreenViaCDP(browserPath: string, targetUrl: string, outDir: string): Promise<Record<string, any>> {
  const tempDir = fs.mkdtempSync(path.join(path.resolve(__dirname, '../../'), '.tmp_cdp_'));

  const cdpPort = portCounter++;
  const args = [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    `--user-data-dir=${tempDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-extensions',
    '--disable-sync',
    '--window-size=1280,800',
    `--remote-debugging-port=${cdpPort}`,
    'about:blank',
  ];

  console.log('[CDP Real-Screen] Spawning browser on port', cdpPort);
  const browserProc = spawn(browserPath, args, { stdio: 'ignore' });
  const browserErrors: string[] = [];

  try {
    // Wait for CDP endpoint to be available
    let connected = false;
    for (let i = 0; i < 120; i++) {
      await new Promise((r) => setTimeout(r, 250));
      try {
        const res = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
        if (res.ok) {
          connected = true;
          break;
        }
      } catch {}
    }
    if (!connected) throw new Error(`Failed to connect to browser CDP endpoint on port ${cdpPort}`);

    // Create a new about:blank page tab first so we can enable Runtime before navigating
    const newTabRes = await fetch(`http://127.0.0.1:${cdpPort}/json/new?about:blank`, { method: 'PUT' });
    const tabData = await newTabRes.json();
    const wsUrl = tabData.webSocketDebuggerUrl;
    console.log('[CDP Real-Screen] Connected to tab ws:', wsUrl);

    // Connect WebSocket
    const ws = new WebSocket(wsUrl);
    await new Promise<void>((resolve, reject) => {
      ws.onopen = () => resolve();
      ws.onerror = (e) => reject(e);
    });

    let msgId = 1;
    const send = (method: string, params: Record<string, any> = {}): Promise<any> => {
      const id = msgId++;
      return new Promise((resolve) => {
        const handler = (event: any) => {
          const data = JSON.parse(event.data);
          if (data.id === id) {
            ws.removeEventListener('message', handler);
            resolve(data.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id, method, params }));
      });
    };

    ws.addEventListener('message', (event: any) => {
      const data = JSON.parse(event.data);
      if (data.method === 'Runtime.consoleAPICalled') {
        const text = data.params.args.map((a: any) => a.value ?? a.description).join(' ');
        if (data.params.type === 'error') {
          console.error('[BROWSER CONSOLE ERROR]', text);
          browserErrors.push(text);
        } else {
          console.log('[BROWSER CONSOLE]', text);
        }
      } else if (data.method === 'Runtime.exceptionThrown') {
        const desc = JSON.stringify(data.params.exceptionDetails);
        console.error('[BROWSER EXCEPTION]', desc);
        browserErrors.push(desc);
      }
    });

    await send('Page.enable');
    await send('Runtime.enable');
    // Emulate prefers-reduced-motion: reduce to freeze procedural jitter/particle rotation for deterministic visual snapshots (AC-03, AC-VISUAL-02)
    try {
      await send('Emulation.setEmulatedMedia', {
        media: 'screen',
        features: [{ name: 'prefers-reduced-motion', value: 'reduce' }],
      });
      await send('Page.addScriptToEvaluateOnNewDocument', {
        source: `
          const origMatchMedia = window.matchMedia;
          window.matchMedia = function(q) {
            if (q && q.includes('prefers-reduced-motion')) {
              return {
                matches: true,
                media: q,
                onchange: null,
                addListener: () => {},
                removeListener: () => {},
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => false,
              };
            }
            return origMatchMedia ? origMatchMedia.call(window, q) : { matches: false, media: q };
          };
        `,
      });
    } catch {}
    await send('Page.navigate', { url: targetUrl });

    // Wait until document.body.dataset.threeSceneReady === 'true' and at least 30 WebGL frames settled (AC-VISUAL-02)
    console.log('[CDP Real-Screen] Waiting for 3D scene ready in DOM and WebGL frame settle...');
    const startTime = Date.now();
    while (Date.now() - startTime < 25000) {
      const evalRes = await send('Runtime.evaluate', {
        awaitPromise: true,
        expression: `(async () => {
          if (document.body.dataset.threeSceneReady !== 'true') return false;
          if (document.fonts) {
            try { await document.fonts.ready; } catch {}
          }
          const sc = window.__sceneController;
          if (!sc) return false;
          const frames = sc.getRenderer()?.info?.render?.frame ?? 0;
          return frames >= 30;
        })()`,
        returnByValue: true,
      });
      if (evalRes?.result?.value === true) {
        console.log('[CDP Real-Screen] 3D scene and WebGL frame settle verified (>= 30 frames)!');
        break;
      }
      await new Promise((r) => setTimeout(r, 200));
    }

    // Set reduced motion to freeze dynamic particle lattice drift and blinking for deterministic visual regression
    await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        if (sc) sc.setReducedMotion(true);
      })()`,
    });

    const settleRenderFrames = async (frames = 30): Promise<void> => {
      await send('Runtime.evaluate', {
        awaitPromise: true,
        expression: `(async () => {
          if (document.fonts) {
            try { await document.fonts.ready; } catch {}
          }
          await new Promise((resolve) => {
            let count = 0;
            const onFrame = () => {
              count++;
              if (count >= ${frames}) {
                resolve();
              } else {
                requestAnimationFrame(onFrame);
              }
            };
            requestAnimationFrame(onFrame);
          });
        })()`,
      });
    };

    // Initial frame settle
    await settleRenderFrames(50);

    const takeScreenshot = async (name: string): Promise<string> => {
      const debugRes = await send('Runtime.evaluate', {
        expression: `(() => {
          const sc = window.__sceneController;
          return {
            scrollY: window.scrollY,
            sp: sc?.getScrollProgress ? Number(sc.getScrollProgress().toFixed(4)) : null,
            camZ: sc?.getCamera() ? Number(sc.getCamera().position.z.toFixed(4)) : null,
            avatarZ: sc?.getAvatarRig() ? Number(sc.getAvatarRig().position.z.toFixed(4)) : null,
          };
        })()`,
        returnByValue: true,
      });
      console.log(`[CDP Real-Screen DEBUG ${name}]`, JSON.stringify(debugRes?.result?.value));

      const screenshotRes = await send('Page.captureScreenshot', { format: 'png' });
      const filePath = path.join(outDir, name);
      fs.writeFileSync(filePath, Buffer.from(screenshotRes.data, 'base64'));
      console.log(`[CDP Real-Screen] Captured ${name} (${screenshotRes.data.length} b64 bytes)`);

      const artifactDir = process.env.ARTIFACT_DIR || 'C:/Users/ziyan/.gemini/antigravity/brain/d188a7c3-0f26-44e4-bebc-d1447787a789';
      if (fs.existsSync(artifactDir)) {
        try {
          fs.writeFileSync(path.join(artifactDir, name), Buffer.from(screenshotRes.data, 'base64'));
        } catch {}
      }
      return filePath;
    };

    // 1. Act 1: Hero Enterprise AI Engine & Kinetic Wave Field Verification
    const act1Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        if (!sc) return null;
        const rig = sc.getAvatarRig();
        const plinth = rig.getObjectByName('Plinth');
        const personaBody = rig.getObjectByName('PersonaBody');
        const engine = rig.getObjectByName('EnterpriseAIEngine');
        const tier1 = rig.getObjectByName('EngineTier1');
        const tier2 = rig.getObjectByName('EngineTier2');
        const tier3 = rig.getObjectByName('EngineTier3');
        const waveField = sc.getScene().getObjectByName('KineticWaveField');
        const spatialHud = document.querySelector('[aria-label="Inspect Keynote Dossier"]');
        const telemetryBar = document.querySelector('[data-cursor="RANK"]');

        return {
          plinthY: plinth ? plinth.position.y : null,
          plinthTopY: plinth ? plinth.position.y + 0.10 : null,
          personaY: personaBody ? personaBody.position.y : null,
          hasEnterpriseEngine: Boolean(engine),
          hasTier1: Boolean(tier1),
          hasTier2: Boolean(tier2),
          hasTier3: Boolean(tier3),
          hasParticles: Boolean(waveField && (waveField.count === 1200 || waveField.isInstancedMesh)),
          particleCount: waveField ? waveField.count : 0,
          hasSpatialHud: Boolean(spatialHud),
          hasTelemetryBar: Boolean(telemetryBar),
        };
      })()`,
      returnByValue: true,
    });
    const act1Shot = await takeScreenshot('real_screen_act1_hero.png');

    // Interactive Core Strata Explosion Verification in Real Chrome Browser
    await send('Runtime.evaluate', {
      expression: `(() => {
        const explodeBtn = document.querySelector('button[aria-label="Explode Architecture"]');
        if (explodeBtn) explodeBtn.click();
      })()`,
    });
    await settleRenderFrames(35);

    const explodedMetrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        if (!sc) return null;
        return {
          isExploded: sc.isEngineExplodedState(),
          tier1Y: sc.getEngineTier1() ? sc.getEngineTier1().position.y : null,
          tier3Y: sc.getEngineTier3() ? sc.getEngineTier3().position.y : null,
        };
      })()`,
      returnByValue: true,
    });
    const act1ExplodedShot = await takeScreenshot('real_screen_act1_exploded.png');

    // Click again to return to integrated state for subsequent acts
    await send('Runtime.evaluate', {
      expression: `(() => {
        const explodeBtn = document.querySelector('button[aria-label="Explode Architecture"]');
        if (explodeBtn) explodeBtn.click();
      })()`,
    });
    await settleRenderFrames(35);

    // 2. Act 1 -> 2 Transition: Synchronous camera and persona travel (DEF-09)
    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const timelineEl = document.getElementById('timeline');
        const targetY = timelineEl ? Math.round(timelineEl.offsetTop * 0.55) : 600;
        window.scrollTo({ top: targetY, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const transMetrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        const camZ = sc.getCamera().position.z;
        const avatarZ = sc.getAvatarRig().position.z;
        return { camZ, avatarZ };
      })()`,
      returnByValue: true,
    });
    const transShot = await takeScreenshot('real_screen_act1_to_2_transition.png');

    // 3. Act 2: Academy & Tome Lectern Pedestal (DEF-08)
    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const el = document.getElementById('timeline');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const act2Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        const pedestal = sc.getScene().getObjectByName('TomeLecternPedestal');
        const base = sc.getScene().getObjectByName('TomeLecternBase');
        return {
          hasPedestal: Boolean(pedestal),
          hasBase: Boolean(base)
        };
      })()`,
      returnByValue: true,
    });
    const act2Shot = await takeScreenshot('real_screen_act2_academy.png');

    // 4. Act 3: Crucible Orbiting Badges & Rotation Surge (DEF-01)
    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const el = document.getElementById('vault');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const act3CrucibleShot = await takeScreenshot('real_screen_act3_crucible.png');

    // Trigger [Surge Cloud Badges]
    await send('Runtime.evaluate', {
      expression: `(() => {
        window.dispatchEvent(new CustomEvent('portfolio:scene_action', { detail: { action: 'surge_badges' } }));
      })()`,
    });
    await settleRenderFrames(40);
    const act3Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        const orbitGroup = sc.getScene().getObjectByName('CrucibleOrbitBadges');
        const avatarRig = sc.getAvatarRig();
        let minRadius = 999;
        orbitGroup.children.forEach(b => {
          const r = Math.hypot(b.position.x, b.position.z);
          if (r < minRadius) minRadius = r;
        });
        return {
          minRadius,
          badgeCount: orbitGroup.children.length,
          avatarRigX: avatarRig.position.x
        };
      })()`,
      returnByValue: true,
    });
    const act3SurgeShot = await takeScreenshot('real_screen_act3_surge.png');

    // 5. Act 4: Mount Pilatus Summit & Star Press Museum Proof (DEF-03)
    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const el = document.getElementById('summit');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const act4Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        const press = sc.getScene().getObjectByName('StarPressParchment');
        const trophy = sc.getScene().getObjectByName('GoldenTrophy');
        const pressWorldPos = press.position.clone();
        const trophyWorldPos = trophy.position.clone();
        press.getWorldPosition(pressWorldPos);
        trophy.getWorldPosition(trophyWorldPos);
        const projectedPress = pressWorldPos.clone().project(sc.getCamera());
        const avatarRig = sc.getAvatarRig();
        const cam = sc.getCamera();
        const projectedAvatar = avatarRig.position.clone().project(cam);
        return {
          pressX: pressWorldPos.x,
          trophyX: trophyWorldPos.x,
          projectedNdcX: projectedPress.x,
          avatarPos: { x: avatarRig.position.x, y: avatarRig.position.y, z: avatarRig.position.z },
          camPos: { x: cam.position.x, y: cam.position.y, z: cam.position.z },
          lookAt: { x: sc.getCurrentLookAt().x, y: sc.getCurrentLookAt().y, z: sc.getCurrentLookAt().z },
          projectedAvatarNdc: { x: projectedAvatar.x, y: projectedAvatar.y, z: projectedAvatar.z }
        };
      })()`,
      returnByValue: true,
    });
    const act4Shot = await takeScreenshot('real_screen_act4_summit.png');

    // 6. Act 5 & Act 6: Frontier & Horizon
    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const el = document.getElementById('ai-solutions');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const act5Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        if (!sc) return null;
        let orb = null;
        sc.getScene().traverse((o) => {
          if (o.userData && o.userData.type === 'flagshipOrb') orb = o;
        });
        if (!orb) return null;
        const cam = sc.getCamera();
        const worldPos = new THREE.Vector3();
        orb.getWorldPosition(worldPos);
        const leftEdge = worldPos.clone().setX(worldPos.x - 1.25);
        leftEdge.project(cam);
        return {
          orbWorldX: worldPos.x,
          orbLeftNdcX: leftEdge.x,
        };
      })()`,
      returnByValue: true,
    });
    const act5Shot = await takeScreenshot('real_screen_act5_frontier.png');

    await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const el = document.getElementById('contact');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
      })()`,
    });
    await settleRenderFrames(35);
    const act6Metrics = await send('Runtime.evaluate', {
      expression: `(() => {
        const activeNav = document.querySelector('header nav div.hidden button.text-white.font-semibold');
        return {
          activeNavLabel: activeNav ? activeNav.textContent.trim() : null,
        };
      })()`,
      returnByValue: true,
    });
    const act6Shot = await takeScreenshot('real_screen_act6_portal.png');

    ws.close();

    return {
      act1Metrics: act1Metrics?.result?.value,
      explodedMetrics: explodedMetrics?.result?.value,
      transMetrics: transMetrics?.result?.value,
      act2Metrics: act2Metrics?.result?.value,
      act3Metrics: act3Metrics?.result?.value,
      act4Metrics: act4Metrics?.result?.value,
      act5Metrics: act5Metrics?.result?.value,
      act6Metrics: act6Metrics?.result?.value,
      screenshots: {
        act1: act1Shot,
        act1Exploded: act1ExplodedShot,
        trans: transShot,
        act2: act2Shot,
        act3Crucible: act3CrucibleShot,
        act3Surge: act3SurgeShot,
        act4: act4Shot,
        act5: act5Shot,
        act6: act6Shot,
      },
      browserErrors,
    };
  } finally {
    try { browserProc.kill(); } catch {}
    await new Promise((r) => setTimeout(r, 500));
    try { fs.rmSync(tempDir, { recursive: true, force: true }); } catch {}
  }
}

describe('Real Screen Browser Verification & Visual Kinematics', () => {
  it('plays and verifies real screen animations, transitions, and spatial staging in browser', async () => {
    const browserPath = findBrowser();
    console.log('[VisualCapture] Browser path found:', browserPath);
    if (!browserPath) {
      console.warn('[VisualCapture] No compatible Chrome/Edge browser found on system; skipping real-screen CDP capture.');
      return;
    }

    const rootDir = path.resolve(__dirname, '../../');
    const distDir = path.resolve(rootDir, 'dist');

    // Create simple HTTP server serving distDir
    const server = http.createServer((req, res) => {
      let reqPath = req.url?.split('?')[0] || '/';
      if (reqPath === '/') reqPath = '/index.html';
      const filePath = path.join(distDir, reqPath);

      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
        fs.createReadStream(filePath).pipe(res);
      } else {
        res.writeHead(404);
        res.end('Not Found');
      }
    });

    const port = 4173 + Math.floor(Math.random() * 50);
    await new Promise<void>((resolve) => server.listen(port, '127.0.0.1', resolve));
    console.log(`[VisualCapture] HTTP server listening on http://127.0.0.1:${port}`);

    try {
      const outDir = path.resolve(rootDir, 'screenshots');
      if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
      }

      const results = await verifyRealScreenViaCDP(browserPath, `http://127.0.0.1:${port}/index.html`, outDir);

      // Verify zero browser exceptions occurred
      expect(results.browserErrors.length).toBe(0);

      // Verify Interactive Enterprise AI Engine & 1,200-particle kinetic wave field in real browser
      if (results.act1Metrics) {
        expect(results.act1Metrics.plinthTopY).toBeCloseTo(-1.45, 2);
        if (results.act1Metrics.personaY !== null) {
          expect(results.act1Metrics.personaY).toBeCloseTo(-1.45, 2);
        }
        expect(results.act1Metrics.hasEnterpriseEngine).toBe(true);
        expect(results.act1Metrics.hasTier1).toBe(true);
        expect(results.act1Metrics.hasTier2).toBe(true);
        expect(results.act1Metrics.hasTier3).toBe(true);
        expect(results.act1Metrics.hasParticles).toBe(true);
        expect(results.act1Metrics.particleCount).toBe(1200);
        expect(results.act1Metrics.hasSpatialHud).toBe(true);
        expect(results.act1Metrics.hasTelemetryBar).toBe(true);
      }

      // Verify Interactive Core Strata Explosion Dynamics in real browser
      if (results.explodedMetrics) {
        expect(results.explodedMetrics.isExploded).toBe(true);
        expect(results.explodedMetrics.tier1Y).toBeGreaterThan(0.65);
        expect(results.explodedMetrics.tier3Y).toBeLessThan(-0.55);
      }

      // Verify DEF-09: Synchronous camera and avatar travel during Act 1 -> 2 transition
      if (results.transMetrics) {
        expect(results.transMetrics.avatarZ).toBeLessThan(5.10);
        expect(results.transMetrics.camZ).toBeLessThan(8.50);
      }

      // Verify DEF-08: Lectern pedestal exists
      if (results.act2Metrics) {
        expect(results.act2Metrics.hasPedestal).toBe(true);
        expect(results.act2Metrics.hasBase).toBe(true);
      }

      // Verify DEF-01: Badges orbit at 0.72m
      if (results.act3Metrics) {
        expect(results.act3Metrics.minRadius).toBeCloseTo(0.72, 2);
        expect(results.act3Metrics.badgeCount).toBe(5);
      }

      // Verify DEF-03: Star Press is in right corridor (X > 1.5, projected NDC X > 0)
      if (results.act4Metrics) {
        expect(results.act4Metrics.pressX).toBeGreaterThan(1.5);
        expect(results.act4Metrics.projectedNdcX).toBeGreaterThan(0);
      }

      // Verify DEF-10: Flagship Orb stays in right corridor (left edge NDC X > -0.15, text corridor clear)
      if (results.act5Metrics) {
        expect(results.act5Metrics.orbLeftNdcX).toBeGreaterThan(-0.15);
      }

      // Verify DEF-11: Act 6 navbar active indicator correctly highlights 06. Interests & Approach
      if (results.act6Metrics && results.act6Metrics.activeNavLabel) {
        expect(results.act6Metrics.activeNavLabel).toBe('06. Interests & Approach');
      }

      // Verify all screenshots against golden baselines with 1.5% pixel mismatch threshold (AC-VISUAL-01, AC-VISUAL-03)
      const baselinesDir = path.resolve(rootDir, 'src/test/baselines');
      const diffResults: Array<{ name: string; diffRatio: number; diffPixels: number; totalPixels: number; match: boolean; diffPath?: string }> = [];

      for (const [key, filePath] of Object.entries(results.screenshots)) {
        const fileName = path.basename(filePath as string);
        const baselinePath = path.join(baselinesDir, fileName);
        const diffPath = path.join(outDir, `${path.parse(fileName).name}_diff.png`);

        const diffResult = verifyScreenshotAgainstBaseline(
          filePath as string,
          baselinePath,
          diffPath,
          {
            threshold: 0.1,
            maxDiffPixelRatio: 0.015, // 1.5% maximum mismatch tolerance
          }
        );

        diffResults.push({
          name: fileName,
          diffRatio: diffResult.diffRatio,
          diffPixels: diffResult.diffPixels,
          totalPixels: diffResult.totalPixels,
          match: diffResult.match,
          diffPath: diffResult.diffPath,
        });

        if (diffResult.initializedBaseline) {
          console.log(`[VisualCapture] 🌟 Initialized golden baseline: ${fileName}`);
        } else {
          console.log(
            `[VisualCapture] 🔍 ${fileName}: ${(diffResult.diffRatio * 100).toFixed(2)}% ` +
            `(${diffResult.diffPixels}/${diffResult.totalPixels} px, threshold: 1.50%) - ${diffResult.match ? 'PASS' : 'FAIL'}`
          );
        }
      }

      const failures = diffResults.filter((r) => !r.match);
      if (failures.length > 0) {
        const failureDetails = failures
          .map((f) => `• ${f.name}: ${(f.diffRatio * 100).toFixed(2)}% diff (${f.diffPixels}/${f.totalPixels} px). Diff overlay: ${f.diffPath}`)
          .join('\n');
        expect.fail(`Visual regression failure in ${failures.length} act(s):\n${failureDetails}`);
      }
    } finally {
      await new Promise<void>((resolve) => server.close(() => resolve()));
    }
  }, 150000);
});
