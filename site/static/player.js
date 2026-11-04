// Songs are known by their ID numbers (the music database's record IDs; see app.py), so
// renaming one never confuses a player. Song links expire after a few minutes and only work
// in the browser they were made for (see song_link in app.py). The site's players fetch a
// fresh link before a song starts, and again if one runs out mid-song (say, after a long
// pause), so listeners never notice. Audio players also get no right-click menu.
window.wiseWild = (() => {
  // A fresh link for a song: { id, title, url }. The title is the song's current one, even if
  // it was renamed in the song manager after this page was opened.
  async function songLink(track) {
    const response = await fetch(`/api/song-link?track=${encodeURIComponent(track)}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`no link for song ${track}`);
    return response.json();
  }

  // Point a player at a song (by ID) through a fresh link, under the song's current title.
  async function load(audio, track) {
    const link = await songLink(track);
    audio.dataset.track = link.id;
    audio.dataset.title = link.title;
    audio.src = link.url;
  }

  // After an error, carry on from the same spot with a fresh link. Returns false when that
  // doesn't help (for example, the song has been archived).
  async function recover(audio) {
    const track = audio.dataset.track;
    if (!track || audio.dataset.retried === track) return false;
    audio.dataset.retried = track;
    const at = audio.currentTime || 0;
    try {
      await load(audio, track);
      if (at) audio.currentTime = at;
      await audio.play();
      return true;
    } catch {
      return false;
    }
  }

  // Players on the page itself (the music library and song manager). Media events don't
  // bubble, so listen in the capture phase.
  document.addEventListener("error", (event) => {
    if (event.target instanceof HTMLAudioElement) recover(event.target);
  }, true);
  document.addEventListener("playing", (event) => {
    if (event.target instanceof HTMLAudioElement) delete event.target.dataset.retried;
  }, true);
  document.addEventListener("contextmenu", (event) => {
    if (event.target instanceof HTMLAudioElement) event.preventDefault();
  });

  // Play log: a song counts as played once it has been heard for 30 seconds (or to its end,
  // if shorter). Pausing and resuming don't count again; playing it again later does.
  const COUNT_AFTER_SECONDS = 30;

  function relightMeters(bars) {
    for (const meter of document.querySelectorAll(".pop-meter[data-track]")) {
      const lit = bars[meter.dataset.track] ?? 0;
      [...meter.children].forEach((bar, i) => bar.classList.toggle("on", i < lit));
      meter.setAttribute("aria-label", `Popularity ${lit} of 7`);
      meter.title = meter.title.replace(/Popularity \d of 7/, `Popularity ${lit} of 7`);
    }
  }

  async function reportPlay(track, src) {
    try {
      const response = await fetch("/api/played", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          track: Number(track), t: new URL(src, location.href).searchParams.get("t"), page: location.pathname,
        }),
      });
      if (response.ok) relightMeters((await response.json()).bars);
    } catch {
      // Logging a play is a nice-to-have; never let it interrupt the music.
    }
  }

  function trackPlays(audio) {
    let track = null;
    let heard = 0;
    let last = 0;
    let counted = false;
    const restart = () => { heard = 0; counted = false; last = audio.currentTime || 0; };
    audio.addEventListener("loadstart", () => {
      // A new song (a refreshed link for the same song carries on where it was).
      if (audio.dataset.track !== track) { track = audio.dataset.track; restart(); }
    });
    for (const type of ["play", "seeked"]) audio.addEventListener(type, () => { last = audio.currentTime; });
    audio.addEventListener("timeupdate", () => {
      const step = audio.currentTime - last;
      last = audio.currentTime;
      if (audio.paused || audio.seeking || step <= 0 || step > 2 * audio.playbackRate) return;
      heard += step;
      const needed = Math.min(COUNT_AFTER_SECONDS, (audio.duration || Infinity) - 1);
      if (!counted && track && heard >= needed) {
        counted = true;
        reportPlay(track, audio.currentSrc);
      }
    });
    audio.addEventListener("ended", restart);
  }

  // Now playing: the title of whatever is playing shows at the top centre of the header
  // (players set audio.dataset.title). While it plays, one letter at a time, picked at
  // random, slowly blinks off and back on.
  const BLINK_MS = 1600;  // the length of the letter-blink animation in style.css
  const header = document.querySelector(".site-header");
  const banner = document.querySelector(".now-playing");
  let shownFor = null;
  let blinkTimer = 0;

  function blink(last = -1) {
    const letters = banner.querySelectorAll(".now-playing-letters span");
    if (!letters.length) return;
    let pick = Math.floor(Math.random() * letters.length);
    if (pick === last) pick = (pick + 1) % letters.length;
    letters[pick].classList.add("blink");
    blinkTimer = setTimeout(() => {
      letters[pick].classList.remove("blink");
      blinkTimer = setTimeout(() => blink(pick), 200 + Math.random() * 600);
    }, BLINK_MS);
  }

  function showTitle(audio) {
    const title = audio.dataset.title || "";
    if (audio === shownFor && banner.title === title && banner.classList.contains("is-on")) return;
    shownFor = audio;
    clearTimeout(blinkTimer);
    banner.querySelector(".now-playing-letters").replaceChildren(...[...title].map((character) => {
      if (!character.trim()) return character;
      const letter = document.createElement("span");
      letter.textContent = character;
      return letter;
    }));
    banner.querySelector(".now-playing-text").textContent = `Now playing: ${title}`;
    banner.title = title;
    banner.classList.add("is-on");
    header.classList.add("has-now-playing");
    blink();
  }

  function hideTitle() {
    clearTimeout(blinkTimer);
    banner.querySelector(".blink")?.classList.remove("blink");
    banner.querySelector(".now-playing-text").textContent = "";
    banner.classList.remove("is-on");
    header.classList.remove("has-now-playing");
  }

  function showTitles(audio) {
    if (!banner) return;
    audio.addEventListener("playing", () => showTitle(audio));
    for (const type of ["pause", "ended", "emptied"]) {
      audio.addEventListener(type, () => { if (audio === shownFor) hideTitle(); });
    }
  }

  // Every player on the site: count its plays and show what it's playing.
  function watch(audio) {
    trackPlays(audio);
    showTitles(audio);
  }

  for (const audio of document.querySelectorAll("audio")) watch(audio);

  return { load, recover, watch };
})();

// Buttons marked data-loop-player (Explore creations and, for now, the site's other
// buttons) play every song in the music folder one after another, starting over after
// the last one, until any of them is pressed again. A button with data-stop-label
// shows that label while music plays.
// The footer dice (data-shuffle-play) are random play: every song once, in a new random
// order on every roll, then stop. Rolling them again while they play stops them.
(() => {
  const buttons = document.querySelectorAll("[data-loop-player], [data-shuffle-play]");
  if (!buttons.length) return;

  for (const button of buttons) {
    button.dataset.idleLabel = button.textContent.trim();
    button.dataset.idleTitle = button.title;
    button.setAttribute("aria-pressed", "false");
  }

  const audio = new Audio();
  wiseWild.watch(audio);
  let tracks = [];
  let index = 0;
  let failures = 0;
  let playing = false;
  let shuffled = false;  // random play (the dice) rather than the loop

  function render() {
    const track = tracks[index];
    for (const button of buttons) {
      if (button.dataset.stopLabel) {
        button.textContent = playing ? button.dataset.stopLabel : button.dataset.idleLabel;
      }
      // Any music stops when a loop button is pressed; the dice light up only for random play.
      const active = playing && (shuffled || !("shufflePlay" in button.dataset));
      button.setAttribute("aria-pressed", String(active));
      button.title = active && track ? `Now playing: ${audio.dataset.title || track.title}` : button.dataset.idleTitle;
    }
  }

  // Fisher-Yates: every order equally likely.
  function shuffle(list) {
    for (let i = list.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]];
    }
    return list;
  }

  async function loadTracks() {
    try {
      const response = await fetch("/api/playlist", { cache: "no-store" });
      tracks = response.ok ? await response.json() : [];
    } catch {
      tracks = [];
    }
  }

  function onPlayError(error) {
    // Only a browser autoplay block stops the loop; bad files are handled by the "error" event.
    if (error.name === "NotAllowedError") stop();
  }

  async function playCurrent() {
    if (index >= tracks.length) {
      // Random play ends after the last song, like Play All.
      if (shuffled) {
        audio.removeAttribute("src");
        return stop();
      }
      // The loop reads the folder again, so renamed or new songs are picked up, and starts over.
      index = 0;
      await loadTracks();
    }
    if (!playing) return;
    if (!tracks.length) return stop();
    const track = tracks[index];
    try {
      await wiseWild.load(audio, track.id);
    } catch {
      audio.dataset.track = track.id;
      audio.dataset.title = track.title;
      audio.src = track.url;  // the "error" handler deals with a song that has gone
    }
    if (!playing) return;  // stopped while the link was on its way
    render();
    audio.play().catch(onPlayError);
  }

  function next() {
    index += 1;
    playCurrent();
  }

  // The loop carries on where it was stopped; random play always starts a fresh shuffle.
  async function start(randomly) {
    playing = true;
    for (const other of document.querySelectorAll("audio")) other.pause();
    if (!randomly && !shuffled && audio.getAttribute("src")) {
      render();
      audio.play().catch(onPlayError);
      return;
    }
    shuffled = randomly;
    index = 0;
    render();
    await loadTracks();
    if (randomly) shuffle(tracks);
    playCurrent();
  }

  function stop() {
    playing = false;
    audio.pause();
    render();
  }

  audio.addEventListener("playing", () => {
    failures = 0;
    delete audio.dataset.retried;
  });
  audio.addEventListener("ended", next);
  audio.addEventListener("error", async () => {
    // An expired link: carry on with a fresh one.
    if (playing && await wiseWild.recover(audio)) return;
    // Otherwise skip a song that won't load (for example, renamed since the list was read),
    // but give up if nothing in the list plays.
    failures += 1;
    if (failures > tracks.length) {
      failures = 0;
      audio.removeAttribute("src");
      stop();
      return;
    }
    if (playing) next();
  });

  for (const button of buttons) {
    const randomly = "shufflePlay" in button.dataset;
    button.addEventListener("click", () => {
      if (playing && (shuffled || !randomly)) return stop();
      if (randomly) roll(button);
      start(randomly);
    });
  }

  // The dice spin as they're rolled.
  function roll(dice) {
    dice.classList.remove("is-rolling");
    void dice.offsetWidth;  // restart the animation if it's already running
    dice.classList.add("is-rolling");
    dice.addEventListener("animationend", () => dice.classList.remove("is-rolling"), { once: true });
  }

  // Stop the loop when a song is started from a song list's own play buttons.
  document.addEventListener("play", (event) => {
    if (playing && event.target !== audio) stop();
  }, true);

  // For other parts of the site: start the loop (unless it's playing already; it pauses any
  // other player on the page), and ask whether the loop, or any music, is playing. The
  // Adventure link and a visitor's first quest start the music this way (adventure.js).
  wiseWild.playAll = () => {
    if (!playing) start(false);
  };
  wiseWild.loopPlaying = () => playing;
  wiseWild.musicPlaying = () => playing || [...document.querySelectorAll("audio")].some((other) => !other.paused);
})();
