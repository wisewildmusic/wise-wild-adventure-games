// The adventure games (/adventure/). Loaded on every page, for the Adventure link.
// - The "Adventure" link starts the site's music (every song, on a loop) and opens the choice of
//   games in the page, without leaving it, so the music plays on. Choosing a game does the same.
//   (Ctrl-clicks and middle clicks open them the ordinary way, and so do the links if anything
//   goes wrong.)
// - Moves are sent without leaving the page: the quest panel is swapped for the new one, so
//   music playing from the site's players (Explore creations, Listen, the dice) carries on
//   through the whole quest. If that ever fails, the form is sent the ordinary way instead.
// - The name box only takes letters, numbers and spaces, starting with a letter: anything
//   else is dropped as it's typed or pasted. (The server checks again; this just helps.)
// - Keys 1, 2... pick a game or a choice, and a to d pick an answer.
// - A button can't be pressed twice while the next scene loads.
// - Leaving a quest, and facing the final boss (which can cost the whole score), ask first.
// - Beginning a quest starts the site's music (every song, on a loop), so visitors find out
//   they can listen while they play. Only once per visit, only if nothing is playing, and
//   not for visitors who have already used a music button on the page (they know).
(() => {
  let musicStarted = false;
  let musicTouched = false;
  document.addEventListener("click", (event) => {
    if (event.target.closest?.("[data-loop-player], [data-shuffle-play]")) musicTouched = true;
  }, true);

  function startQuestMusic() {
    if (musicStarted || musicTouched || !window.wiseWild?.playAll || wiseWild.musicPlaying()) return;
    musicStarted = true;
    wiseWild.playAll();  // called during the click on "Begin the quest", so browsers allow it
  }

  // The Adventure link: music first (during the click, so browsers allow it), then the choice
  // of games. The links to the games themselves start it only for visitors who haven't used a
  // music button: someone who stopped the music on the way here meant it.
  const ADVENTURE = "/adventure/";
  let movedInPage = false;

  async function openInPage(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`the server answered ${response.status}`);
    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    const main = page.querySelector("main");
    if (!main) throw new Error("no page content in the answer");
    document.querySelector("main").replaceWith(main);
    // The menu's lit-up link and the footer's visitor number belong to the new page; the
    // header (with the playing music) stays as it is.
    for (const link of document.querySelectorAll(".float-nav a.nav-link")) {
      const fresh = page.querySelector(`.float-nav a.nav-link[href="${link.getAttribute("href")}"]`);
      if (fresh) link.replaceWith(fresh);
    }
    const legal = page.querySelector(".site-footer .legal");
    if (legal) document.querySelector(".site-footer .legal")?.replaceWith(legal);
    document.title = page.title;
    history.pushState({ inPage: true }, "", url);
    window.scrollTo({ top: 0, behavior: "instant" });
    if (!movedInPage) {
      movedInPage = true;
      // Back (or forward) from here loads that page properly.
      window.addEventListener("popstate", () => location.reload());
    }
  }

  document.addEventListener("click", async (event) => {
    const link = event.target.closest?.("a[href]");
    if (!link || link.origin !== location.origin || !link.pathname.startsWith(ADVENTURE)) return;
    if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (link.pathname !== ADVENTURE) {
      startQuestMusic();
    } else if (window.wiseWild?.playAll && !wiseWild.loopPlaying()) {
      musicStarted = true;
      wiseWild.playAll();
    }
    if (location.pathname === link.pathname) return;  // already here: just the music
    try {
      await openInPage(link.href);
    } catch {
      location.href = link.href;
    }
  });

  // The box itself takes up to 64 characters, so a pasted name isn't cut short before its
  // special characters are dropped; it's trimmed to the real limit here.
  document.addEventListener("input", (event) => {
    const name = event.target;
    if (!name.matches?.(".name-input")) return;
    const tidy = name.value
      .replace(/[^A-Za-z0-9 ]+/g, "")  // letters, numbers and spaces only
      .replace(/^[^A-Za-z]+/, "")      // starting with a letter
      .replace(/ {2,}/g, " ")          // single spaces
      .slice(0, Number(name.dataset.max) || 20);
    if (tidy !== name.value) name.value = tidy;
  });

  // Send a quest form in the background and put the panel it leads to in place of this one.
  async function send(form, submitter) {
    const data = new FormData(form);
    if (submitter?.name) data.append(submitter.name, submitter.value);
    const response = await fetch(form.action, { method: "POST", body: data });
    if (!response.ok) throw new Error(`the server answered ${response.status}`);
    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    const next = page.querySelector(".quest");
    if (!next) throw new Error("no quest panel in the answer");
    document.querySelector(".quest").replaceWith(next);
    // Show the new scene from its picture, as a fresh page would, and move keyboard and
    // screen-reader focus to its title.
    const top = next.getBoundingClientRect().top + window.scrollY - 140;
    window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
    const title = next.querySelector(".scene-title");
    if (title) {
      title.tabIndex = -1;
      title.focus({ preventScroll: true });
    }
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!form.closest(".quest") || form.dataset.plain) return;  // plain: the ordinary way, as a fallback
    if (form.classList.contains("is-sending")) {
      event.preventDefault();
      return;
    }
    if (form.matches(".quest-leave") && !confirm("Leave this quest? It won't count on the Hall of Explorers.")) {
      event.preventDefault();
      return;
    }
    if (form.dataset.confirm && !confirm(form.dataset.confirm)) {  // the final boss
      event.preventDefault();
      return;
    }
    event.preventDefault();
    if (form.matches(".quest-start")) startQuestMusic();
    form.classList.add("is-sending");
    try {
      await send(form, event.submitter);
    } catch {
      form.classList.remove("is-sending");
      form.dataset.plain = "yes";
      form.requestSubmit(event.submitter?.isConnected ? event.submitter : undefined);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.metaKey || event.altKey || event.target.closest?.("input, textarea, select")) return;
    const key = CSS.escape(event.key.toLowerCase());
    const button = document.querySelector(`.quest button[data-key="${key}"], .game-choice[data-key="${key}"]`);
    if (button) {
      event.preventDefault();
      button.click();
    }
  });
})();
