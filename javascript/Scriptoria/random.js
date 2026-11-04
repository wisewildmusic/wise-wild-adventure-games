// A seeded source of random numbers. Math.random() can't be given a seed, and a saved quest has to replay
// exactly the same every time, so the game has its own: mulberry32, a small generator of 32-bit numbers
// written with JavaScript's bit operators, which work on 32-bit whole numbers whatever else a number may be.
export class Rng {
  #state;

  constructor(seed) {
    this.#state = Number(seed) >>> 0;
  }

  #next32() {
    this.#state = (this.#state + 0x6d2b79f5) >>> 0;
    let t = this.#state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (t ^ (t >>> 14)) >>> 0;
  }

  /** A whole number from 0 up to bound - 1, each equally likely. */
  next(bound) {
    const tooLow = 2 ** 32 % bound; // the numbers to throw away, so that none comes up more than the rest
    let number;
    do {
      number = this.#next32();
    } while (number < tooLow);
    return number % bound;
  }
}

/** A Fisher-Yates shuffle, of the array itself. */
export function shuffle(rng, items) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = rng.next(i + 1);
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}
