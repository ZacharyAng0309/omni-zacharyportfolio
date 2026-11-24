// @vitest-environment node
import { describe, it, expect } from 'vitest';
import * as http from 'node:http';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { spawn } from 'node:child_process';
import { verifyScreenshotAgainstBaseline } from './visualDiff';

const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.glb': 'model/gltf-binary',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.webp': 'image/webp',
  '.json': 'application/json',
};

function findBrowser(): string | null {
  if (process.env.SKIP_CDP === '1' || process.env.SKIP_CDP === 'true') {
    return null;
  }
  const candidates: string[] = [];
  if (process.env.CHROME_BIN) {
    candidates.push(process.env.CHROME_BIN);
  }
  candidates.push(
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`
  );

  // Discover Playwright-managed Chromium installs (work reliably in Windows sandboxed environments)
  const playwrightRoot = `${process.env.LOCALAPPDATA}\\ms-playwright`;
  try {
    if (fs.existsSync(playwrightRoot)) {
      const dirs = fs.readdirSync(playwrightRoot).filter((d) => /^chromium-\d+$/.test(d)).sort().reverse();
      for (const dir of dirs) {
        candidates.push(path.join(playwrightRoot, dir, 'chrome-win64', 'chrome.exe'));
      }
      const shellDirs = fs.readdirSync(playwrightRoot).filter((d) => /^chromium_headless_shell-\d+$/.test(d)).sort().reverse();
      for (const dir of shellDirs) {
        candidates.push(path.join(playwrightRoot, dir, 'chrome-headless-shell-win64', 'chrome-headless-shell.exe'));
      }
    }
  } catch {}

  candidates.push(
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  );
  for (const c of candidates) {
    try {
      if (c && fs.existsSync(c)) return c;
    } catch {}
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
  const isHeadlessShell = /chrome-headless-shell/i.test(browserPath);
  const args = [
    ...(isHeadlessShell ? [] : ['--headless=new']),
    '--no-sandbox',
    '--disable-gpu-sandbox',
    '--enable-unsafe-swiftshader',
    '--autoplay-policy=no-user-gesture-required',
    '--disable-features=RendererCodeIntegrity',
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
  const browserWarnings: string[] = [];

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
        } else if (data.params.type === 'warning') {
          console.log('[BROWSER CONSOLE WARNING]', text);
          browserWarnings.push(text);
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
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1280,
      height: 800,
      deviceScaleFactor: 1,
      mobile: false,
    });
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
          const hasAtelier = Boolean(sc.getAvatarRig()?.getObjectByName('Act1StudioGLB'));
          const hasCompanion = Boolean(sc.getStylizedCompanionModel());
          return frames >= 30 && hasAtelier && hasCompanion;
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

      const artifactDir = process.env.ARTIFACT_DIR;
      if (artifactDir && fs.existsSync(artifactDir)) {
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
        const spatialHud = document.querySelector('[data-testid="whisper-stage-hud"]');
        const telemetryBar = document.querySelector('[data-testid="diegetic-hotspot-layer"]');
        const whisperCaption = document.querySelector('[data-testid="companion-whisper-caption"]');

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
          hasStylizedCompanion: Boolean(sc.getStylizedCompanionModel()),
          companionActiveClip: sc.getCompanionActiveClip(),
          hasCompanionWhisperCaption: Boolean(whisperCaption && whisperCaption.textContent && whisperCaption.textContent.trim().length > 10),
        };
      })()`,
      returnByValue: true,
    });
    const act1Shot = await takeScreenshot('real_screen_act1_hero.png');

    // Interactive Core Strata Explosion Verification in Real Chrome Browser
    await send('Runtime.evaluate', {
      expression: `(() => {
        const explodeBtn = document.querySelector('button[data-testid="trigger-3d-gesture-btn"]');
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
          companionActiveClip: sc.getCompanionActiveClip(),
        };
      })()`,
      returnByValue: true,
    });
    const act1ExplodedShot = await takeScreenshot('real_screen_act1_exploded.png');

    // Click again to return to integrated state for subsequent acts
    await send('Runtime.evaluate', {
      expression: `(() => {
        const explodeBtn = document.querySelector('button[data-testid="trigger-3d-gesture-btn"]');
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
        return {
          camZ,
          avatarZ,
          companionActiveClip: sc.getCompanionActiveClip(),
        };
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

    // Interactive regression checks in live Chromium D3D11 (after clean desktop captures):
    // 1. Act 5 Dock [Explode Strata] toggles Act 5 Frontier (NOT off-screen Act 1)
    const act5DockMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const sc = window.__sceneController;
        const el = document.getElementById('ai-solutions');
        if (el) el.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 150));
        const act1Before = sc.isEngineExplodedState();
        const act5Before = sc.isFrontierStrataExplodedState();
        const btn = document.querySelector('[data-testid="trigger-3d-gesture-btn"]');
        if (btn) btn.click();
        await new Promise((r) => setTimeout(r, 120));
        return {
          act1Before,
          act5Before,
          act1After: sc.isEngineExplodedState(),
          act5After: sc.isFrontierStrataExplodedState(),
        };
      })()`,
      returnByValue: true,
    });

    // 2. Act 1 Whisper subtarget click (no stack-overflow recursion) + Close sheet resets pose + 6-mesh morph sync
    const subtargetPoseMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const sc = window.__sceneController;
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 150));
        const pill = document.querySelector('[data-testid="whisper-subtarget-strategy-table"]');
        if (pill) pill.click();
        await new Promise((r) => setTimeout(r, 150));
        const sheet = document.querySelector('[data-testid="slide-over-inspection-sheet"]');
        const dock = document.querySelector('[data-testid="spatial-stage-control-dock"]');
        const openState = sheet ? sheet.getAttribute('data-sheet-open') : null;
        const activePose = sc.getCurrentPoseAction();

        const closeBtn = document.querySelector('[data-testid="close-inspection-sheet-btn"]');
        const navEl = document.querySelector('header nav');
        const timelineCard = document.querySelector('[data-testid="cinema-timeline-hud"] > div');
        const navRect = navEl ? navEl.getBoundingClientRect() : null;
        const sheetRect = sheet ? sheet.getBoundingClientRect() : null;
        const closeBtnRect = closeBtn ? closeBtn.getBoundingClientRect() : null;
        const dockRect = dock ? dock.getBoundingClientRect() : null;
        const timelineRect = timelineCard ? timelineCard.getBoundingClientRect() : null;
        const sheetScrollTop = sheet ? sheet.scrollTop : null;
        const closeBtnVisibleInSheet = Boolean(
          sheetRect && closeBtnRect && closeBtnRect.top >= sheetRect.top && closeBtnRect.bottom <= sheetRect.bottom
        );
        const navClearsTimeline = Boolean(navRect && timelineRect && navRect.bottom <= timelineRect.top);
        const sheetClearsDock = Boolean(sheetRect && dockRect && sheetRect.bottom <= dockRect.top);
        const sheetClearsTimeline = Boolean(sheetRect && timelineRect && sheetRect.top >= timelineRect.bottom);

        // Verify Peek 3D Stage fades an open SlideOverInspectionSheet cleanly
        const waitFrames = (n = 4) =>
          new Promise((resolve) => {
            let count = 0;
            const step = () => {
              if (++count >= n) resolve();
              else requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
          });
        const peekBtn = document.querySelector('[data-testid="peek-stage-toggle"]');
        if (peekBtn) peekBtn.click();
        await waitFrames(6);
        const peekSheetOpacity = sheet ? parseFloat(getComputedStyle(sheet).opacity) : 1;
        if (peekBtn) peekBtn.click();
        await waitFrames(4);

        // Verify representative Acts 1-6 Focus Dolly targets stay clear of the right-hand sheet & top timeline
        const sectionIds = ['hero', 'timeline', 'vault', 'summit', 'ai-solutions', 'contact'];
        const focusChecks = [
          { actIndex: 0, id: 'strategy-table' },
          { actIndex: 1, id: 'vol-3' },
          { actIndex: 2, id: 'cloud-ai' },
          { actIndex: 3, id: 'hilti-trophy' },
          { actIndex: 3, id: 'star-press' },
          { actIndex: 4, id: 'privacy-first-ai-work-tracker' },
          { actIndex: 5, id: 'ai-systems' },
        ];
        let allFocusFramingClear = true;
        for (const fc of focusChecks) {
          if (closeBtn) closeBtn.click();
          await new Promise((r) => setTimeout(r, 40));
          const secEl = document.getElementById(sectionIds[fc.actIndex]);
          if (secEl) secEl.scrollIntoView({ behavior: 'instant', block: 'start' });
          window.dispatchEvent(new Event('scroll'));
          await new Promise((r) => setTimeout(r, 60));
          const subBtn = document.querySelector('[data-testid="whisper-subtarget-' + fc.id + '"]');
          if (subBtn) subBtn.click();
          await new Promise((r) => setTimeout(r, 80));
          sc.animateTick(0.016);
          const cam = sc.getCamera();
          cam.updateMatrixWorld(true);
          const sr = sheet.getBoundingClientRect();
          const sheetLeftNdc = (sr.left / window.innerWidth) * 2 - 1;
          const cfg = sc.constructor.DIORAMA_SUB_TARGETS.find((x) => x.id === fc.id);
          const pAnchor = cfg.worldAnchor.clone().project(cam);
          const tlBottom = timelineRect ? timelineRect.bottom : 124;
          let sculptureClippedTop = false;
          if (fc.actIndex === 0) {
            const tier1 = sc.getAvatarRig().getObjectByName('Prop_Blueprint_Tier1');
            if (tier1) {
              const tPos = new THREE.Vector3();
              tier1.getWorldPosition(tPos);
              const tTop = tPos.clone().add(new THREE.Vector3(0, 0.08, 0)).project(cam);
              const tPxY = (-tTop.y * 0.5 + 0.5) * window.innerHeight;
              sculptureClippedTop = tPxY <= tlBottom || tPos.clone().project(cam).x >= sheetLeftNdc - 0.03;
            }
          }
          if (
            pAnchor.x >= sheetLeftNdc - 0.03 ||
            pAnchor.x <= -0.95 ||
            sculptureClippedTop
          ) {
            allFocusFramingClear = false;
          }
        }

        // Verify CinemaTimelineHUD hover preview tooltip clears the timeline bar cleanly (never covers slate text)
        let hoverTooltipClearsTimeline = false;
        const trackForHover = document.querySelector('[data-testid="cinema-timeline-track"]');
        if (trackForHover && timelineRect) {
          const trH = trackForHover.getBoundingClientRect();
          trackForHover.dispatchEvent(new PointerEvent('pointermove', { clientX: trH.left + trH.width * 0.3, bubbles: true }));
          await new Promise((r) => setTimeout(r, 40));
          const tipRect = document.querySelector('[data-testid="cinema-hover-preview"]')?.getBoundingClientRect();
          hoverTooltipClearsTimeline = Boolean(tipRect && tipRect.top >= timelineRect.bottom);
          trackForHover.dispatchEvent(new PointerEvent('pointerout', { bubbles: true }));
        }

        // Verify clicking inside open SlideOverInspectionSheet over Act 5 flagshipOrb does NOT raycast through to open modal
        if (closeBtn) closeBtn.click();
        await new Promise((r) => setTimeout(r, 40));
        const act5ElForClickThrough = document.getElementById('ai-solutions');
        if (act5ElForClickThrough) act5ElForClickThrough.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
        sc.animateTick(0.016);
        const dossierOpenForClickThrough = document.querySelector('[data-testid="whisper-open-dossier-btn"]');
        if (dossierOpenForClickThrough) dossierOpenForClickThrough.click();
        await new Promise((r) => setTimeout(r, 100));
        for (let f = 0; f < 40; f++) sc.animateTick(0.016);
        let act5Orb = null;
        sc.getScene().traverse((o) => {
          if (o.userData?.type === 'flagshipOrb') act5Orb = o;
        });
        let sheetClickThroughBlocked = false;
        let act5OrbClearOfSheet = true;
        if (act5Orb && sheet) {
          sc.getCamera().updateMatrixWorld(true);
          const orbWorld = new THREE.Vector3();
          act5Orb.getWorldPosition(orbWorld);
          orbWorld.project(sc.getCamera());
          const orbX = (orbWorld.x * 0.5 + 0.5) * window.innerWidth;
          const sheetRect = sheet.getBoundingClientRect();
          act5OrbClearOfSheet = orbX < sheetRect.left;
          const probeX = sheetRect.left + 80;
          const probeY = sheetRect.top + 180;
          const topEl = document.elementFromPoint(probeX, probeY);
          const isInsideSheet = Boolean(topEl?.closest('[data-testid="slide-over-inspection-sheet"]'));
          topEl?.dispatchEvent(new PointerEvent('pointerdown', { clientX: probeX, clientY: probeY, bubbles: true }));
          await new Promise((r) => setTimeout(r, 80));
          sheetClickThroughBlocked = act5OrbClearOfSheet && isInsideSheet && !document.querySelector('[role="dialog"]');
          document.querySelector('[aria-label="Close modal"]')?.click();
        }

        // Verify desktop sheet-open left-58% avatar framing across Acts 1-6 (avatarScreenX < sheetRect.left - 24)
        let sheetFramingAllActsClear = true;
        if (dossierOpenForClickThrough && sheet) {
          for (let actIdx = 0; actIdx < sectionIds.length; actIdx++) {
            const secEl = document.getElementById(sectionIds[actIdx]);
            if (secEl) secEl.scrollIntoView({ behavior: 'instant', block: 'start' });
            window.dispatchEvent(new Event('scroll'));
            await new Promise((r) => setTimeout(r, 60));
            if (sheet.getAttribute('aria-hidden') === 'true') {
              dossierOpenForClickThrough.click();
              await new Promise((r) => setTimeout(r, 60));
            }
            for (let f = 0; f < 45; f++) sc.animateTick(0.016);
            sc.getCamera().updateMatrixWorld(true);
            const avWorld = new THREE.Vector3();
            sc.getAvatarRig().getWorldPosition(avWorld);
            avWorld.y += 1.0;
            avWorld.project(sc.getCamera());
            const avatarScreenX = (avWorld.x * 0.5 + 0.5) * window.innerWidth;
            const srAct = sheet.getBoundingClientRect();
            if (avatarScreenX >= srAct.left - 24 || avatarScreenX <= 24) {
              sheetFramingAllActsClear = false;
            }
          }
          if (closeBtn) closeBtn.click();
          await new Promise((r) => setTimeout(r, 60));
          for (let f = 0; f < 45; f++) sc.animateTick(0.016);
        }

        // Verify chapter-tab switch from focused Act 1 releases camera focus & moves cleanly to Act 4
        if (closeBtn) closeBtn.click();
        await new Promise((r) => setTimeout(r, 40));
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 60));
        const optBtn = document.querySelector('[data-testid="whisper-subtarget-optical-core"]');
        if (optBtn) optBtn.click();
        await new Promise((r) => setTimeout(r, 60));
        const tabAct4 = document.querySelector('[data-testid="sheet-tab-act-3"]');
        if (tabAct4) tabAct4.click();
        await new Promise((r) => setTimeout(r, 120));
        sc.animateTick(0.016);
        const tabSwitchClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null;
        const tabSwitchCamZ = sc.getCamera().position.z;

        // Verify cross-act "Focus 3D Core" from Act 1 scrolls to Act 5 so Act 5 is visible (never empty void)
        if (closeBtn) closeBtn.click();
        await new Promise((r) => setTimeout(r, 40));
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 60));
        const dossierBtn = document.querySelector('[data-testid="whisper-open-dossier-btn"]');
        if (dossierBtn) dossierBtn.click();
        await new Promise((r) => setTimeout(r, 80));
        const sec4 = document.querySelector('[data-sheet-chapter="4"]');
        const focusCoreBtn = sec4 && Array.from(sec4.querySelectorAll('button')).find((b) => b.textContent.includes('Focus 3D Core'));
        if (focusCoreBtn) focusCoreBtn.click();
        await new Promise((r) => setTimeout(r, 120));
        sc.animateTick(0.016);
        const crossActFrontierVisible = sc.getFrontierGroup().visible;
        const crossActScrollProgress = sc.getScrollProgress();

        // Verify NavbarHUD click while sheet is open clears focus and syncs sheet header to Act 02
        const navGrowthBtn = Array.from(document.querySelectorAll('header nav button')).find((b) => b.textContent.includes('02. Growth'));
        if (navGrowthBtn) navGrowthBtn.click();
        await new Promise((r) => setTimeout(r, 120));
        sc.animateTick(0.016);
        const navbarClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null;
        const navbarSyncedSheetHeader = (sheet?.querySelector('span.uppercase')?.textContent?.trim() ?? '').startsWith('Act 02');

        // Verify scrubbing CinemaTimelineHUD (keyboard ArrowRight & pointer scrub within Act 1) while focused releases CameraRig focus
        if (closeBtn) closeBtn.click();
        await new Promise((r) => setTimeout(r, 40));
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 60));
        const optBtnForScrub = document.querySelector('[data-testid="whisper-subtarget-optical-core"]');
        if (optBtnForScrub) optBtnForScrub.click();
        await new Promise((r) => setTimeout(r, 80));
        sc.animateTick(0.016);
        const scrubCamZBefore = sc.getCamera().position.z;
        const timelineTrack = document.querySelector('[data-testid="cinema-timeline-track"]');
        if (timelineTrack) {
          timelineTrack.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
        }
        await new Promise((r) => setTimeout(r, 100));
        sc.animateTick(0.016);
        const scrubKeyClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null && sc.getActiveSubTarget() === null;
        const scrubKeyCamZ = sc.getCamera().position.z;
        const scrubKeyProgress = sc.getScrollProgress();

        // Also verify pointer scrub on timeline track while focused releases CameraRig focus
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 60));
        if (optBtnForScrub) optBtnForScrub.click();
        await new Promise((r) => setTimeout(r, 60));
        if (timelineTrack) {
          const tr = timelineTrack.getBoundingClientRect();
          timelineTrack.dispatchEvent(new PointerEvent('pointerdown', { clientX: tr.left + tr.width * 0.05, bubbles: true, pointerId: 1 }));
          timelineTrack.dispatchEvent(new PointerEvent('pointerup', { clientX: tr.left + tr.width * 0.05, bubbles: true, pointerId: 1 }));
        }
        await new Promise((r) => setTimeout(r, 100));
        sc.animateTick(0.016);
        const scrubPointerClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null && sc.getActiveSubTarget() === null;

        // Verify clicking already-active chapter tab (Act 01) does NOT arm stale pendingNavAct blocking subsequent scroll to Act 02
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 60));
        const tabAct1 = document.querySelector('[data-testid="sheet-tab-act-0"]');
        if (tabAct1) tabAct1.click();
        await new Promise((r) => setTimeout(r, 60));
        const act2SecEl = document.getElementById('timeline');
        if (act2SecEl) act2SecEl.scrollIntoView({ behavior: 'instant', block: 'start' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
        const sameTabThenScrollSyncedAct2 = (sheet?.querySelector('span.uppercase')?.textContent?.trim() ?? '').startsWith('Act 02');

        // Return cleanly to Act 1 and close sheet to verify Architectural Centerpiece mode & Titanium Atelier GLB
        if (closeBtn) closeBtn.click();
        await new Promise((r) => setTimeout(r, 80));
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 80));
        const resetPose = sc.getCurrentPoseAction();

        const hasGltfAvatarOnStage = Boolean(sc.getAvatarRig()?.getObjectByName('GLTFRealisticAvatar'));
        const stylizedRigVisible = sc.getStylizedRig().group.visible;
        const architecturalCenterpieceMode = sc.isArchitecturalCenterpieceMode();
        const atelierRoot = sc.getAvatarRig()?.getObjectByName('Act1StudioGLB');
        const requiredAtelierNames = [
          'SM_Island_Act1',
          'SM_Atelier_Pedestal',
          'Prop_Blueprint_Tier1',
          'Prop_Blueprint_Tier2',
          'Prop_Blueprint_Tier3',
          'SM_Core_Nucleus',
          'SM_Core_Filament',
          'SM_Gyro_Gimbal_Outer',
          'SM_Gyro_Gimbal_Inner',
        ];
        const atelierNodeCount = requiredAtelierNames.filter((n) => Boolean(atelierRoot?.getObjectByName(n))).length;
        const tier1Obj = atelierRoot?.getObjectByName('Prop_Blueprint_Tier1');
        const nucleusObj = atelierRoot?.getObjectByName('SM_Core_Nucleus');
        const tier1FirstMat = tier1Obj
          ? (() => {
              let found: any = null;
              tier1Obj.traverse((o: any) => {
                if (!found && o.isMesh) {
                  found = Array.isArray(o.material) ? o.material[0] : o.material;
                }
              });
              return found;
            })()
          : null;
        const nucleusMat = nucleusObj
          ? (() => {
              let found: any = null;
              nucleusObj.traverse((o: any) => {
                if (!found && o.isMesh) {
                  found = Array.isArray(o.material) ? o.material[0] : o.material;
                }
              });
              return found;
            })()
          : null;
        const glError = sc.getRenderer()?.getContext()?.getError?.() ?? 0;
        const checkShaderErrorsActive = sc.getRenderer()?.debug?.checkShaderErrors ?? false;

        return {
          openState,
          activePose,
          resetPose,
          hasGltfAvatarOnStage,
          stylizedRigVisible,
          architecturalCenterpieceMode,
          hasAtelierGlb: Boolean(atelierRoot),
          atelierNodeCount,
          hasStudioEnvRT: sc.getStudioEnvTarget() !== null,
          atelierMetallicHasEnvMap: Boolean(tier1FirstMat?.envMap),
          opticalGlassIsPhysical: Boolean(nucleusMat?.isMeshPhysicalMaterial && nucleusMat?.transmission > 0.5),
          sheetScrollTop,
          closeBtnVisibleInSheet,
          navClearsTimeline,
          sheetClearsDock,
          sheetClearsTimeline,
          peekSheetOpacity,
          allFocusFramingClear,
          hoverTooltipClearsTimeline,
          sheetClickThroughBlocked,
          sheetFramingAllActsClear,
          tabSwitchClearedFocus,
          tabSwitchCamZ,
          crossActFrontierVisible,
          crossActScrollProgress,
          navbarClearedFocus,
          navbarSyncedSheetHeader,
          scrubCamZBefore,
          scrubKeyClearedFocus,
          scrubKeyCamZ,
          scrubKeyProgress,
          scrubPointerClearedFocus,
          sameTabThenScrollSyncedAct2,
          sceneEnvIsNull: sc.getScene().environment === null,
          glError,
          checkShaderErrorsActive,
        };
      })()`,
      returnByValue: true,
    });

    // 2b. Short Desktop 1024x640 HUD clearance, zero nav overflow, and portrait headroom verification
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1024,
      height: 640,
      deviceScaleFactor: 1,
      mobile: false,
    });
    const shortDesktopMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        window.dispatchEvent(new Event('resize'));
        await new Promise((r) => setTimeout(r, 120));
        const sc = window.__sceneController;
        const navEl = document.querySelector('header nav');
        const nav = navEl?.getBoundingClientRect();
        const navOverflowX = navEl ? navEl.scrollWidth - navEl.clientWidth : null;
        const timeline = document.querySelector('[data-testid="cinema-timeline-hud"] > div')?.getBoundingClientRect();
        const sheet = document.querySelector('[data-testid="slide-over-inspection-sheet"]')?.getBoundingClientRect();
        const dock = document.querySelector('[data-testid="spatial-stage-control-dock"]')?.getBoundingClientRect();
        // Verify sculpture crown stays clear of timeline bottom even on 640px short desktop across Act 1 rested & exploded states
        let minHeadClearancePx = 9999;
        for (const id of ['strategy-table', 'optical-core']) {
          window.scrollTo({ top: 0, behavior: 'instant' });
          window.dispatchEvent(new Event('scroll'));
          sc.selectSubTarget(0, id, { emitCallback: false });
          sc.animateTick(0.016);
          const cam = sc.getCamera();
          cam.updateMatrixWorld(true);
          const tier1 = sc.getAvatarRig().getObjectByName('Prop_Blueprint_Tier1');
          const tp = new THREE.Vector3();
          if (tier1) {
            tier1.getWorldPosition(tp);
          } else {
            sc.getAvatarRig().getWorldPosition(tp);
            tp.y += 0.15;
          }
          const crown = tp.clone().add(new THREE.Vector3(0, 0.08, 0)).project(cam);
          const crownPxY = (-crown.y * 0.5 + 0.5) * window.innerHeight;
          minHeadClearancePx = Math.min(minHeadClearancePx, crownPxY - (timeline ? timeline.bottom : 124));
        }
        sc.clearSubTargetFocus();
        return {
          navBottom: nav ? nav.bottom : null,
          navHeight: nav ? nav.height : null,
          navOverflowX,
          timelineTop: timeline ? timeline.top : null,
          timelineBottom: timeline ? timeline.bottom : null,
          sheetTop: sheet ? sheet.top : null,
          sheetBottom: sheet ? sheet.bottom : null,
          dockTop: dock ? dock.top : null,
          minHeadClearancePx,
        };
      })()`,
      returnByValue: true,
    });

    // 2c. Tablet 768x1024 HUD clearance & mobile menu backdrop stacking above sheet/dock
    await send('Emulation.setDeviceMetricsOverride', {
      width: 768,
      height: 1024,
      deviceScaleFactor: 1,
      mobile: false,
    });
    const tabletMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const waitRaf = (n = 4) => new Promise((res) => { let c = 0; const f = () => (++c >= n ? res() : requestAnimationFrame(f)); requestAnimationFrame(f); });
        window.dispatchEvent(new Event('resize'));
        await waitRaf(4);
        document.querySelector('[data-testid="whisper-open-dossier-btn"]')?.click();
        await waitRaf(6);
        const nav = document.querySelector('header nav')?.getBoundingClientRect();
        const timeline = document.querySelector('[data-testid="cinema-timeline-hud"] > div')?.getBoundingClientRect();
        const sheet = document.querySelector('[data-testid="slide-over-inspection-sheet"]')?.getBoundingClientRect();
        const dock = document.querySelector('[data-testid="spatial-stage-control-dock"]')?.getBoundingClientRect();
        const hamburger = document.querySelector('button[aria-label="Open Navigation Menu"]');
        let backdropCoversSheet = false;
        let backdropCoversDock = false;
        let backdropTop = null;
        if (hamburger && sheet && dock) {
          hamburger.click();
          await waitRaf(6);
          const bdRect = document.querySelector('[data-testid="mobile-menu-backdrop"]')?.getBoundingClientRect();
          backdropTop = bdRect ? bdRect.top : null;
          const menuDialog = document.querySelector('[aria-label="Mobile Navigation"]')?.getBoundingClientRect();
          const testY = menuDialog ? Math.min(sheet.bottom - 20, menuDialog.bottom + 40) : sheet.bottom - 20;
          const sheetMidX = Math.min(window.innerWidth - 20, Math.max(20, sheet.left + sheet.width / 2));
          backdropCoversSheet = document.elementFromPoint(sheetMidX, testY)?.getAttribute('data-testid') === 'mobile-menu-backdrop';
          backdropCoversDock = document.elementFromPoint(dock.left + dock.width / 2, dock.top + dock.height / 2)?.getAttribute('data-testid') === 'mobile-menu-backdrop';
          document.querySelector('button[aria-label="Close Navigation Menu"]')?.click();
          await waitRaf(4);
        }
        document.querySelector('[data-testid="close-inspection-sheet-btn"]')?.click();
        await waitRaf(4);
        return {
          navBottom: nav ? nav.bottom : null,
          navHeight: nav ? nav.height : null,
          timelineTop: timeline ? timeline.top : null,
          timelineBottom: timeline ? timeline.bottom : null,
          sheetTop: sheet ? sheet.top : null,
          sheetBottom: sheet ? sheet.bottom : null,
          sheetLeft: sheet ? sheet.left : null,
          dockTop: dock ? dock.top : null,
          backdropTop,
          backdropCoversSheet,
          backdropCoversDock,
        };
      })()`,
      returnByValue: true,
    });

    // 3. Mobile 375x812 viewport HUD non-overlap, mobile menu backdrop stacking & widened FOV verification
    await send('Emulation.setDeviceMetricsOverride', {
      width: 375,
      height: 812,
      deviceScaleFactor: 2,
      mobile: true,
    });
    const mobileMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const waitRaf = (n = 4) => new Promise((res) => { let c = 0; const f = () => (++c >= n ? res() : requestAnimationFrame(f)); requestAnimationFrame(f); });
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        window.dispatchEvent(new Event('resize'));
        await waitRaf(6);
        const nav = document.querySelector('header nav')?.getBoundingClientRect();
        const timeline = document.querySelector('[data-testid="cinema-timeline-hud"] > div')?.getBoundingClientRect();
        const timelineTrack = document.querySelector('[data-testid="cinema-timeline-track"]')?.getBoundingClientRect();
        const hud = document.querySelector('[data-testid="whisper-stage-hud"]');
        const dock = document.querySelector('[data-testid="spatial-stage-control-dock"]');
        const hudRect = hud ? hud.getBoundingClientRect() : null;
        const dockRect = dock ? dock.getBoundingClientRect() : null;
        document.querySelector('[data-testid="whisper-open-dossier-btn"]')?.click();
        await waitRaf(6);
        const sheet = document.querySelector('[data-testid="slide-over-inspection-sheet"]')?.getBoundingClientRect();
        const hudWhenOpen = document.querySelector('[data-testid="whisper-stage-hud"]');
        const sheetHidesWhisperHud = Boolean(hudWhenOpen?.className.includes('max-sm:opacity-0'));
        const hamburger = document.querySelector('button[aria-label="Open Navigation Menu"]');
        let backdropCoversSheet = false;
        let backdropCoversDock = false;
        let backdropTop = null;
        if (hamburger && sheet && dockRect) {
          hamburger.click();
          await waitRaf(6);
          const bdRect = document.querySelector('[data-testid="mobile-menu-backdrop"]')?.getBoundingClientRect();
          backdropTop = bdRect ? bdRect.top : null;
          const menuDialog = document.querySelector('[aria-label="Mobile Navigation"]')?.getBoundingClientRect();
          const testY = menuDialog ? Math.min(sheet.bottom - 20, menuDialog.bottom + 40) : sheet.bottom - 20;
          const sheetMidX = Math.min(window.innerWidth - 20, Math.max(20, sheet.left + sheet.width / 2));
          backdropCoversSheet = document.elementFromPoint(sheetMidX, testY)?.getAttribute('data-testid') === 'mobile-menu-backdrop';
          backdropCoversDock = document.elementFromPoint(dockRect.left + dockRect.width / 2, dockRect.top + dockRect.height / 2)?.getAttribute('data-testid') === 'mobile-menu-backdrop';
          document.querySelector('button[aria-label="Close Navigation Menu"]')?.click();
          await waitRaf(4);
        }
        document.querySelector('[data-testid="close-inspection-sheet-btn"]')?.click();
        await waitRaf(6);
        const sc = window.__sceneController;
        sc.animateTick(0.016);
        const hotspots0 = sc ? sc.getProjectedHotspots(0) : [];
        const maxHotspotYPercent = hotspots0.length > 0 ? Math.max(...hotspots0.map((p) => p.yPercent)) : null;
        return {
          navBottom: nav ? nav.bottom : null,
          timelineTop: timeline ? timeline.top : null,
          timelineBottom: timeline ? timeline.bottom : null,
          timelineTrackWidth: timelineTrack ? timelineTrack.width : 0,
          sheetTop: sheet ? sheet.top : null,
          sheetBottom: sheet ? sheet.bottom : null,
          sheetLeft: sheet ? sheet.left : null,
          hudBottom: hudRect ? hudRect.bottom : null,
          hudHeight: hudRect ? hudRect.height : null,
          dockTop: dockRect ? dockRect.top : null,
          backdropTop,
          backdropCoversSheet,
          backdropCoversDock,
          sheetHidesWhisperHud,
          maxHotspotYPercent,
          mobileFov: sc ? sc.getCurrentFov() : null,
        };
      })()`,
      returnByValue: true,
    });
    await settleRenderFrames(6);
    await takeScreenshot('mobile_act1_portrait.png');

    // 4. Real Smooth-Motion (prefers-reduced-motion: no-preference, CSS scroll-behavior: smooth active) timeline scrub & wheel interrupt checks
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1280,
      height: 800,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await send('Emulation.setEmulatedMedia', {
      media: 'screen',
      features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }],
    });
    const smoothMotionMetrics = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        window.dispatchEvent(new Event('resize'));
        const enableAnimBtn = document.querySelector('button[aria-label="Enable 3D Animations"]');
        if (enableAnimBtn) enableAnimBtn.click();
        const sc = window.__sceneController;
        sc.setReducedMotion(false);
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 120));

        const htmlScrollBehavior = getComputedStyle(document.documentElement).scrollBehavior;
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        const track = document.querySelector('[data-testid="cinema-timeline-track"]');
        const tr = track.getBoundingClientRect();

        // 4a. Focus optical-core, then ArrowRight must jump immediately (not 600ms smooth lag) & release focus
        document.querySelector('[data-testid="whisper-subtarget-optical-core"]')?.click();
        await new Promise((r) => setTimeout(r, 250));
        track.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
        const arrowImmediateY = window.scrollY;
        const arrowClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null;

        // 4b. Re-focus optical-core, click 50% on timeline -> eased flight must reach ~50% (NOT stall at 2px under CSS scroll-behavior: smooth)
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 100));
        document.querySelector('[data-testid="whisper-subtarget-optical-core"]')?.click();
        await new Promise((r) => setTimeout(r, 220));
        track.dispatchEvent(new PointerEvent('pointerdown', { clientX: tr.left + tr.width * 0.50, bubbles: true, pointerId: 11 }));
        track.dispatchEvent(new PointerEvent('pointerup', { clientX: tr.left + tr.width * 0.50, bubbles: true, pointerId: 11 }));
        await new Promise((r) => setTimeout(r, 950));
        const smoothClickEndY = window.scrollY;
        const smoothClickClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null;

        // 4c. Pointer drag on timeline track must track pointer immediately (zero lag)
        track.dispatchEvent(new PointerEvent('pointerdown', { clientX: tr.left + tr.width * 0.15, bubbles: true, pointerId: 12 }));
        await new Promise((r) => setTimeout(r, 30));
        track.dispatchEvent(new PointerEvent('pointermove', { clientX: tr.left + tr.width * 0.65, bubbles: true, pointerId: 12 }));
        const dragImmediateY = window.scrollY;
        track.dispatchEvent(new PointerEvent('pointerup', { clientX: tr.left + tr.width * 0.65, bubbles: true, pointerId: 12 }));

        // 4d. Mid-flight page wheel interrupt during cross-act Focus 3D Core as real quintic flight enters Act 2 clears focus & syncs sheet to Act 02
        document.querySelector('[data-testid="close-inspection-sheet-btn"]')?.click();
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 120));
        document.querySelector('[data-testid="whisper-open-dossier-btn"]')?.click();
        await new Promise((r) => setTimeout(r, 80));
        const sec4 = document.querySelector('[data-sheet-chapter="4"]');
        const focusCoreBtn = sec4 && Array.from(sec4.querySelectorAll('button')).find((b) => b.textContent.includes('Focus 3D Core'));
        focusCoreBtn?.click();
        // Wait until the real smooth flight naturally enters Act 2 (#timeline, ~800..1500px), then interrupt with page wheel
        const waitStart = Date.now();
        while (Date.now() - waitStart < 1500 && window.scrollY < 820) {
          await new Promise((r) => setTimeout(r, 20));
        }
        window.dispatchEvent(new WheelEvent('wheel', { deltaY: 120, bubbles: true }));
        const interruptedY = window.scrollY;
        await new Promise((r) => setTimeout(r, 250));
        const sheet = document.querySelector('[data-testid="slide-over-inspection-sheet"]');
        const activeNavAfterInterrupt = document.querySelector('header nav div.hidden button.text-white.font-semibold')?.textContent?.trim() ?? '';
        const wheelInterruptStoppedFlight = Math.abs(window.scrollY - interruptedY) < 80 && window.scrollY < 2800;
        const wheelInterruptClearedFocus = sc.getCameraRig().getActiveFocusTarget() === null;
        const navPrefix = activeNavAfterInterrupt.slice(0, 2);
        const expectedActByNav: Record<string, string> = {
          '01': 'Act 01',
          '02': 'Act 02',
          '03': 'Act 03',
          '04': 'Act 04',
          '05': 'Act 05',
          '06': 'Act 06',
        };
        const expectedActPrefix = expectedActByNav[navPrefix] ?? 'Act 02';
        const wheelInterruptSyncedSheet =
          Boolean(expectedActByNav[navPrefix]) &&
          (sheet?.querySelector('span.uppercase')?.textContent?.trim() ?? '').startsWith(expectedActPrefix);

        // 4e. Live Chrome verification of unmuted Web Audio API synthesis energy & mute reset
        document.querySelector('[data-testid="close-inspection-sheet-btn"]')?.click();
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 80));
        sc.setReducedMotion(false);
        const audioBtn = document.querySelector('button[aria-label="Enable Procedural Web Audio"]');
        if (audioBtn) audioBtn.click();
        try {
          await sc.getAudioContext()?.resume?.();
        } catch {}
        sc.playHarmonicHum(220, 0.45);
        await new Promise((r) => setTimeout(r, 40));

        const audioEnabledOnUnmute = sc.isAudioEnabled();
        const audioContextState = sc.getAudioContext()?.state ?? null;
        const audioEnergyOnUnmute = sc.getSoundEngine().getAudioEnergy();

        // Mute audio again and verify energy resets cleanly
        const muteBtn = document.querySelector('button[aria-label="Mute Procedural Web Audio"]');
        if (muteBtn) muteBtn.click();
        const audioDisabledOnMute = !sc.isAudioEnabled();
        const audioEnergyOnMute = sc.getSoundEngine().getAudioEnergy();

        return {
          htmlScrollBehavior,
          maxScroll,
          arrowImmediateY,
          arrowClearedFocus,
          smoothClickEndY,
          smoothClickClearedFocus,
          dragImmediateY,
          wheelInterruptStoppedFlight,
          wheelInterruptClearedFocus,
          wheelInterruptSyncedSheet,
          audioEnabledOnUnmute,
          audioContextState,
          audioEnergyOnUnmute,
          audioDisabledOnMute,
          audioEnergyOnMute,
        };
      })()`,
      returnByValue: true,
    });

    // 5. Act 1 Executive Editorial Portrait Dossier & Atelier GLB Strata Separation Verification in Real Chrome
    const dossierPortraitMetricsRes = await send('Runtime.evaluate', {
      awaitPromise: true,
      expression: `(async () => {
        const sc = window.__sceneController;
        sc.setReducedMotion(true);
        sc.clearSubTargetFocus();
        const tlTrack = document.querySelector('[data-testid="cinema-timeline-track"]');
        if (tlTrack) {
          tlTrack.dispatchEvent(new PointerEvent('pointerout', { bubbles: true, relatedTarget: document.body }));
          tlTrack.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, relatedTarget: document.body }));
        }
        window.scrollTo({ top: 0, behavior: 'instant' });
        window.dispatchEvent(new Event('scroll'));
        await new Promise((r) => setTimeout(r, 80));

        const root = sc.getAvatarRig()?.getObjectByName('Act1StudioGLB');
        const t1 = root?.getObjectByName('Prop_Blueprint_Tier1');
        const t3 = root?.getObjectByName('Prop_Blueprint_Tier3');
        const baseY1 = t1 ? t1.position.y : null;
        const baseY3 = t3 ? t3.position.y : null;
        sc.triggerSceneAction('explode_strata', { exploded: true });
        for (let i = 0; i < 6; i++) sc.animateTick(0.016);
        const explodedY1 = t1 ? t1.position.y : null;
        const explodedY3 = t3 ? t3.position.y : null;
        sc.triggerSceneAction('explode_strata', { exploded: false });
        for (let i = 0; i < 6; i++) sc.animateTick(0.016);

        const dossierBtn = document.querySelector('[data-testid="whisper-open-dossier-btn"]');
        if (dossierBtn) dossierBtn.click();
        await new Promise((r) => setTimeout(r, 380));
        const img = document.querySelector('[data-testid="executive-editorial-portrait"]');
        if (img && !img.complete) {
          await new Promise((res) => {
            img.addEventListener('load', res, { once: true });
            img.addEventListener('error', res, { once: true });
            setTimeout(res, 1500);
          });
        }
        const glErr = sc.getRenderer()?.getContext()?.getError?.() ?? 0;
        return {
          portraitComplete: Boolean(img?.complete),
          portraitNaturalW: img?.naturalWidth ?? 0,
          portraitNaturalH: img?.naturalHeight ?? 0,
          tier1Delta: baseY1 !== null && explodedY1 !== null ? explodedY1 - baseY1 : null,
          tier3Delta: baseY3 !== null && explodedY3 !== null ? explodedY3 - baseY3 : null,
          glErr,
        };
      })()`,
      returnByValue: true,
    });
    await settleRenderFrames(8);
    await takeScreenshot('real_screen_act1_dossier_portrait.png');
    await send('Runtime.evaluate', {
      expression: `(() => {
        document.querySelector('[data-testid="close-inspection-sheet-btn"]')?.click();
      })()`,
    });
    await settleRenderFrames(4);
    // Diagnostic live WebGL2 studio lighting close-up of Designer Vinyl Companion (not part of 9 regression baselines)
    await send('Runtime.evaluate', {
      expression: `(() => {
        const sc = window.__sceneController;
        if (!sc) return;
        sc.setReducedMotion(true);
        const renderer = sc.getRenderer();
        renderer.setAnimationLoop(null);
        const cam = sc.getCamera();
        const rig = sc.getAvatarRig();
        cam.fov = 36;
        cam.position.set(rig.position.x - 0.24, rig.position.y + 0.16, rig.position.z + 0.86);
        cam.lookAt(rig.position.x, rig.position.y + 0.13, rig.position.z);
        cam.updateProjectionMatrix();
        cam.updateMatrixWorld(true);
        renderer.render(sc.getScene(), cam);
      })()`,
    });
    await takeScreenshot('companion_act1_closeup.png');
    const dossierPortraitMetrics = dossierPortraitMetricsRes?.result?.value;

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
      act5DockMetrics: act5DockMetrics?.result?.value,
      subtargetPoseMetrics: subtargetPoseMetrics?.result?.value,
      shortDesktopMetrics: shortDesktopMetrics?.result?.value,
      tabletMetrics: tabletMetrics?.result?.value,
      mobileMetrics: mobileMetrics?.result?.value,
      smoothMotionMetrics: smoothMotionMetrics?.result?.value,
      dossierPortraitMetrics,
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
      browserWarnings,
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
        if (reqPath === '/index.html') {
          const html = fs
            .readFileSync(filePath, 'utf8')
            .replace(/<link[^>]*fonts\.(googleapis|gstatic)\.com[^>]*>/gi, '');
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(html);
        } else {
          res.writeHead(200, { 'Content-Type': MIME_TYPES[ext] || 'application/octet-stream' });
          fs.createReadStream(filePath).pipe(res);
        }
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

      // Verify zero browser exceptions and zero WebGLProgram / FXC X4122 shader warnings occurred
      expect(results.browserErrors.length).toBe(0);
      const shaderWarnings = (results.browserWarnings ?? []).filter((w: string) => /X4122|WebGLProgram/i.test(w));
      expect(shaderWarnings).toHaveLength(0);

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
        expect(results.act1Metrics.hasStylizedCompanion).toBe(true);
        expect(results.act1Metrics.companionActiveClip).toBe('Idle_Breathing');
        expect(results.act1Metrics.hasCompanionWhisperCaption).toBe(true);
      }

      // Verify Interactive Core Strata Explosion Dynamics in real browser
      if (results.explodedMetrics) {
        expect(results.explodedMetrics.isExploded).toBe(true);
        expect(results.explodedMetrics.tier1Y).toBeGreaterThan(0.65);
        expect(results.explodedMetrics.tier3Y).toBeLessThan(-0.55);
        expect(results.explodedMetrics.companionActiveClip).toBe('Gesture_Present');
      }

      // Verify DEF-09: Synchronous camera and avatar travel during Act 1 -> 2 transition
      if (results.transMetrics) {
        expect(results.transMetrics.avatarZ).toBeLessThan(5.10);
        expect(results.transMetrics.camZ).toBeLessThan(8.50);
        expect(results.transMetrics.companionActiveClip).toBe('Walk_Forward');
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

      if (results.act5DockMetrics) {
        expect(results.act5DockMetrics.act5After).toBe(!results.act5DockMetrics.act5Before);
        expect(results.act5DockMetrics.act1After).toBe(results.act5DockMetrics.act1Before);
      }

      if (results.subtargetPoseMetrics) {
        expect(results.subtargetPoseMetrics.openState).toBe('true');
        expect(results.subtargetPoseMetrics.activePose).toBe('keynote_present');
        expect(results.subtargetPoseMetrics.resetPose).toBe('neutral');
        expect(results.subtargetPoseMetrics.hasGltfAvatarOnStage).toBe(false);
        expect(results.subtargetPoseMetrics.stylizedRigVisible).toBe(false);
        expect(results.subtargetPoseMetrics.architecturalCenterpieceMode).toBe(true);
        expect(results.subtargetPoseMetrics.hasAtelierGlb).toBe(true);
        expect(results.subtargetPoseMetrics.atelierNodeCount).toBe(9);
        expect(results.subtargetPoseMetrics.hasStudioEnvRT).toBe(true);
        expect(results.subtargetPoseMetrics.atelierMetallicHasEnvMap).toBe(true);
        expect(results.subtargetPoseMetrics.opticalGlassIsPhysical).toBe(true);
        expect(results.subtargetPoseMetrics.sheetScrollTop).toBe(0);
        expect(results.subtargetPoseMetrics.closeBtnVisibleInSheet).toBe(true);
        expect(results.subtargetPoseMetrics.navClearsTimeline).toBe(true);
        expect(results.subtargetPoseMetrics.sheetClearsDock).toBe(true);
        expect(results.subtargetPoseMetrics.sheetClearsTimeline).toBe(true);
        expect(results.subtargetPoseMetrics.peekSheetOpacity).toBeLessThan(0.2);
        expect(results.subtargetPoseMetrics.allFocusFramingClear).toBe(true);
        expect(results.subtargetPoseMetrics.hoverTooltipClearsTimeline).toBe(true);
        expect(results.subtargetPoseMetrics.sheetClickThroughBlocked).toBe(true);
        expect(results.subtargetPoseMetrics.sheetFramingAllActsClear).toBe(true);
        expect(results.subtargetPoseMetrics.tabSwitchClearedFocus).toBe(true);
        expect(results.subtargetPoseMetrics.tabSwitchCamZ).toBeLessThan(-40);
        expect(results.subtargetPoseMetrics.crossActFrontierVisible).toBe(true);
        expect(results.subtargetPoseMetrics.crossActScrollProgress).toBeGreaterThanOrEqual(0.75);
        expect(results.subtargetPoseMetrics.navbarClearedFocus).toBe(true);
        expect(results.subtargetPoseMetrics.navbarSyncedSheetHeader).toBe(true);
        expect(results.subtargetPoseMetrics.scrubCamZBefore).toBeCloseTo(7.20, 1);
        expect(results.subtargetPoseMetrics.scrubKeyClearedFocus).toBe(true);
        expect(results.subtargetPoseMetrics.scrubKeyCamZ).toBeGreaterThan(8.3);
        expect(results.subtargetPoseMetrics.scrubKeyProgress).toBeGreaterThan(0.02);
        expect(results.subtargetPoseMetrics.scrubPointerClearedFocus).toBe(true);
        expect(results.subtargetPoseMetrics.sameTabThenScrollSyncedAct2).toBe(true);
        expect(results.subtargetPoseMetrics.sceneEnvIsNull).toBe(true);
        expect(results.subtargetPoseMetrics.glError).toBe(0);
        expect(results.subtargetPoseMetrics.checkShaderErrorsActive).toBe(true);
      }

      if (results.shortDesktopMetrics) {
        expect(results.shortDesktopMetrics.navBottom!).toBeLessThanOrEqual(results.shortDesktopMetrics.timelineTop!);
        expect(results.shortDesktopMetrics.navHeight!).toBeLessThanOrEqual(56);
        expect(results.shortDesktopMetrics.navOverflowX).toBe(0);
        expect(results.shortDesktopMetrics.timelineBottom!).toBeLessThanOrEqual(results.shortDesktopMetrics.sheetTop!);
        expect(results.shortDesktopMetrics.sheetBottom!).toBeLessThanOrEqual(results.shortDesktopMetrics.dockTop!);
        expect(results.shortDesktopMetrics.minHeadClearancePx!).toBeGreaterThan(0);
      }

      if (results.tabletMetrics) {
        expect(results.tabletMetrics.navBottom!).toBeLessThanOrEqual(results.tabletMetrics.timelineTop!);
        expect(results.tabletMetrics.navHeight!).toBeLessThanOrEqual(56);
        expect(results.tabletMetrics.timelineBottom!).toBeLessThanOrEqual(results.tabletMetrics.sheetTop!);
        expect(results.tabletMetrics.sheetBottom!).toBeLessThanOrEqual(results.tabletMetrics.dockTop!);
        expect(results.tabletMetrics.sheetLeft!).toBeLessThan(768);
        expect(results.tabletMetrics.backdropTop).toBe(0);
        expect(results.tabletMetrics.backdropCoversSheet).toBe(true);
        expect(results.tabletMetrics.backdropCoversDock).toBe(true);
      }

      if (results.mobileMetrics) {
        expect(results.mobileMetrics.navBottom!).toBeLessThanOrEqual(results.mobileMetrics.timelineTop!);
        expect(results.mobileMetrics.timelineBottom!).toBeLessThanOrEqual(results.mobileMetrics.sheetTop!);
        expect(results.mobileMetrics.sheetBottom!).toBeLessThanOrEqual(results.mobileMetrics.dockTop!);
        expect(results.mobileMetrics.sheetLeft!).toBeLessThan(375);
        expect(results.mobileMetrics.hudBottom).not.toBeNull();
        expect(results.mobileMetrics.dockTop).not.toBeNull();
        expect(results.mobileMetrics.hudBottom!).toBeLessThanOrEqual(results.mobileMetrics.dockTop!);
        expect(results.mobileMetrics.hudHeight!).toBeLessThanOrEqual(210);
        expect(results.mobileMetrics.timelineTrackWidth).toBeGreaterThan(120);
        expect(results.mobileMetrics.sheetHidesWhisperHud).toBe(true);
        expect(results.mobileMetrics.maxHotspotYPercent!).toBeLessThanOrEqual(54);
        expect(results.mobileMetrics.backdropTop).toBe(0);
        expect(results.mobileMetrics.backdropCoversSheet).toBe(true);
        expect(results.mobileMetrics.backdropCoversDock).toBe(true);
        expect(results.mobileMetrics.mobileFov).toBeGreaterThan(46);
      }

      if (results.smoothMotionMetrics) {
        const sm = results.smoothMotionMetrics;
        expect(sm.htmlScrollBehavior).toBe('smooth');
        expect(sm.arrowClearedFocus).toBe(true);
        expect(sm.arrowImmediateY).toBeGreaterThanOrEqual(Math.round(sm.maxScroll * 0.04));
        expect(sm.smoothClickClearedFocus).toBe(true);
        expect(sm.smoothClickEndY).toBeGreaterThanOrEqual(Math.round(sm.maxScroll * 0.45));
        expect(sm.smoothClickEndY).toBeLessThanOrEqual(Math.round(sm.maxScroll * 0.55));
        expect(sm.dragImmediateY).toBeGreaterThanOrEqual(Math.round(sm.maxScroll * 0.60));
        expect(sm.wheelInterruptStoppedFlight).toBe(true);
        expect(sm.wheelInterruptClearedFocus).toBe(true);
        expect(sm.wheelInterruptSyncedSheet).toBe(true);
        expect(sm.audioEnabledOnUnmute).toBe(true);
        expect(sm.audioContextState).toBe('running');
        expect(sm.audioEnergyOnUnmute).toBeGreaterThan(0.25);
        expect(sm.audioDisabledOnMute).toBe(true);
        expect(sm.audioEnergyOnMute).toBe(0);
      }

      if (results.dossierPortraitMetrics) {
        const dp = results.dossierPortraitMetrics;
        expect(dp.portraitComplete).toBe(true);
        expect(dp.portraitNaturalW).toBe(600);
        expect(dp.portraitNaturalH).toBe(800);
        expect(dp.tier1Delta).toBeGreaterThan(0.25);
        expect(dp.tier3Delta).toBeLessThan(-0.10);
        expect(dp.glErr).toBe(0);
      }

      // Verify all screenshots against golden baselines with 1.5% pixel mismatch threshold (AC-VISUAL-01, AC-VISUAL-03)
      const baselinesDir = path.resolve(rootDir, 'src/test/baselines');
      const diffResults: Array<{ name: string; diffRatio: number; diffPixels: number; totalPixels: number; match: boolean; diffPath?: string }> = [];

      for (const [, filePath] of Object.entries(results.screenshots)) {
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
