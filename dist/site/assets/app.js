const DATA = window.TRI_COUNTY_GUIDE_DATA || { directory_sources: [], resources: [] };
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function textMatch(item, query) {
  const blob = Object.values(item).join(" ").toLowerCase();
  return blob.includes(query.toLowerCase());
}

function uniqueValues(items, field) {
  return [...new Set(items.map(item => item[field]).filter(Boolean))].sort((a, b) => a.localeCompare(b));
}

function populateSelect(select, values, allLabel) {
  if (!select) return;
  select.innerHTML = `<option value="All">${allLabel}</option>` + values.map(value => `<option value="${value}">${value}</option>`).join("");
}

function sourceCard(item) {
  return `
    <article class="source-card" data-county="${escapeHtml(item.county)}" data-kind="${escapeHtml(item.kind)}">
      <div class="source-card__meta">
        <span>${escapeHtml(item.county)}</span>
        <span>${escapeHtml(item.kind)}</span>
      </div>
      <h3><a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${escapeHtml(item.title)}</a></h3>
      <p>${escapeHtml(item.best_for)}</p>
      <p class="action-line">${escapeHtml(item.action)}</p>
      <p class="source-note">Details can change. Open the page, then send an update if this pathway is outdated.</p>
    </article>
  `;
}

function publicDescription(item) {
  const raw = String(item.notes || item.best_for || item.description || "").trim();
  const joinedFlag = (...parts) => parts.join("");
  const genericPhrases = [
    "use as a launch/outreach " + "lead",
    "commercial-directory-only " + "lead",
    joinedFlag("source", "-check"),
    "spreadsheet-" + "backed",
    "not final proof",
    "verify details before spending",
    "visitor-facing listing pulled",
    "creative-directory " + "lead added"
  ];
  const genericText = !raw || genericPhrases.some(phrase => raw.toLowerCase().includes(phrase.toLowerCase()));
  const place = [item.town, item.county, item.state].filter(Boolean).join(", ") || item.county || "the tri-county region";
  const category = publicType(item.category || item.resource_type || item.kind || "local resource").toLowerCase();
  const blob = [item.resource_name, item.title, item.channel, item.category, item.resource_type, item.kind, item.source_type, item.best_for, item.notes]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (!genericText) {
    return raw
      .replace(/source-backed starting points?/gi, "starting points")
      .replace(new RegExp("lead-discovery/" + joinedFlag("source", "-check") + " candidates?", "gi"), "resource entries")
      .replace(/lead bank/gi, "resource list")
      .replace(/Confirm current rules, rates, dates, and acceptance before action\./gi, "Check current details before spending money or announcing placement.");
  }

  let descriptor = "Local business or organization";
  let use = "Use it to identify a possible local contact, then check a current business-owned page or directory listing before outreach.";
  if (/grant|fund|loan|stipend|scholarship|sba|usda|economic development|technical assistance/.test(blob)) {
    descriptor = "Funding or business-support route";
    use = "Use it to find program pages, eligibility details, deadlines, and the office or organization that should confirm the next step.";
  } else if (/artist|arts|creative|gallery|studio|painting|writer|storyteller|tattoo|museum|theat|music|film|photo|design/.test(blob)) {
    descriptor = "Arts, culture, or creative-business listing";
    use = "Use it for artist referrals, exhibitions, workshops, performances, cultural events, and creative cross-promotion questions.";
  } else if (/restaurant|dining|cafe|coffee|bar|brew|bakery|food|beverage|cater|kitchen|grill/.test(blob)) {
    descriptor = "Food, drink, or dining listing";
    use = "Use it for visitor referrals, local event outreach, shop-local campaigns, and cross-promotion questions.";
  } else if (/event|calendar|festival|market|performance|venue|workshop|class/.test(blob)) {
    descriptor = "Event, venue, or calendar route";
    use = "Use it when planning public events, performances, classes, workshops, or calendar visibility across the region.";
  } else if (/chamber|mainstreet|city|town|county|government|library|school|college|visitor center|tourism/.test(blob)) {
    descriptor = "Civic, visitor, or partner-organization route";
    use = "Use it to find formal contact paths, business referrals, community-posting questions, or local program connections.";
  } else if (/media|magazine|newspaper|radio|newsletter|press|advertis|publisher|broadcast|localstash|weekender/.test(blob)) {
    descriptor = "Media, visitor, or advertising route";
    use = "Use it to ask about appropriate announcement, advertising, calendar, newsletter, or public-information routes.";
  } else if (/lodging|hotel|motel|inn|cabin|rv|campground|resort|vacation rental|bed and breakfast|b&b/.test(blob)) {
    descriptor = "Lodging or hospitality listing";
    use = "Use it for visitor referrals, event guest planning, trip-planning pages, and guest-facing information questions.";
  } else if (/shop|retail|store|boutique|mercantile|market|gift|thrift|antique|book|florist|jewelry|maker|artisan/.test(blob)) {
    descriptor = "Shop, maker, or local retail listing";
    use = "Use it for shop-local outreach, event materials, visitor referrals, or local-goods partnerships.";
  }
  return `${descriptor} in ${place}. ${use}`;
}

