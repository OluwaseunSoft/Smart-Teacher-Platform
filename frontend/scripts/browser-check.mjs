// Browser smoke check with isolated API fixtures; no accounts or live data are changed.
// Run with the Vite server available: node scripts/browser-check.mjs
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const base = process.env.CHECK_URL || "http://127.0.0.1:5173";
const artifacts = await mkdtemp(join(tmpdir(), "suhail-ui-check-"));
const port = 19000 + Math.floor(Math.random() * 1000);
const browser = spawn(process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe", [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  `--remote-debugging-port=${port}`, `--user-data-dir=${join(artifacts, "profile")}`, "about:blank",
], { windowsHide: true, stdio: "ignore" });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
try {
  let targets;
  for (let i = 0; i < 100; i++) {
    try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); break; }
    catch { await delay(200); }
  }
  assert(targets?.length, "Chrome debugging endpoint must be available");
  socket = new WebSocket(targets.find(target => target.type === "page").webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let id = 0;
  const pending = new Map();
  const errors = [];
  const requests = [];
  const messages = [];
  let empty = false;
  const user = { id: 999, display_name: "Alex", email: "fixture@example.test", role: "student", grade: 9, language: "en", timezone: "Africa/Lagos" };
  const dashboard = {
    streak: { current: 5, longest: 12 }, topics_total: 24, topics_covered: 16,
    average_mastery: 0.72, due_reviews: 3, achievements_unlocked: 4, achievements_total: 12,
    active_plan: { completed_items: 4, total_items: 12, percent_complete: 0.3333 }, study_minutes: 45,
    subject_progress: [
      { subject: "Biology", total: 8, covered: 6, mastery: 0.78 },
      { subject: "Mathematics", total: 10, covered: 7, mastery: 0.65 },
      { subject: "Arabic Literature", total: 6, covered: 3, mastery: 0.52 },
    ],
    score_trend: [60, 72, 65, 80, 78, 86, 92].map((score, i) => ({ date: `2026-10-${12 + i}`, score: score / 100, attempts: 10 })),
    upcoming_exams: [{ id: 1, title: "Biology chapter quiz", exam_date: "2026-11-02" }],
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const requestId = ++id;
    pending.set(requestId, { resolve, reject });
    socket.send(JSON.stringify({ id: requestId, method, params }));
  });
  socket.onmessage = event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const request = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) request?.reject(new Error(JSON.stringify(message.error)));
      else request?.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") errors.push(message.params.exceptionDetails.exception?.description || message.params.exceptionDetails.text);
    if (message.method === "Runtime.consoleAPICalled") messages.push(message.params.args.map(arg => arg.value || arg.description));
    if (message.method === "Network.loadingFailed") messages.push(message.params);
    if (message.method === "Fetch.requestPaused") {
      const { requestId, request } = message.params;
      const path = new URL(request.url).pathname;
      requests.push(path);
      let data = [];
      if (path === "/api/auth/me") data = user;
      else if (path === "/api/lessons/123") data = {
        id: 123, material_id: 1, title: "الأدب العربي", objectives: ["فهم النصوص العربية"],
        content: "# English heading\n\nAn English introduction.\n\n## الأدب العربي\n\nهذه فقرة باللغة العربية تشرح الدرس ويجب محاذاتها إلى اليمين حتى عندما تكون الواجهة باللغة الإنجليزية.\n\n- نقطة عربية للتعلّم\n\n> اقتباس باللغة العربية\n\n```python\nprint('hello')\n```",
      };
      else if (path === "/api/notifications") data = { items: [], unread: 2 };
      else if (path === "/api/reviews/queue") data = { items: [] };
      else if (path === "/api/reviews/summary") data = { due_count: 0, scheduled_count: 0, reviewed_count: 0 };
      else if (path === "/api/gamification/dashboard") data = empty ? {
        ...dashboard, topics_total: 0, topics_covered: 0, average_mastery: 0, due_reviews: 0,
        active_plan: null, subject_progress: [], score_trend: [], upcoming_exams: [],
      } : dashboard;
      else if (path === "/api/study-today") data = { items: empty ? [] : [
        { topic_id: 1, title: "Photosynthesis and the world around us", reason: "Review due" },
        { topic_id: 2, title: "Solving equations, one step at a time", reason: "Incorrect answer" },
        { topic_id: 3, title: "The Abbasid Era", reason: "Review due" },
      ] };
      void send("Fetch.fulfillRequest", { requestId, responseCode: 200, responseHeaders: [{ name: "Content-Type", value: "application/json" }], body: Buffer.from(JSON.stringify(data)).toString("base64") }).catch(error => errors.push(error.message));
    }
  };
  await send("Page.enable");
  await send("Runtime.enable");
  await send("Network.enable");
  await send("Network.setBypassServiceWorker", { bypass: true });
  await send("Fetch.enable", { patterns: [{ urlPattern: `${base}/api/*`, requestStage: "Request" }] });
  await send("Page.addScriptToEvaluateOnNewDocument", { source: `localStorage.setItem('suhail.access_token','fixture-token');` });
  const evaluate = async expression => {
    const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  };
  const waitFor = async expression => {
    for (let i = 0; i < 100; i++) { if (await evaluate(`Boolean(${expression})`)) return; await delay(100); }
    throw new Error(`Timed out: ${expression}\n${JSON.stringify({ errors, requests, messages, page: await evaluate("document.body.outerHTML.slice(0, 1800)"), url: await evaluate("location.href") })}`);
  };
  const viewport = async (width, height) => {
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
    await delay(150);
  };
  const screenshot = async name => {
    await delay(200); // Let short color transitions settle before capturing.
    const { cssContentSize } = await send("Page.getLayoutMetrics");
    const { data } = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width: cssContentSize.width, height: cssContentSize.height, scale: 1 } });
    await writeFile(join(artifacts, `${name}.png`), Buffer.from(data, "base64"));
  };
  const noOverflow = async name => assert(await evaluate("document.documentElement.scrollWidth <= innerWidth"), `${name}: no horizontal overflow`);

  await viewport(1440, 1000);
  await send("Page.navigate", { url: base });
  await waitFor("document.querySelector('.dashboard-stats') && document.querySelectorAll('.study-topic-row').length === 3");
  await noOverflow("Desktop");
  assert.equal(await evaluate("document.querySelector('[aria-label=\"Active plan\"]').getAttribute('aria-valuenow')"), "33");
  await screenshot("desktop-dark");
  for (const width of [768, 1024]) {
    await viewport(width, 1000);
    await noOverflow(`Tablet ${width}`);
  }
  await viewport(1440, 1000);
  await evaluate("document.querySelector('[aria-label=\"Switch to light mode\"]').click()");
  await waitFor("document.querySelector('.app-shell').dataset.theme === 'light'");
  await screenshot("desktop-light");
  await send("Page.reload");
  await delay(500);
  await waitFor("document.querySelector('.dashboard-stats')");
  assert.equal(await evaluate("document.querySelector('.app-shell').dataset.theme"), "light");
  await evaluate("document.querySelector('[aria-label=\"Switch to dark mode\"]').click()");
  await viewport(390, 844);
  await noOverflow("Mobile");
  assert(await evaluate("[...document.querySelectorAll('.mobile-tab')].every(e=>e.getBoundingClientRect().width >= 44 && e.getBoundingClientRect().height >= 44)"));
  await screenshot("mobile-dark");
  await evaluate("document.querySelector('.mobile-tab[aria-expanded]').click()");
  await waitFor("document.querySelector('#more-navigation')");
  assert(await evaluate("document.querySelector('#more-navigation a') === document.activeElement"));
  await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 });
  await waitFor("!document.querySelector('#more-navigation')");
  assert(await evaluate("document.activeElement.matches('.mobile-tab[aria-expanded]')"));
  await evaluate("document.querySelector('#language-select').value = 'ar'; document.querySelector('#language-select').dispatchEvent(new Event('change', { bubbles:true }))");
  await waitFor("document.documentElement.dir === 'rtl'");
  await noOverflow("Arabic mobile");
  await screenshot("mobile-arabic");
  await viewport(320, 740);
  await noOverflow("Small mobile Arabic");
  await viewport(1440, 1000);
  await noOverflow("Arabic desktop");
  await screenshot("desktop-arabic");
  user.language = "en";
  empty = true;
  await send("Page.reload");
  await delay(500);
  await waitFor("document.querySelector('.friendly-empty h3')");
  assert.equal(await evaluate("document.querySelector('.focus-copy a').getAttribute('href')"), "/upload");
  await screenshot("desktop-empty");
  for (const route of ["upload", "library", "tutor", "planner", "reviews", "progress", "settings"]) {
    await evaluate(`history.pushState({}, '', '/${route}'); dispatchEvent(new PopStateEvent('popstate'))`);
    await waitFor("document.querySelector('main h1')");
    await delay(150);
    await noOverflow(route);
    if (route === "upload") await screenshot("upload-dark");
  }
  await evaluate("history.pushState({}, '', '/lessons/123'); dispatchEvent(new PopStateEvent('popstate'))");
  await waitFor("document.querySelector('.prose-lesson h2')");
  for (const language of ["en", "ar"]) {
    await evaluate(`document.querySelector('#language-select').value = '${language}'; document.querySelector('#language-select').dispatchEvent(new Event('change', { bubbles:true }))`);
    await waitFor(`document.documentElement.lang === '${language}'`);
    const blocks = await evaluate(`Array.from(document.querySelectorAll('.prose-lesson p, .prose-lesson h2, .prose-lesson li, .prose-lesson pre')).map(e => ({tag:e.tagName, direction:getComputedStyle(e).direction, alignment:getComputedStyle(e).textAlign}))`);
    assert.deepEqual(blocks.filter(block => block.direction === "rtl").map(block => block.alignment), ["right", "right", "right", "right"]);
    assert(blocks.filter(block => block.direction === "ltr").every(block => block.alignment === "left"));
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.prose-lesson pre')).direction"), "ltr");
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.prose-lesson ul')).direction"), "rtl");
    assert.equal(await evaluate("getComputedStyle(document.querySelector('.prose-lesson blockquote')).borderRightWidth"), "3px");
    await viewport(390, 844);
    await noOverflow(`Mixed-language lesson in ${language}`);
    await screenshot(`arabic-lesson-${language}-interface`);
  }
  assert.deepEqual(errors, [], "No browser exceptions");
  console.log(JSON.stringify({ result: "passed", checks: ["desktop and tablet layouts", "dark/light theme persistence", "mobile touch targets", "More menu keyboard focus", "Arabic RTL at 320px, 390px and desktop", "empty state", "upload, library, tutor, planner, reviews, progress and settings routes", "Arabic paragraphs, headings and lists right-aligned in both interface languages; English and code left-aligned", "no browser exceptions"], artifacts }, null, 2));
} finally {
  socket?.close();
  browser.kill();
}
