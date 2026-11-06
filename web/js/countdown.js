/**
 * Wuthering Waves Arabic - High-Precision Countdown Engine
 * Replicates the exact algorithm from wuwa.py:
 * diff = end_time - now
 * days = total_seconds // 86400
 * hours = (total_seconds % 86400) // 3600
 * minutes = (total_seconds % 3600) // 60
 * seconds = total_seconds % 60
 * If total_seconds <= 0: "انتهى."
 */

export class CountdownEngine {
  constructor() {
    this.targets = new Map(); // id -> { isoUtc, onTick, onExpire }
    this.timerId = null;
    this.start();
  }

  start() {
    if (this.timerId) return;
    this.tick();
    this.timerId = setInterval(() => this.tick(), 1000);
  }

  stop() {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  /**
   * Register a timer target.
   * @param {string} id Unique identifier
   * @param {string} isoUtc ISO 8601 UTC date string (e.g. 2026-11-21T04:56:05Z)
   * @param {function} onTick Callback receiving { days, hours, minutes, seconds, arabicStr, isExpired }
   */
  register(id, isoUtc, onTick) {
    if (!isoUtc) return;
    this.targets.set(id, { isoUtc, onTick });
    // Immediate calculation for this target
    this.calcTarget(id, isoUtc, onTick);
  }

  unregister(id) {
    this.targets.delete(id);
  }

  clear() {
    this.targets.clear();
  }

  calcTarget(id, isoUtc, onTick) {
    const endMs = new Date(isoUtc).getTime();
    const nowMs = Date.now();
    const totalSeconds = Math.floor((endMs - nowMs) / 1000);

    if (isNaN(totalSeconds) || totalSeconds <= 0) {
      onTick({
        days: 0,
        hours: 0,
        minutes: 0,
        seconds: 0,
        totalSeconds: 0,
        arabicStr: 'انتهى.',
        isExpired: true
      });
      return;
    }

    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const arabicStr = `${days} يوم و ${hours} ساعة و ${minutes} دقيقة و ${seconds} ثانية`;

    onTick({
      days,
      hours,
      minutes,
      seconds,
      totalSeconds,
      arabicStr,
      isExpired: false
    });
  }

  tick() {
    for (const [id, { isoUtc, onTick }] of this.targets.entries()) {
      this.calcTarget(id, isoUtc, onTick);
    }
  }
}

export const countdownEngine = new CountdownEngine();

