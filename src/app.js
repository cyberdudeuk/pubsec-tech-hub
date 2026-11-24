"use strict";
(function () {
  const D = JSON.parse(document.getElementById("hubdata").textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = (u) => (/^https:\/\//.test(u) || /^#[\w-]*$/.test(u) || /^data\/[\w.-]+$/.test(u) ? u : "#");
  const icon = (n) => `<svg class="i" aria-hidden="true"><use href="#i-${esc(n)}"/></svg>`;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage unavailable: preference lasts this visit only */ } },
  };
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const REPO = D.meta.repo;
  const formUrl = (t) => `${REPO}/issues/new?template=${encodeURIComponent(t)}`;
  const src = (id) => (D.sources[id] ? `<a class="src" href="#src-${esc(id)}" title="${esc(D.sources[id].t)}">${esc(id)}</a>` : "");
  const L = D.listings;
  const catIcon = { Messaging: "msg", Payments: "card", Forms: "form", Identity: "id", Design: "palette", "Citizen apps": "phone", AI: "spark", "Web publishing": "globe", APIs: "api" };

  /* ---------- binds and forms ---------- */
  $$("[data-bind=evidence]").forEach((e) => (e.textContent = new Date(D.meta.evidence_date + "T12:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })));
  $$("[data-bind=harvestDate]").forEach((e) => (e.textContent = D.harvest.date || "not yet run"));
  $$("[data-bind=harvestCount]").forEach((e) => (e.textContent = `${D.harvest.found} of ${D.harvest.checked} repositories had a publiccode.yml file`));
  $$("[data-form]").forEach((a) => { a.href = formUrl(a.dataset.form); });

  /* ---------- theme ---------- */
  const setTheme = (t) => { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; };
  setTheme(store.get("hub-theme"));
  $("#themeBtn").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    const t = dark ? "light" : "dark"; setTheme(t); store.set("hub-theme", t);
  });

  /* ---------- views and global navigation ---------- */
  const views = $$("section.view");
  const gnav = $("#gnav");
  gnav.innerHTML = views.map((v) => `<li><a href="#${v.id}" data-v="${v.id}">${icon(v.dataset.icon)}${esc(v.dataset.title)}</a></li>`).join("") +
    `<li class="hidden" id="moreLi"><button class="more" type="button" id="moreBtn" aria-expanded="false" aria-controls="moreMenu">${icon("menu")}More</button></li>`;
  const moreMenu = document.createElement("div"); moreMenu.className = "moremenu"; moreMenu.id = "moreMenu"; moreMenu.hidden = true;
  $("nav.gnav").appendChild(moreMenu);
  function foldNav() {
    const items = $$("#gnav > li:not(#moreLi)"); const moreLi = $("#moreLi");
    items.forEach((li) => li.classList.remove("hidden")); moreLi.classList.add("hidden");
    const avail = gnav.clientWidth; let used = 0; const hidden = [];
    const moreW = 96;
    items.forEach((li, i) => { used += li.offsetWidth + 2; const need = i < items.length - 1 ? moreW : 0; if (used + need > avail) hidden.push(li); });
    if (hidden.length) { moreLi.classList.remove("hidden"); hidden.forEach((li) => li.classList.add("hidden")); }
    moreMenu.innerHTML = hidden.map((li) => li.innerHTML).join("");
    return hidden.length;
  }
  $("#moreBtn").addEventListener("click", (e) => { const open = moreMenu.hidden; moreMenu.hidden = !open; e.currentTarget.setAttribute("aria-expanded", String(open)); });
  moreMenu.addEventListener("click", () => { moreMenu.hidden = true; $("#moreBtn").setAttribute("aria-expanded", "false"); });

  /* ---------- drawer ---------- */
  const drawer = $("#drawer"); const dtog = $("#drawerToggle");
  function setDrawer(open, save) {
    drawer.classList.toggle("closed", !open); dtog.setAttribute("aria-expanded", String(open));
    $(".tl", dtog).textContent = open ? "Hide" : "Show"; if (save) store.set("hub-drawer", open ? "open" : "closed");
  }
  const narrow = window.matchMedia("(max-width:860px)").matches;
  setDrawer(store.get("hub-drawer") ? store.get("hub-drawer") === "open" : !narrow, false);
  dtog.addEventListener("click", () => setDrawer(drawer.classList.contains("closed"), true));
  const changed = new Set(D.meta.changed || []);
  function buildDrawer(view) {
    const hs = $$("h2[id]", view);
    const counts = { "st-list": L.length, "ab-sources": Object.keys(D.sources).length, "ab-defects": D.defects.length, "kn-h-gloss": D.glossary.length, "do-h-req": D.requirements.length, "do-h-rec": D.reconciliation.rows.length, "dv-h-platforms": L.filter((x) => x.kind === "Platform").length };
    $("#drawerTitle").textContent = view.dataset.title;
    $("#drawerBody").innerHTML = `<details open><summary>${icon(view.dataset.icon)}${esc(view.dataset.title)}<span class="cnt">${hs.length}</span></summary>` +
      hs.map((h) => `<a href="#${h.id}">${esc(h.textContent)}${counts[h.id] != null ? `<span class="cnt">${counts[h.id]}</span>` : ""}${changed.has(h.id) ? '<span class="flag">New</span>' : ""}</a>`).join("") + "</details>";
  }
  $("#drawerBody").addEventListener("click", (e) => {
    const a = e.target.closest("a[href^='#']"); if (!a) return;
    const t = document.getElementById(a.getAttribute("href").slice(1));
    const tp = t && t.closest(".tp"); if (tp) activateTab(tp.id);
    if (window.matchMedia("(max-width:860px)").matches) setDrawer(false, false); // overlay on phones: get out of the way
  });

  function show() {
    const id = decodeURIComponent(location.hash.slice(1)) || "overview";
    let target = document.getElementById(id); let view = target && (target.matches("section.view") ? target : target.closest("section.view"));
    if (!view) { view = $("#overview"); target = null; }
    views.forEach((v) => v.classList.toggle("on", v === view));
    $$("#gnav a, #moreMenu a").forEach((a) => (a.dataset.v === view.id ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
    buildDrawer(view);
    document.title = `${view.dataset.title} · Public Sector Tech Hub`;
    if (target && target !== view) { const tp = target.closest(".tp"); if (tp) activateTab(tp.id); target.scrollIntoView(); } else { window.scrollTo(0, 0); setTimeout(() => window.scrollTo(0, 0), 0); }
  }
  window.addEventListener("hashchange", show);

  /* ---------- tabs ---------- */
  function activateTab(panelId) {
    const panel = document.getElementById(panelId); if (!panel) return;
    const list = $(`[aria-controls="${panelId}"]`).closest("[role=tablist]");
    $$("[role=tab]", list).forEach((b) => { const on = b.getAttribute("aria-controls") === panelId; b.setAttribute("aria-selected", String(on)); b.tabIndex = on ? 0 : -1; const p = document.getElementById(b.getAttribute("aria-controls")); if (p) p.classList.toggle("on", on); });
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[role=tab]"); if (b) activateTab(b.getAttribute("aria-controls"));
    const t = e.target.closest("[data-tab-target]"); if (t) setTimeout(() => activateTab(t.dataset.tabTarget), 0);
  });
  document.addEventListener("keydown", (e) => {
    const b = e.target.closest && e.target.closest("[role=tab]"); if (!b || !["ArrowLeft", "ArrowRight"].includes(e.key)) return;
    const tabs = $$("[role=tab]", b.closest("[role=tablist]")); const i = tabs.indexOf(b) + (e.key === "ArrowRight" ? 1 : -1);
    const n = tabs[(i + tabs.length) % tabs.length]; activateTab(n.getAttribute("aria-controls")); n.focus();
  });

  /* ---------- dialogs ---------- */
  $$("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target.closest("[data-close]") || e.target === d) d.close(); }));
  function openListing(id) {
    const x = L.find((l) => l.id === id); if (!x) return;
    $("#dlgTitle").textContent = x.name;
    const links = (x.code || []).map((u) => `<li><a href="${esc(safeUrl(u))}">${esc(u.replace("https://github.com/", ""))}</a></li>`).join("");
    const users = x.users && x.users.length ? `<ul>${x.users.map((u) => `<li>${esc(u.body)}${u.url ? ` (<a href="${esc(safeUrl(u.url))}">their page</a>)` : ""}</li>`).join("")}</ul>` :
      `<p>No public body has declared use here yet. <a href="${esc(formUrl("4-declare-use.yml"))}">Declare that your body uses it</a>.</p>`;
    $("#dlgBody").innerHTML = `<p>${esc(x.summary)}</p>
      <p>${x.pc ? '<span class="badge b-har">Harvested from publiccode.yml</span>' : '<span class="badge b-cur">Curated from public sources</span>'} <span class="tag">${esc(x.kind)}</span><span class="tag">${esc(x.cat)}</span><span class="tag">${esc(x.body)}</span></p>
      <table><tbody><tr><th scope="row">Owner</th><td>${esc(x.owner)}</td></tr><tr><th scope="row">Maturity</th><td>${esc(x.maturity)}${x.pc ? "" : " (the owner has not published a publiccode.yml)"}</td></tr><tr><th scope="row">Licence</th><td>${esc(x.licence)} ${src("S16")}</td></tr><tr><th scope="row">Live service</th><td>${x.live ? `<a href="${esc(safeUrl(x.live))}">${esc(x.live)}</a>` : "No public address listed"}</td></tr></tbody></table>
      <h3>Facts</h3>${x.figures.length ? `<ul>${x.figures.map((f) => `<li>${esc(f.t)} ${src(f.s)}</li>`).join("")}</ul>` : "<p>No published figures found on the evidence date.</p>"}
      <h3>Code</h3><ul>${links}</ul><h3>Declared users</h3>${users}
      <p><a href="${esc(formUrl("3-claim.yml"))}">Claim this listing</a> · <a href="${esc(formUrl("1-correction.yml"))}">Report a correction</a></p>`;
    $("#dlg").showModal();
  }

  /* ---------- store ---------- */
  const uniq = (a) => Array.from(new Set(a)).sort();
  const fill = (sel, vals, all) => { sel.innerHTML = `<option value="">${esc(all)}</option>` + vals.map((v) => `<option>${esc(v)}</option>`).join(""); };
  fill($("#fCat"), uniq(L.map((x) => x.cat)), "All categories");
  fill($("#fBody"), uniq(L.map((x) => x.body)), "All bodies");
  fill($("#fKind"), uniq(L.map((x) => x.kind)), "All kinds");
  fill($("#fLic"), uniq(L.map((x) => x.licence)), "All licences");
  function card(x) {
    return `<button type="button" class="card lcard" data-id="${esc(x.id)}"><span style="display:flex;gap:10px;align-items:center"><span class="ico">${icon(catIcon[x.cat] || "layers")}</span><span><strong>${esc(x.name)}</strong><br><span class="own">${esc(x.owner)}</span></span></span>
      <span>${esc(x.summary)}</span><span>${x.pc ? '<span class="badge b-har">Harvested</span>' : '<span class="badge b-cur">Curated</span>'} <span class="tag">${esc(x.cat)}</span><span class="tag">${esc(x.licence)}</span></span></button>`;
  }
  function filterListings(q, f) {
    const terms = (q || "").toLowerCase().split(/\s+/).filter(Boolean);
    return L.filter((x) => (!f.cat || x.cat === f.cat) && (!f.body || x.body === f.body) && (!f.kind || x.kind === f.kind) && (!f.lic || x.licence === f.lic) &&
      terms.every((t) => [x.name, x.owner, x.summary, x.cat, (x.tags || []).join(" ")].join(" ").toLowerCase().includes(t)));
  }
  function renderStore() {
    const f = { cat: $("#fCat").value, body: $("#fBody").value, kind: $("#fKind").value, lic: $("#fLic").value };
    const s = $("#fSort").value; const r = filterListings($("#fQ").value, f).sort((a, b) => a[s].localeCompare(b[s]));
    $("#storeGrid").innerHTML = r.map(card).join("") || "<p>No listings match. Clear a filter, or look in the other directories.</p>";
    $("#stCount").textContent = `Showing ${r.length} of ${L.length} listings.`;
  }
  ["#fQ", "#fCat", "#fBody", "#fKind", "#fLic", "#fSort"].forEach((s) => $(s).addEventListener("input", renderStore));
  document.addEventListener("click", (e) => { const c = e.target.closest(".lcard"); if (c) openListing(c.dataset.id); });

  /* ---------- overview stats ---------- */
  const figs = L.reduce((n, x) => n + x.figures.length, 0);
  const stats = [[L.length, "listings"], [uniq(L.map((x) => x.owner)).length, "owning bodies or communities"], [figs, "facts, each with a source"], [D.harvest.found, "harvested from publiccode.yml so far"]];
  $("#ovStats").innerHTML = stats.map(([n, l]) => `<div class="card stat"><div class="n" data-n="${n}">${reduced ? n : 0}</div><div class="l">${esc(l)}</div></div>`).join("");
  if (!reduced) $$("#ovStats .n").forEach((el) => { const n = +el.dataset.n; let i = 0; const t = setInterval(() => { i++; el.textContent = Math.round((n * i) / 20); if (i >= 20) clearInterval(t); }, 30); });

  /* ---------- developers, directories, ecosystem ---------- */
  $("#dvPlatforms").innerHTML = L.filter((x) => x.kind === "Platform").map(card).join("");
  $("#dvStandards").innerHTML = D.ecosystem.Standards.map((s) => `<li><a href="${esc(safeUrl(s.u))}">${esc(s.n)}</a></li>`).join("");
  const groups = uniq(D.directories.map((d) => d.g));
  $("#dirList").innerHTML = groups.map((g) => `<h2 id="di-${esc(g.toLowerCase().replace(/\W+/g, "-"))}">${esc(g)}</h2><div class="grid g3">` +
    D.directories.filter((d) => d.g === g).map((d) => `<div class="card"><h3>${icon("link")}<a href="${esc(safeUrl(d.u))}">${esc(d.n)}</a></h3><p>${esc(d.d)}</p></div>`).join("") + "</div>").join("");
  const ek = Object.keys(D.ecosystem);
  $("#ecTabs").innerHTML = ek.map((k, i) => `<button role="tab" aria-selected="${i === 0}" aria-controls="ec-${i}" id="t-ec-${i}">${esc(k)}</button>`).join("");
  $("#ecPanels").innerHTML = ek.map((k, i) => `<div class="tp${i === 0 ? " on" : ""}" role="tabpanel" id="ec-${i}" aria-labelledby="t-ec-${i}"><h2 id="ec-h-${i}">${esc(k)}</h2><ul>${D.ecosystem[k].map((s) => `<li><a href="${esc(safeUrl(s.u))}">${esc(s.n)}</a></li>`).join("")}</ul></div>`).join("");

  /* ---------- knowledge ---------- */
  function renderGloss() {
    const q = $("#gq").value.toLowerCase();
    $("#glist").innerHTML = D.glossary.filter((g) => !q || (g[0] + " " + g[1]).toLowerCase().includes(q)).map((g) => `<dt id="g-${esc(g[0].toLowerCase().replace(/\W+/g, "-"))}"><strong>${esc(g[0])}</strong> <span class="tag">${esc(g[2])}</span></dt><dd>${esc(g[1])}</dd>`).join("");
  }
  $("#gq").addEventListener("input", renderGloss); renderGloss();
  const dict = [["id", "Stable short name of the listing", "derived from name"], ["name", "Product name", "name"], ["kind", "Platform, product, app, component library, tool or directory", "softwareType (mapped)"], ["cat", "Category", "categories (first)"], ["owner", "Owning body or community", "legal.repoOwner or mainCopyrightOwner"], ["body", "Type of body: central, local, NHS or devolved", "editor, at moderation"], ["summary", "One-line description", "description.en-GB or .en shortDescription"], ["maturity", "As declared by the owner, otherwise 'Not declared'", "developmentStatus"], ["licence", "SPDX licence", "legal.license"], ["code", "Repository addresses", "url"], ["live", "Live service or landing page", "landingURL"], ["figures", "Facts with a source each", "never; curated only"], ["users", "Bodies that declared use through the form", "never; declared by each body"], ["pc", "True if harvested from publiccode.yml", "set by the harvester"]];
  $("#dictBody").innerHTML = dict.map((r) => `<tr><td><code>${esc(r[0])}</code></td><td>${esc(r[1])}</td><td>${esc(r[2])}</td></tr>`).join("");
  function graph() {
    const svg = $("#kg"); const W = svg.clientWidth || 800, H = 520; svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const N = [], E = [], idx = {};
    const add = (id, label, type) => { if (idx[id] == null) { idx[id] = N.length; N.push({ id, label, type, x: W / 2 + 200 * Math.cos(N.length), y: H / 2 + 160 * Math.sin(N.length * 1.7), vx: 0, vy: 0 }); } };
    L.forEach((x) => { add(x.id, x.name, "listing"); add("o:" + x.owner, x.owner, "owner"); add("c:" + x.cat, x.cat, "category"); E.push([x.id, "o:" + x.owner], [x.id, "c:" + x.cat]); x.figures.forEach((f) => { add("s:" + f.s, f.s, "source"); E.push([x.id, "s:" + f.s]); }); });
    for (let k = 0; k < 220; k++) {
      for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) { const a = N[i], b = N[j]; const dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy + 0.01, f = 5200 / d2, d = Math.sqrt(d2); a.vx += (dx / d) * f; a.vy += (dy / d) * f; b.vx -= (dx / d) * f; b.vy -= (dy / d) * f; }
      E.forEach(([s, t]) => { const a = N[idx[s]], b = N[idx[t]]; const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) || 1, f = (d - 120) * 0.02; a.vx += (dx / d) * f; a.vy += (dy / d) * f; b.vx -= (dx / d) * f; b.vy -= (dy / d) * f; });
      N.forEach((n) => { n.vx += (W / 2 - n.x) * 0.002; n.vy += (H / 2 - n.y) * 0.003; n.x = Math.max(30, Math.min(W - 30, n.x + n.vx * 0.5)); n.y = Math.max(20, Math.min(H - 20, n.y + n.vy * 0.5)); n.vx *= 0.6; n.vy *= 0.6; });
    }
    const col = { listing: "var(--brand)", owner: "var(--accent)", category: "var(--muted)", source: "var(--ok)" };
    svg.innerHTML = `<title id="kgT">Graph of listings, owners, categories and sources</title>` + E.map(([s, t]) => { const a = N[idx[s]], b = N[idx[t]]; return `<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="var(--line)"/>`; }).join("") +
      N.map((n) => `<g data-node="${esc(n.id)}" tabindex="0" role="button" aria-label="${esc(n.type + ": " + n.label)}" style="cursor:pointer"><circle cx="${n.x.toFixed(1)}" cy="${n.y.toFixed(1)}" r="${n.type === "listing" ? 8 : 6}" fill="${col[n.type]}"/><text x="${(n.x + 10).toFixed(1)}" y="${(n.y + 4).toFixed(1)}">${esc(n.label.length > 22 ? n.label.slice(0, 21) + "…" : n.label)}</text></g>`).join("");
    $("#kgText").innerHTML = L.map((x) => `<li>${esc(x.name)}: owned by ${esc(x.owner)}; category ${esc(x.cat)}${x.figures.length ? "; sources " + esc(uniq(x.figures.map((f) => f.s)).join(", ")) : ""}</li>`).join("");
  }
  $("#kg").addEventListener("click", (e) => { const g = e.target.closest("[data-node]"); if (!g) return; const id = g.dataset.node; if (L.some((x) => x.id === id)) openListing(id); else if (id.startsWith("s:")) location.hash = "src-" + id.slice(2); });
  $("#kg").addEventListener("keydown", (e) => { if (e.key === "Enter") { const g = e.target.closest("[data-node]"); if (g) g.dispatchEvent(new MouseEvent("click", { bubbles: true })); } });
  let graphDone = false;
  document.addEventListener("click", (e) => { if (e.target.closest("#t-kn-graph") && !graphDone) { graphDone = true; setTimeout(graph, 30); } });

  /* ---------- documents and about ---------- */
  $("#needs").innerHTML = "<ul>" + D.user_needs.map((n) => `<li><strong>${esc(n[0])}</strong> ${esc(n[1])}</li>`).join("") + "</ul>";
  $("#reqBody").innerHTML = D.requirements.map((r) => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td><td>${esc(r[2].join(", "))}</td><td><a href="#${esc(r[3])}">${esc(r[3])}</a></td><td>${r[4].map((c) => `<code>${esc(c)}</code>`).join(" ")}</td><td>${esc(r[5])}</td></tr>`).join("");
  $("#recAbout").textContent = D.reconciliation.about;
  $("#recHead").innerHTML = "<tr>" + D.reconciliation.columns.map((c) => `<th scope="col">${esc(c)}</th>`).join("") + "</tr>";
  function renderRec() { const f = $("#recF").value; const rows = D.reconciliation.rows.filter((r) => !f || r[5] === f); $("#recBody").innerHTML = rows.map((r) => "<tr>" + r.map((c, i) => `<td>${i === 5 ? `<strong>${esc(c)}</strong>` : esc(c)}</td>`).join("") + "</tr>").join(""); $("#recCount").textContent = `${rows.length} of ${D.reconciliation.rows.length} rows`; }
  $("#recF").addEventListener("input", renderRec); renderRec();
  $("#defBody").innerHTML = D.defects.map((d) => `<tr><td>${esc(d[0])}</td><td>${esc(d[1])}</td><td>${esc(d[2])}</td><td>${esc(d[3])}</td><td>${esc(d[4])}</td><td>${d[5].map((c) => `<code>${esc(c)}</code>`).join(" ")}</td></tr>`).join("");
  $("#srcList").innerHTML = Object.entries(D.sources).map(([k, s]) => `<li id="src-${esc(k)}"><strong>${esc(k)}</strong> <a href="${esc(safeUrl(s.url))}">${esc(s.t)}</a></li>`).join("");

  /* ---------- search ---------- */
  const IDX = [];
  L.forEach((x) => IDX.push({ t: x.name, d: x.summary, k: "Listing", body: [x.name, x.owner, x.summary, x.cat, x.kind, (x.tags || []).join(" "), x.figures.map((f) => f.t).join(" ")].join(" "), go: () => openListing(x.id), id: x.id }));
  D.glossary.forEach((g) => IDX.push({ t: g[0], d: g[1], k: "Glossary", body: g[0] + " " + g[1], href: "#g-" + g[0].toLowerCase().replace(/\W+/g, "-") }));
  D.directories.forEach((d) => IDX.push({ t: d.n, d: d.d, k: "Directory", body: d.n + " " + d.d + " " + d.g, href: d.u }));
  Object.entries(D.ecosystem).forEach(([k, a]) => a.forEach((s) => IDX.push({ t: s.n, d: k, k: "Link", body: s.n + " " + k, href: s.u })));
  views.forEach((v) => $$("h2[id]", v).forEach((h) => { const p = h.nextElementSibling; IDX.push({ t: h.textContent, d: v.dataset.title, k: "Section", body: h.textContent + " " + (p ? p.textContent : ""), href: "#" + h.id }); }));
  const STOP = new Set("a an and are can do does for from how i in is it me my of on or the to what where which who with you your".split(" "));
  const toks = (s) => String(s).toLowerCase().replace(/[^a-z0-9£.\s-]/g, " ").split(/\s+/).filter((t) => t.length > 1 && !STOP.has(t)).map((t) => t.replace(/(ing|es|s)$/, ""));
  function search(q) {
    const qt = toks(q); if (!qt.length) return [];
    return IDX.map((it) => { const bt = toks(it.body); const tt = toks(it.t); let s = 0; qt.forEach((t) => { if (tt.includes(t)) s += 3; else if (bt.some((b) => b.startsWith(t) || t.startsWith(b) && b.length > 3)) s += 1; }); return { it, s }; })
      .filter((r) => r.s > 0).sort((a, b) => b.s - a.s).map((r) => r.it);
  }
  const resItem = (it, i) => `<div class="card" style="margin:8px 0"><span class="tag">${esc(it.k)}</span> ${it.go ? `<a href="#store" data-r="${i}">${esc(it.t)}</a>` : `<a href="${esc(safeUrl(it.href))}">${esc(it.t)}</a>`}<br><span class="own">${esc(it.d)}</span></div>`;
  let lastRes = [];
  $("#sq").addEventListener("input", () => { lastRes = search($("#sq").value).slice(0, 20); $("#sRes").innerHTML = lastRes.map(resItem).join(""); $("#sCount").textContent = $("#sq").value ? `${lastRes.length} results` : ""; });
  $("#sRes").addEventListener("click", (e) => { const a = e.target.closest("a"); if (!a) return; $("#searchDlg").close(); if (a.dataset.r != null) { e.preventDefault(); location.hash = "store"; lastRes[+a.dataset.r].go(); } });
  $("#searchOpen").addEventListener("click", () => { $("#searchDlg").showModal(); $("#sq").focus(); });
  document.addEventListener("keydown", (e) => { if (e.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); $("#searchOpen").click(); } });

  /* ---------- Ask ---------- */
  function ask(q) {
    const r = search(q);
    if (!r.length) return { html: `<p>I couldn't find that on this site. Try the <a href="#directories">other directories</a>, or <a href="${esc(formUrl("0-contact.yml"))}">ask through the contact form</a>.</p>`, ids: [] };
    const top = r.find((x) => x.k === "Listing");
    let html = "";
    if (top) {
      const x = L.find((l) => l.id === top.id);
      html += `<p><strong>${esc(x.name)}</strong> (${esc(x.owner)}): ${esc(x.summary)}</p>` + (x.figures.length ? `<ul>${x.figures.map((f) => `<li>${esc(f.t)} ${src(f.s)}</li>`).join("")}</ul>` : "") +
        `<p>Licence ${esc(x.licence)}. ${x.live ? `Live: <a href="${esc(safeUrl(x.live))}">${esc(x.live)}</a>. ` : ""}Code: ${x.code.map((u) => `<a href="${esc(safeUrl(u))}">${esc(u.replace("https://github.com/", ""))}</a>`).join(", ")}.</p>`;
    }
    const more = r.filter((x) => x !== top).slice(0, 4);
    if (more.length) html += `<p>Also relevant:</p><ul>${more.map((it) => `<li><span class="tag">${esc(it.k)}</span> ${it.go ? esc(it.t) : `<a href="${esc(safeUrl(it.href))}">${esc(it.t)}</a>`}</li>`).join("")}</ul>`;
    html += `<p class="own">Answer assembled from this hub's own content; check the sources before you rely on it.</p>`;
    return { html, ids: top ? [top.id] : [] };
  }
  $("#askOpen").addEventListener("click", () => { $("#askDlg").showModal(); $("#askIn").focus(); });
  $("#askForm").addEventListener("submit", (e) => { e.preventDefault(); const q = $("#askIn").value.trim(); if (!q) return; $("#askOut").innerHTML = `<div class="ans"><p><strong>You asked:</strong> ${esc(q)}</p>${ask(q).html}</div>`; });

  /* ---------- self-checks, each proved by a negative test ---------- */
  const EMAIL = /[\w.+-]{1,64}@[\w-]{1,63}\.[\w.]{2,}/;
  const C = [
    ["Every fact cites a known source", (d) => d.listings.flatMap((x) => x.figures.filter((f) => !d.sources[f.s]).map((f) => x.id + ":" + f.s)), (d) => { d.listings[0].figures.push({ t: "x", s: "S999" }); }],
    ["Every source address is https or an in-page anchor", (d) => Object.entries(d.sources).filter(([, s]) => !/^(https:\/\/|#)/.test(s.url)).map(([k]) => k), (d) => { d.sources.SX = { t: "x", url: "http://insecure.example" }; }],
    ["No ratings, reviews or stars in any listing", (d) => d.listings.filter((x) => ["rating", "ratings", "reviews", "stars", "score"].some((k) => k in x)).map((x) => x.id), (d) => { d.listings[0].rating = 4.8; }],
    ["Every listing links to https code", (d) => d.listings.filter((x) => !x.code.length || x.code.some((u) => !/^https:\/\//.test(u))).map((x) => x.id), (d) => { d.listings[0].code = ["ftp://x"]; }],
    ["Maturity uses the declared vocabulary only", (d) => d.listings.filter((x) => !["Not declared", "concept", "development", "beta", "stable", "obsolete"].includes(x.maturity)).map((x) => x.id), (d) => { d.listings[0].maturity = "Certified"; }],
    ["No email address in the data", (d) => (EMAIL.test(JSON.stringify(d)) ? ["email found"] : []), (d) => { d.listings[0].summary += " write to someone@example.org"; }],
    ["Requirements trace to known user needs", (d) => { const n = new Set(d.user_needs.map((x) => x[0])); return d.requirements.filter((r) => !r[2].length || r[2].some((x) => !n.has(x))).map((r) => r[0]); }, (d) => { d.requirements[0][2] = ["N99"]; }],
    ["Reconciliation rows are complete", (d) => d.reconciliation.rows.filter((r) => r.length !== 7 || !["Keep", "Improve", "Link", "Drop"].includes(r[5])).map((r) => r[0]), (d) => { d.reconciliation.rows[0][5] = "Maybe"; }],
    ["Search finds GOV.UK Notify for 'text messages'", (d, s) => ((s || search)("text messages").some((x) => x.id === "govuk-notify") ? [] : ["not found"]), null, () => () => [{ id: "other" }]],
    ["Ask declines what the hub does not hold", (d, a) => ((a || ask)("zzqx flurble").ids.length === 0 ? [] : ["answered nonsense"]), null, () => () => ({ ids: ["govuk-notify"] })],
    ["Drawer toggle is labelled and reports its state", (d, el) => { const t = el || dtog; return t.getAttribute("aria-expanded") && t.textContent.trim() ? [] : ["unlabelled toggle"]; }, null, () => document.createElement("button")],
    ["Global navigation fits the screen", (d, w) => ((w != null ? w : $("#gnav").scrollWidth - $("#gnav").clientWidth) <= 1 ? [] : ["navigation overflows"]), null, () => 50],
  ];
  function runChecks() {
    let pass = 0, neg = 0, negTotal = 0;
    const rows = C.map(([name, fn, breakData, fake]) => {
      const p = fn(D); const ok = p.length === 0; if (ok) pass++;
      let negOk = false;
      if (breakData) { const bad = JSON.parse(JSON.stringify(D)); breakData(bad); negOk = fn(bad).length > 0; } else { negOk = fn(D, fake()).length > 0; }
      negTotal++; if (negOk) neg++;
      return `<tr><td>${esc(name)}</td><td class="${ok ? "ok" : "bad"}">${ok ? "Pass" : "Fail: " + esc(p.slice(0, 3).join(", "))}</td><td class="${negOk ? "ok" : "bad"}">${negOk ? "Fails on a bad sample, as it should" : "Did not fail on a bad sample"}</td></tr>`;
    });
    $("#checksBody").innerHTML = rows.join("");
    $("#checksSummary").textContent = `${pass} of ${C.length} checks pass. ${neg} of ${negTotal} negative tests fail as they should.`;
  }

  /* ---------- start ---------- */
  renderStore();
  function layout() { document.documentElement.style.setProperty("--mh", $("#mast").offsetHeight + "px"); foldNav(); }
  window.addEventListener("resize", layout);
  layout(); show(); runChecks();
  window.__hub = { search, ask, runChecks, foldNav };
})();
