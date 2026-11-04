// Song list pages: one shared audio element; each row's button plays or pauses its song.
// "Play All" (song library only) plays the list from the top, one song after another,
// lighting up each row as it plays, and stops after the last song.
// Word tags (music library): picking a tag shows only the songs with that tag and plays them
// all, top to bottom; picking it again stops them and shows every song. Play All then plays
// whichever songs are showing. A link such as /music/?tag=Chill opens with that tag picked.
(() => {
  const audio = document.getElementById("song-audio");
  const buttons = [...document.querySelectorAll("[data-song]")];
  if (!audio || !buttons.length) return;

  const playAll = document.querySelector("[data-play-all]");
  const scroller = document.querySelector(".library-scroll");
  const tagPicks = [...document.querySelectorAll(".tag-pick")];  // the tag bar and the tags under titles
  const tagBar = [...document.querySelectorAll(".tag-filter .tag-pick")];
  const filterNote = document.querySelector(".tag-filter-note");
  let current = null;
  let playingAll = false;
  let activeTag = null;

  const showing = () => buttons.filter((button) => !button.closest("tr").hidden);

  function render() {
    for (const button of buttons) {
      const playing = button === current && !audio.paused;
      button.classList.toggle("is-playing", playing);
      button.setAttribute("aria-label", `${playing ? "Pause" : "Play"} ${button.dataset.title}`);
      button.closest("tr").classList.toggle("is-playing", playing);
    }
    if (playAll) {
      const active = playingAll && !audio.paused;
      playAll.textContent = active ? playAll.dataset.stopLabel : "Play All";
      playAll.setAttribute("aria-pressed", String(active));
    }
    for (const pick of tagBar) pick.setAttribute("aria-pressed", String(pick.dataset.tag === activeTag));
  }

  function play(button) {
    if (button !== current) {
      current = button;
      audio.dataset.track = button.dataset.track;  // the song's ID: lets player.js refresh an expired link
      audio.dataset.title = button.dataset.title;  // shown in the header while it plays
      audio.src = button.dataset.song;
    }
    audio.play().catch(() => {});
  }

  // Keep the playing row in view inside the panel, without scrolling the whole page.
  function showRow(button) {
    if (!scroller || scroller.scrollHeight <= scroller.clientHeight) return;
    const row = button.closest("tr");
    const head = scroller.querySelector("thead");
    const top = row.offsetTop - (head ? head.offsetHeight : 0);
    const bottom = row.offsetTop + row.offsetHeight;
    if (top < scroller.scrollTop) scroller.scrollTop = top;
    else if (bottom > scroller.scrollTop + scroller.clientHeight) scroller.scrollTop = bottom - scroller.clientHeight;
  }

  function startAll() {
    const first = showing()[0];
    if (!first) return;
    playingAll = true;
    current = null;
    play(first);
    showRow(first);
  }

  // Show only the songs with this tag (by its ID), or every song (null).
  function filter(tag) {
    activeTag = tag;
    for (const button of buttons) {
      const row = button.closest("tr");
      row.hidden = Boolean(tag) && !(row.dataset.tags || "").split(" ").includes(tag);
    }
    const name = tag && tagBar.find((pick) => pick.dataset.tag === tag)?.dataset.name;
    if (filterNote) {
      const count = showing().length;
      filterNote.textContent = name ? `${count} song${count === 1 ? "" : "s"} tagged “${name}” · pick it again to show all` : "";
    }
    const url = new URL(location.href);
    if (name) url.searchParams.set("tag", name);
    else url.searchParams.delete("tag");
    history.replaceState(null, "", url);
    if (scroller) scroller.scrollTop = 0;
    render();
  }

  for (const button of buttons) {
    button.addEventListener("click", () => {
      if (button === current && !audio.paused) {
        audio.pause();
        return;
      }
      if (button !== current) playingAll = false;  // picking a song ends "Play All"
      play(button);
    });
  }

  if (playAll) {
    playAll.addEventListener("click", () => {
      if (playingAll && !audio.paused) {
        playingAll = false;
        audio.pause();
        render();
        return;
      }
      startAll();
    });
  }

  for (const pick of tagPicks) {
    pick.addEventListener("click", () => {
      if (pick.dataset.tag === activeTag) {
        if (playingAll) audio.pause();
        playingAll = false;
        filter(null);
        return;
      }
      filter(pick.dataset.tag);
      startAll();
    });
  }

  audio.addEventListener("ended", () => {
    const list = showing();
    const next = list[list.indexOf(current) + 1];
    if (playingAll && next) {
      play(next);
      showRow(next);
    } else {
      playingAll = false;
      render();
    }
  });

  for (const type of ["play", "pause", "emptied"]) audio.addEventListener(type, render);

  // Opened with ?tag=Name: pick that tag (browsers won't start music before a click, so the
  // songs show, ready for Play All).
  const wanted = (new URLSearchParams(location.search).get("tag") || "").toLowerCase();
  const picked = wanted && tagBar.find((pick) => pick.dataset.name.toLowerCase() === wanted);
  if (picked) filter(picked.dataset.tag);
})();