function publicType(value) {
  return String(value || "Resource")
    .replace(/Outreach lead \/ source-check candidate/gi, "Local resource")
    .replace(/source-linked lead/gi, "listed resource")
    .replace(/Commercial directory lead \/ local business/gi, "Local business listing")
    .replace(/Unknown source/gi, "Source needed");
}

function resourceCard(item) {
  const url = item.website || item.source_url || "";
  const link = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">Open page</a>` : `<a href="/submit/">Send an update</a>`;
  const badges = [item.access_mode, item.source_type]
    .filter(value => value && !/unknown/i.test(String(value)))
    .map(value => `<span class="badge">${escapeHtml(value)}</span>`)
    .join(" ");
  return `
    <article class="resource-item">
      <div class="resource-item__head">
        <h3>${escapeHtml(item.resource_name || "Unnamed resource")}</h3>
      </div>
      <p>${escapeHtml([item.town, item.county, item.state].filter(Boolean).join(", "))} - ${escapeHtml(publicType(item.resource_type))} - ${escapeHtml(publicType(item.category || "General"))}</p>
      ${badges ? `<p>${badges}</p>` : ""}
      <p>${escapeHtml(publicDescription(item))}</p>
      <p class="source-note">If this looks outdated, send a correction so the guide can be updated.</p>
      ${link}
    </article>
  `;
}

