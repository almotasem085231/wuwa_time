/**
 * Wuthering Waves Arabic - API Client
 * Features:
 * - LocalStorage Caching
 * - Offline / Termux phone disconnection resilience
 * - Auto-reconnection background polling with onDataUpdate callbacks
 * - Configurable Base URL (supports Netlify proxy or direct API)
 */

// Auto-detect and store ?api=... query parameter for easy one-click backend connection
(function initApiConfig() {
  try {
    if (typeof window !== 'undefined' && window.location.search) {
      const params = new URLSearchParams(window.location.search);
      const apiParam = params.get('api');
      if (apiParam) {
        let cleanUrl = apiParam.trim().replace(/\/+$/, '');
        if (!cleanUrl.endsWith('/api')) {
          cleanUrl += '/api';
        }
        localStorage.setItem('wuwa_api_url', cleanUrl);
        console.log('[API] Connected to backend URL from parameter:', cleanUrl);
      }
    }
  } catch (e) {
    console.warn('[API] Query param init error:', e);
  }
})();

const API_CONFIG = {
  // Priority: 1. window.API_BASE_URL (if injected) 2. localStorage 3. Relative '/api'
  baseUrl: window.API_BASE_URL || localStorage.getItem('wuwa_api_url') || '/api',
  cacheKey: 'wuwa_cached_content',
  cacheExpiryKey: 'wuwa_cache_timestamp',
  pollIntervalMs: 15000, // Background re-poll interval (15s)
};

class ApiService {
  constructor() {
    this.isOffline = false;
    this.lastSuccessfulData = this.loadFromCache();
    this.statusListeners = [];
    this.dataListeners = [];
    this._pollTimer = null;
  }

  /** Subscribe to online/offline status changes */
  onStatusChange(callback) {
    this.statusListeners.push(callback);
  }

  /** Subscribe to live data updates — called when background poll gets fresh data after reconnect */
  onDataUpdate(callback) {
    this.dataListeners.push(callback);
  }

  notifyStatus(isOffline, dataAgeStr = '') {
    this.isOffline = isOffline;
    this.statusListeners.forEach(cb => cb(isOffline, dataAgeStr));
  }

  notifyDataUpdate(data) {
    this.dataListeners.forEach(cb => cb(data));
  }

  saveToCache(data) {
    try {
      localStorage.setItem(API_CONFIG.cacheKey, JSON.stringify(data));
      localStorage.setItem(API_CONFIG.cacheExpiryKey, new Date().toISOString());
      this.lastSuccessfulData = data;
    } catch (e) {
      console.warn('LocalStorage save failed:', e);
    }
  }

  loadFromCache() {
    try {
      const raw = localStorage.getItem(API_CONFIG.cacheKey);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      console.warn('LocalStorage load failed:', e);
      return null;
    }
  }

  getCacheAgeString() {
    try {
      const timestamp = localStorage.getItem(API_CONFIG.cacheExpiryKey);
      if (!timestamp) return '';
      const diffMinutes = Math.floor((Date.now() - new Date(timestamp).getTime()) / 60000);
      if (diffMinutes < 1) return 'منذ لحظات';
      if (diffMinutes < 60) return `منذ ${diffMinutes} دقيقة`;
      const diffHours = Math.floor(diffMinutes / 60);
      return `منذ ${diffHours} ساعة`;
    } catch {
      return '';
    }
  }

  async fetchWithTimeout(endpoint, options = {}, timeoutMs = 8000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          ...(options.headers || {})
        }
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      throw err;
    }
  }

  /**
   * Fetches full content (banner, stygian, spiral_abyss, events).
   * Falls back to cached data if network fails (Termux phone offline).
   */
  async getAllContent() {
    try {
      const data = await this.fetchWithTimeout('/content');
      this.saveToCache(data);
      this.notifyStatus(false);
      return data;
    } catch (err) {
      console.warn('Failed to fetch from live API, falling back to cache:', err.message);
      const cached = this.loadFromCache();
      if (cached) {
        this.notifyStatus(true, this.getCacheAgeString());
        return cached;
      }
      throw err;
    }
  }

  /**
   * Start background polling — re-fetches /content every pollIntervalMs.
   * Calls onDataUpdate listeners when:
   * 1. Reconnected after offline mode.
   * 2. Content has changed (admin updated banner/events via bot).
   */
  startPolling() {
    if (this._pollTimer) return; // already polling
    this._pollTimer = setInterval(async () => {
      try {
        const data = await this.fetchWithTimeout('/content');
        const wasOffline = this.isOffline;

        // Detect content change via comparing timestamp
        const prevTs  = this.lastSuccessfulData?.timestamp_utc || '';
        const freshTs = data?.timestamp_utc || '';
        const contentChanged = freshTs !== prevTs;

        this.saveToCache(data);
        this.notifyStatus(false);

        // Re-render if reconnected OR if content was updated by admin
        if (wasOffline || contentChanged) {
          if (contentChanged && !wasOffline) {
            console.info('[API] Content updated by admin. Refreshing UI...');
          } else if (wasOffline) {
            console.info('[API] Reconnected. Refreshing UI with fresh data...');
          }
          this.notifyDataUpdate(data);
        }
      } catch (err) {
        if (!this.isOffline) {
          this.notifyStatus(true, this.getCacheAgeString());
        }
      }
    }, API_CONFIG.pollIntervalMs);
  }

  stopPolling() {
    if (this._pollTimer) {
      clearInterval(this._pollTimer);
      this._pollTimer = null;
    }
  }

  async getHealth() {
    try {
      return await this.fetchWithTimeout('/health', {}, 4000);
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  }
}

export const api = new ApiService();