function assistantCard(item) {
  const title = item.title || item.resource_name || item.channel || item.place || "Directory result";
  const url = item.url || item.website || item.source_url || "";
  const county = item.county || item.area_served || [item.town, item.state].filter(Boolean).join(", ") || "Regional";
  const category = item.kind || item.resource_type || item.channel_type || item.type || "Directory route";
  const description = publicDescription(item) || item.asks || item.short_description || item.best_for || "Use this result to choose a next contact or page to open.";
  const action = item.action || item.reader_action || "Open the page, then send a correction if details have changed.";
  const typeLabel = item.assistant_type === "Lead bank" ? "Resource" : item.assistant_type || "Directory";
  const sourceLink = url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer" aria-label="Open page for ${escapeHtml(title)}">Open page</a>` : `<span class="source-note">Listing link needed</span>`;
  return `
    <article class="assistant-result" role="listitem">
      <div class="assistant-result__meta">
        <span class="assistant-result__type">${escapeHtml(typeLabel)}</span>
        <span>${escapeHtml(county)}</span>
        <span>${escapeHtml(category)}</span>
      </div>
      <h3>${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(title)}</a>` : escapeHtml(title)}</h3>
      <p>${escapeHtml(description)}</p>
      <p class="action-line">${escapeHtml(action)}</p>
      <div class="assistant-result__actions">
        ${sourceLink}
        <a href="network/index.html" aria-label="Search the full directory for results related to ${escapeHtml(title)}">Search full directory</a>
      </div>
    </article>
  `;
}

function assistantSearch(query) {
  const normalized = String(query || "").trim().toLowerCase();
  const terms = normalized.split(/\s+/).filter(Boolean);
  const pools = [
    ...(DATA.directory_sources || []).map(item => ({ ...item, assistant_type: "Shortcut" })),
    ...(DATA.resources || []).map(item => ({ ...item, assistant_type: "Resource" })),
    ...(DATA.amplifier_channels || []).map(item => ({ ...item, assistant_type: "Amplifier" })),
    ...(DATA.posting_spaces || []).map(item => ({ ...item, assistant_type: "Posting path" }))
  ];
  const scored = pools.map(item => {
    const blob = Object.values(item).join(" ").toLowerCase();
    let score = 0;
    for (const term of terms) {
      if (!term) continue;
      if (blob.includes(term)) score += 3;
      if (String(item.title || item.resource_name || item.channel || item.place || "").toLowerCase().includes(term)) score += 5;
      if (String(item.county || item.area_served || "").toLowerCase().includes(term)) score += 2;
    }
    if (!terms.length && item.assistant_type === "Shortcut") score += 1;
    return { item, score };
  }).filter(entry => entry.score > 0);

  return scored
    .sort((a, b) => b.score - a.score || String(a.item.title || a.item.resource_name || a.item.channel || "").localeCompare(String(b.item.title || b.item.resource_name || b.item.channel || "")))
    .slice(0, 6)
    .map(entry => entry.item);
}

function assistantUrl(key) {
  const root = document.querySelector("[data-directory-assistant]");
  if (!root) return key === "submit" ? "submit/index.html" : "network/index.html";
  return key === "submit" ? root.dataset.submitUrl : root.dataset.networkUrl;
}

function assistantCardWithUrls(item) {
  return assistantCard(item)
    .replaceAll('href="network/index.html"', `href="${escapeHtml(assistantUrl("network"))}"`)
    .replaceAll('href="submit/index.html"', `href="${escapeHtml(assistantUrl("submit"))}"`);
}

function initDirectoryAssistant() {
  const root = document.querySelector("[data-directory-assistant]");
  if (!root) return;
  const toggle = root.querySelector(".directory-assistant__toggle");
  const panel = root.querySelector(".directory-assistant__panel");
  const close = root.querySelector(".directory-assistant__close");
  const form = root.querySelector(".directory-assistant__form");
  const input = root.querySelector("#directory-assistant-query");
  const results = root.querySelector("[data-assistant-results]");
  const status = root.querySelector(".directory-assistant__status");
  const chips = [...root.querySelectorAll("[data-assistant-prompt]")];
  if (!toggle || !panel || !form || !input || !results || !status) return;
  let renderTimer = null;
  let lastFocusedElement = null;
  let returnFocusOnClose = true;

  function setOpen(open, { returnFocus = true } = {}) {
    if (open) {
      lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : toggle;
      if (!panel.open) {
        if (typeof panel.showModal === "function") {
          panel.showModal();
        } else {
          panel.setAttribute("open", "");
        }
      }
      toggle.setAttribute("aria-expanded", "true");
      root.dataset.open = "true";
      window.setTimeout(() => input.focus(), 40);
      return;
    }
    returnFocusOnClose = returnFocus;
    if (panel.open && typeof panel.close === "function") {
      panel.close();
    } else {
      panel.removeAttribute("open");
      syncClosed();
    }
  }

  function syncClosed() {
    toggle.setAttribute("aria-expanded", "false");
    root.dataset.open = "false";
    if (renderTimer) {
      window.clearTimeout(renderTimer);
      renderTimer = null;
    }
    if (returnFocusOnClose && lastFocusedElement && typeof lastFocusedElement.focus === "function") {
      window.setTimeout(() => lastFocusedElement.focus(), 0);
    }
  }

  function render(query) {
    const search = String(query || "").trim();
    const displayQuery = search || "regional help";
    const matches = assistantSearch(displayQuery);
    status.textContent = matches.length
      ? `Showing ${matches.length} route${matches.length === 1 ? "" : "s"} for "${displayQuery}".`
      : `No close match for "${displayQuery}". Try a county, town, or need like funding, events, artist, nonprofit, or media.`;
    results.innerHTML = matches.map(assistantCardWithUrls).join("") || `
      <article class="assistant-result" role="listitem">
        <h3>No direct match yet</h3>
        <p>Open the full directory or submit a correction if a resource should be added.</p>
        <div class="assistant-result__actions">
          <a href="${escapeHtml(assistantUrl("network"))}">Open full directory</a>
          <a href="${escapeHtml(assistantUrl("submit"))}">Submit a correction</a>
        </div>
      </article>
    `;
  }

  toggle.addEventListener("click", () => {
    const shouldOpen = !panel.open;
    setOpen(shouldOpen);
    if (shouldOpen && !results.innerHTML.trim()) {
      render(input.value || "funding events business support");
    }
  });
  close && close.addEventListener("click", () => setOpen(false));
  panel.addEventListener("close", syncClosed);
  panel.addEventListener("click", event => {
    if (event.target !== panel) return;
    const rect = panel.getBoundingClientRect();
    const isBackdropClick = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
    if (isBackdropClick) setOpen(false);
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    render(input.value);
  });
  input.addEventListener("input", () => {
    if (renderTimer) window.clearTimeout(renderTimer);
    if (input.value.trim().length >= 2) {
      renderTimer = window.setTimeout(() => render(input.value), 220);
    }
  });
  chips.forEach(chip => chip.addEventListener("click", () => {
    input.value = chip.dataset.assistantPrompt || "";
    render(input.value);
    input.focus();
  }));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && panel.open && typeof panel.close !== "function") {
      event.preventDefault();
      setOpen(false);
    }
  });
}

function initSourceSearch() {
  const host = document.querySelector("#source-results");
  if (!host) return;
  const input = document.querySelector("#source-search");
  const chips = [...document.querySelectorAll("[data-source-filter]")];
  let county = "All";
  function render() {
    const query = input.value.trim();
    const filtered = DATA.directory_sources
      .filter(item => (county === "All" || item.county === county) && (!query || textMatch(item, query)))
      .sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
    host.innerHTML = filtered.map(sourceCard).join("") || `<p class="section-note">No shortcuts match that search yet.</p>`;
  }
  input.addEventListener("input", render);
  chips.forEach(chip => chip.addEventListener("click", () => {
    county = chip.dataset.sourceFilter;
    chips.forEach(c => c.classList.toggle("is-active", c === chip));
    render();
  }));
  render();
}

function initResourceSearch() {
  const host = document.querySelector("#resource-results");
  if (!host) return;
  const input = document.querySelector("#resource-search");
  const chips = [...document.querySelectorAll("[data-resource-filter]")];
  const typeSelect = document.querySelector("#resource-type-filter");
  const accessSelect = document.querySelector("#access-mode-filter");
  let county = "All";
  populateSelect(typeSelect, uniqueValues(DATA.resources, "resource_type"), "All types");
  populateSelect(accessSelect, uniqueValues(DATA.resources, "access_mode"), "All access modes");
  function render() {
    const query = input.value.trim();
    const resourceType = typeSelect ? typeSelect.value : "All";
    const accessMode = accessSelect ? accessSelect.value : "All";
    const filtered = DATA.resources
      .filter(item => (county === "All" || item.county === county) && (!query || textMatch(item, query)))
      .filter(item => resourceType === "All" || item.resource_type === resourceType)
      .filter(item => accessMode === "All" || item.access_mode === accessMode)
      .sort((a, b) => String(a.resource_name || "").localeCompare(String(b.resource_name || "")))
      .slice(0, 80);
    host.innerHTML = filtered.map(resourceCard).join("") || `<p class="section-note">No local inventory entries match that search.</p>`;
  }
  input.addEventListener("input", render);
  [typeSelect, accessSelect].forEach(select => select && select.addEventListener("change", render));
  chips.forEach(chip => chip.addEventListener("click", () => {
    county = chip.dataset.resourceFilter;
    chips.forEach(c => c.classList.toggle("is-active", c === chip));
    render();
  }));
  render();
}

function initCopyButtons() {
  document.querySelectorAll(".template-card").forEach(card => {
    const button = card.querySelector(".copy-button");
    const pre = card.querySelector("pre");
    if (!button || !pre) return;
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(pre.innerText);
        button.textContent = "Copied";
        setTimeout(() => (button.textContent = "Copy"), 1400);
      } catch {
        button.textContent = "Select text";
      }
    });
  });
}

function initPrintButtons() {
  document.querySelectorAll(".print-button").forEach(button => {
    button.addEventListener("click", () => window.print());
  });
}

function initCornerControls() {
  const backToTop = document.querySelector(".back-to-top");
  if (backToTop) {
    backToTop.addEventListener("click", event => {
      event.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
      });
    });
  }
}

function initAmbientMusic() {
  const toggle = document.querySelector(".music-toggle");
  const trackSelect = document.querySelector(".music-track-select");
  const progress = document.querySelector(".music-progress");
  const timeLabel = document.querySelector(".music-time");
  const volume = document.querySelector(".music-volume");
  const intro = document.querySelector(".intro-curtain");
  const loopAudio = document.getElementById("site-music-loop");
  if (!toggle || !loopAudio) return;

  const MUSIC_KEY = "triCountyPianoMusicV2";
  const TIME_KEY = "triCountyPianoLoopTimeV2";
  const INTRO_KEY = "triCountyLandingIntroSeenV2";
  const TRACK_KEY = "triCountyPianoTrackV2";
  const VOLUME_KEY = "triCountyPianoVolumeV2";
  const savedChoice = localStorage.getItem(MUSIC_KEY);
  const hasSeenIntro = localStorage.getItem(INTRO_KEY) === "seen";
  const saveData = Boolean(navigator.connection && navigator.connection.saveData);
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let isPlaying = false;
  let delayedStartId = null;
  let timeSaveId = null;

  loopAudio.loop = true;
  if (trackSelect) {
    const savedTrack = localStorage.getItem(TRACK_KEY);
    const savedOption = savedTrack ? Array.from(trackSelect.options).find(option => option.dataset.trackId === savedTrack) : null;
    if (savedOption) trackSelect.value = savedOption.value;
    loopAudio.src = trackSelect.value;
  }

  function selectedTrackId() {
    const option = trackSelect ? trackSelect.selectedOptions[0] : null;
    return option ? option.dataset.trackId || option.value : "rael-arroyo-hondo";
  }

  function trackTimeKey(trackId = selectedTrackId()) {
    return `${TIME_KEY}:${trackId}`;
  }

  function formatTime(seconds) {
    const safeSeconds = Number.isFinite(seconds) && seconds > 0 ? seconds : 0;
    const minutes = Math.floor(safeSeconds / 60);
    const remaining = Math.floor(safeSeconds % 60).toString().padStart(2, "0");
    return `${minutes}:${remaining}`;
  }

  function updateProgress() {
    const duration = loopAudio.duration;
    const current = loopAudio.currentTime || 0;
    if (progress) {
      progress.value = Number.isFinite(duration) && duration > 0
        ? String(Math.min(1000, Math.round((current / duration) * 1000)))
        : "0";
    }
    if (timeLabel) {
      timeLabel.textContent = Number.isFinite(duration) && duration > 0
        ? `${formatTime(current)} / ${formatTime(duration)}`
        : formatTime(current);
    }
  }

  function applyVolume({ save = false } = {}) {
    const savedVolume = Number(localStorage.getItem(VOLUME_KEY));
    const fallback = Number.isFinite(savedVolume) ? savedVolume : 58;
    const raw = volume ? Number(volume.value || fallback) : fallback;
    const clamped = Math.max(0, Math.min(100, Number.isFinite(raw) ? raw : fallback));
    if (volume) volume.value = String(clamped);
    const normalized = clamped / 100;
    loopAudio.volume = normalized;
    if (save) localStorage.setItem(VOLUME_KEY, String(clamped));
  }

  applyVolume();
  updateProgress();

  function setButtonState(state) {
    toggle.dataset.state = state;
    if (state === "playing") {
      toggle.textContent = "Stop";
      toggle.setAttribute("aria-pressed", "true");
    } else {
      toggle.textContent = "Play";
      toggle.setAttribute("aria-pressed", "false");
    }
  }

  function rememberTime({ force = false } = {}) {
    if ((!force && !isPlaying) || !Number.isFinite(loopAudio.currentTime)) return;
    localStorage.setItem(trackTimeKey(), String(loopAudio.currentTime));
  }

  function restoreLoopPosition() {
    const savedTime = Number(localStorage.getItem(trackTimeKey()));
    if (Number.isFinite(savedTime) && savedTime > 0) {
      try {
        loopAudio.currentTime = savedTime;
      } catch {
        loopAudio.addEventListener("loadedmetadata", () => {
          try { loopAudio.currentTime = savedTime; } catch {}
        }, { once: true });
      }
    }
  }

  async function startLoop({ userInitiated = false, resume = true, fromBeginning = false } = {}) {
    try {
      if (fromBeginning) {
        loopAudio.currentTime = 0;
      } else if (resume) {
        restoreLoopPosition();
      }
      applyVolume();
      await loopAudio.play();
      isPlaying = true;
      setButtonState("playing");
      localStorage.setItem(MUSIC_KEY, "playing");
      if (timeSaveId) window.clearInterval(timeSaveId);
      timeSaveId = window.setInterval(rememberTime, 900);
      if (userInitiated) {
        rememberTime({ force: true });
      }
      updateProgress();
    } catch {
      isPlaying = false;
      setButtonState("blocked");
    }
  }

  async function startMusic({ userInitiated = false, withIntro = false } = {}) {
    if (withIntro) {
      if (delayedStartId) window.clearTimeout(delayedStartId);
      delayedStartId = window.setTimeout(() => {
        delayedStartId = null;
        startLoop({ userInitiated, fromBeginning: true, resume: false });
      }, 900);
      return;
    }
    await startLoop({ userInitiated, resume: true });
  }

  function stopMusic() {
    rememberTime({ force: true });
    if (delayedStartId) {
      window.clearTimeout(delayedStartId);
      delayedStartId = null;
    }
    if (timeSaveId) {
      window.clearInterval(timeSaveId);
      timeSaveId = null;
    }
    isPlaying = false;
    loopAudio.pause();
    setButtonState("stopped");
    localStorage.setItem(MUSIC_KEY, "stopped");
    updateProgress();
  }

  toggle.addEventListener("click", () => {
    if (isPlaying) {
      stopMusic();
      return;
    }
    startMusic({ userInitiated: true });
  });

  if (trackSelect) {
    trackSelect.addEventListener("change", () => {
      const wasPlaying = isPlaying;
      rememberTime({ force: true });
      if (timeSaveId) {
        window.clearInterval(timeSaveId);
        timeSaveId = null;
      }
      isPlaying = false;
      loopAudio.pause();
      localStorage.setItem(TRACK_KEY, selectedTrackId());
      loopAudio.src = trackSelect.value;
      loopAudio.currentTime = 0;
      updateProgress();
      if (wasPlaying) startLoop({ userInitiated: true, resume: false, fromBeginning: true });
    });
  }

  if (volume) {
    volume.addEventListener("input", () => applyVolume({ save: true }));
  }

  if (progress) {
    progress.addEventListener("input", () => {
      const duration = loopAudio.duration;
      if (!Number.isFinite(duration) || duration <= 0) return;
      loopAudio.currentTime = (Number(progress.value) / 1000) * duration;
      rememberTime({ force: true });
      updateProgress();
    });
  }

  loopAudio.addEventListener("timeupdate", updateProgress);
  loopAudio.addEventListener("loadedmetadata", updateProgress);
  loopAudio.addEventListener("ended", updateProgress);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) rememberTime({ force: true });
  });

  function markIntroComplete() {
    if (!intro) return;
    intro.dataset.introState = "complete";
    localStorage.setItem(INTRO_KEY, "seen");
  }

  function startAfterFirstGesture(event) {
    if (event.target && event.target.closest && event.target.closest(".music-bar")) return;
    if (isPlaying || localStorage.getItem(MUSIC_KEY) === "stopped" || prefersReducedMotion || saveData) return;
    startMusic({ userInitiated: true });
  }

  window.addEventListener("beforeunload", () => rememberTime({ force: true }));

  setButtonState("stopped");
  if (intro) {
    if (hasSeenIntro || prefersReducedMotion) {
      intro.dataset.introState = "skipped";
      if (savedChoice === "playing" && !saveData && !prefersReducedMotion) {
        window.setTimeout(() => startMusic(), 250);
      }
    } else {
      intro.dataset.introState = "playing";
      window.setTimeout(markIntroComplete, 3300);
      if (savedChoice !== "stopped" && !saveData) {
        window.setTimeout(() => startMusic({ withIntro: true }), 120);
        document.addEventListener("pointerdown", startAfterFirstGesture, { once: true });
        document.addEventListener("keydown", startAfterFirstGesture, { once: true });
      }
    }
  } else if (savedChoice === "playing" && !saveData && !prefersReducedMotion) {
    window.setTimeout(() => startMusic(), 250);
  }
}

function initLandingIntro() {
  const intro = document.querySelector(".intro-curtain");
  if (!intro) return;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const key = "triCountyQuickGlowIntroSeenV1";

  function getSeen() {
    try {
      return localStorage.getItem(key) === "seen";
    } catch {
      return true;
    }
  }

  function setSeen() {
    try {
      localStorage.setItem(key, "seen");
    } catch {}
  }

  function complete() {
    intro.dataset.introState = "complete";
    setSeen();
  }

  if (prefersReducedMotion || getSeen()) {
    intro.dataset.introState = "skipped";
    return;
  }

  intro.dataset.introState = "playing";
  intro.addEventListener("animationend", event => {
    if (event.animationName === "introReveal") complete();
  }, { once: true });
  window.setTimeout(complete, 3300);
}

function initListSearch() {
  document.querySelectorAll("[data-list-search]").forEach(panel => {
    const section = panel.closest("section") || document;
    const input = panel.querySelector("[data-list-search-input]");
    const status = panel.querySelector("[data-list-search-status]");
    const items = [...section.querySelectorAll(".source-card, .resource-item, .compact-resource, .everything-entry, .mini-card, .lead-list li, .table-wrap tbody tr")];
    if (!input || !items.length) return;
    function render() {
      const terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      let shown = 0;
      items.forEach(item => {
        const match = !terms.length || terms.every(term => item.textContent.toLowerCase().includes(term));
        item.hidden = !match;
        if (match) shown += 1;
      });
      if (status) status.textContent = terms.length ? `Showing ${shown} of ${items.length} items for "${input.value.trim()}".` : `Search ${items.length} items in this section.`;
    }
    input.addEventListener("input", render);
    render();
  });
}

initListSearch();
initSourceSearch();
initResourceSearch();
initDirectoryAssistant();
initCopyButtons();
initPrintButtons();
initCornerControls();
initLandingIntro();
initAmbientMusic();
