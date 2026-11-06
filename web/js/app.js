/**
 * Wuthering Waves Arabic - Main Application & SPA Router
 */

import { api } from './api.js';
import { countdownEngine } from './countdown.js';
import { tgAdapter } from './telegram.js';
import { i18n } from './i18n.js';

class App {
  constructor() {
    this.currentRoute = 'home';
    this.contentData = null;
    this.allEvents = [];
    this.init();
  }

  async init() {
    i18n.apply();
    this.bindEvents();
    this.setupTelegram();
    this.setupStatusBanner();
    await this.loadData();
    this.handleRoute();
    // Start background polling for live reconnection
    api.startPolling();
    api.onDataUpdate((freshData) => {
      this.contentData = freshData;
      this.allEvents = freshData?.events || [];
      this.render();
    });
  }

  bindEvents() {
    // Hash routing
    window.addEventListener('hashchange', () => this.handleRoute());

    // Mobile drawer toggle
    const toggleBtn = document.getElementById('mobileMenuToggle');
    const drawer = document.getElementById('mobileDrawer');
    if (toggleBtn && drawer) {
      toggleBtn.addEventListener('click', () => {
        drawer.classList.toggle('open');
      });
      drawer.querySelectorAll('.mobile-nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          drawer.classList.remove('open');
          tgAdapter.haptic('light');
        });
      });
    }

    // Language switcher toggle (AR / EN)
    const langBtn = document.getElementById('langSwitcher');
    if (langBtn) {
      langBtn.addEventListener('click', () => {
        tgAdapter.haptic('light');
        i18n.toggle();
        this.render();
      });
    }

    // Navigation buttons haptic
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => tgAdapter.haptic('light'));
    });
  }

  setupTelegram() {
    if (tgAdapter.isInsideTelegram) {
      const badge = document.getElementById('tgBadge');
      if (badge) badge.classList.add('visible');

      tgAdapter.setupBackButton(() => {
        window.location.hash = '#home';
      });
    }
  }

  setupStatusBanner() {
    const banner = document.getElementById('offlineBanner');
    const textEl = document.getElementById('offlineText');
    if (!banner || !textEl) return;

    api.onStatusChange((isOffline, ageStr) => {
      if (isOffline) {
        banner.classList.add('active');
        textEl.textContent = `⚠️ تعذر الاتصال بهاتف السيرفر (Termux) - يتم عرض آخر بيانات متوفرة (${ageStr}) - جاري محاولة إعادة الاتصال تلقائياً...`;
      } else {
        banner.classList.remove('active');
      }
    });
  }

  async loadData() {
    try {
      this.contentData = await api.getAllContent();
      this.allEvents = this.contentData?.events || [];
      this.render();
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  }

  handleRoute() {
    const hash = window.location.hash.replace('#', '') || 'home';
    this.currentRoute = hash;

    document.querySelectorAll('.page-view').forEach(view => {
      view.classList.remove('active');
    });

    const activeView = document.getElementById(`view-${hash}`);
    if (activeView) {
      activeView.classList.add('active');
    } else {
      const homeView = document.getElementById('view-home');
      if (homeView) homeView.classList.add('active');
      this.currentRoute = 'home';
    }

    document.querySelectorAll('.nav-btn, .mobile-nav-btn').forEach(btn => {
      const route = btn.getAttribute('data-route');
      if (route === this.currentRoute) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    if (this.currentRoute === 'home') {
      tgAdapter.hideBackButton();
    } else {
      tgAdapter.showBackButton();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  render() {
    if (!this.contentData) return;

    this.renderHome();
    this.renderBanners();
    this.renderEvents();
    this.renderStygian();
    this.renderTower();
  }

  renderHome() {
    const { banner, events } = this.contentData;

    if (banner) {
      const titleEl = document.getElementById('homeBannerTitle');
      const nameEl  = document.getElementById('homeBannerName');

      if (titleEl) titleEl.textContent = banner.title || 'بنر الشخصيات الحالي';
      if (nameEl)  nameEl.textContent  = banner.name  || '';

      // Update hero background image dynamically from API
      const heroBgEl = document.querySelector('.version-hero-bg');
      if (heroBgEl) {
        heroBgEl.style.backgroundImage = `url('${api.getImageUrl(`/image/banner?t=${Date.now()}`)}')`;
      }

      this.setupServerCountdownCards('home', banner.servers);
    }

    const eventsContainer = document.getElementById('homeEventsGrid');
    if (eventsContainer && events) {
      eventsContainer.innerHTML = '';
      const previewEvents = events.slice(0, 4);
      if (previewEvents.length === 0) {
        eventsContainer.innerHTML =
          '<div style="color:var(--text-muted);grid-column:1/-1;text-align:center;padding:20px;">لا توجد أحداث نشطة حالياً.</div>';
      } else {
        previewEvents.forEach((ev, idx) => {
          eventsContainer.appendChild(this.createEventCard(ev, `home-ev-${idx}`));
        });
      }
    }
  }

  renderBanners() {
    const { banner } = this.contentData;
    if (!banner) return;

    const pageTitleEl = document.getElementById('bannersPageTitle');
    const charsEl = document.getElementById('bannersPageChars');
    const descEl = document.getElementById('bannersPageDesc');
    const imgEl = document.getElementById('bannersPageImg');

    if (pageTitleEl) pageTitleEl.textContent = banner.title;
    if (charsEl) charsEl.textContent = banner.name || '';
    if (descEl) {
      if (banner.description) {
        descEl.textContent = banner.description;
        descEl.style.display = 'block';
      } else {
        descEl.style.display = 'none';
      }
    }
    if (imgEl) imgEl.src = api.getImageUrl(`/image/banner?t=${Date.now()}`);

    // Populate overlay text on the artwork
    const overlayTitle = document.getElementById('bannerOverlayTitle');
    const overlayChars = document.getElementById('bannerOverlayChars');
    if (overlayTitle) overlayTitle.textContent = banner.title || '';
    if (overlayChars) overlayChars.textContent = banner.name || '';

    this.setupServerCountdownCards('banners', banner.servers);
  }

  renderEvents() {
    const events = this.allEvents;
    const container = document.getElementById('eventsListGrid');
    if (!container) return;

    container.innerHTML = '';
    if (!events || events.length === 0) {
      container.innerHTML = '<div style="color:var(--text-muted);grid-column:1/-1;text-align:center;padding:40px;">لا توجد أحداث مضافة حالياً في قاعدة البيانات.</div>';
      return;
    }

    events.forEach((ev, idx) => {
      container.appendChild(this.createEventCard(ev, `page-ev-${idx}`));
    });
  }

  renderStygian() {
    const { stygian } = this.contentData;
    if (!stygian) return;

    const titleEl = document.getElementById('stygianTitle');
    const descEl = document.getElementById('stygianDesc');
    const imgEl = document.getElementById('stygianImg');

    if (titleEl) titleEl.textContent = stygian.title || 'السفينة — Stygian Sea';
    if (descEl) {
      if (stygian.description) {
        descEl.textContent = stygian.description;
        descEl.style.display = 'block';
      } else {
        descEl.style.display = 'none';
      }
    }
    if (imgEl) imgEl.src = api.getImageUrl(`/image/stygian?t=${Date.now()}`);

    this.setupServerCountdownCards('stygian', stygian.servers);
  }

  renderTower() {
    const { spiral_abyss } = this.contentData;
    if (!spiral_abyss) return;

    const titleEl = document.getElementById('towerTitle');
    const descEl = document.getElementById('towerDesc');
    const imgEl = document.getElementById('towerImg');

    if (titleEl) titleEl.textContent = spiral_abyss.title || 'التاور — Tower of Adversity';
    if (descEl) {
      if (spiral_abyss.description) {
        descEl.textContent = spiral_abyss.description;
        descEl.style.display = 'block';
      } else {
        descEl.style.display = 'none';
      }
    }
    if (imgEl) imgEl.src = api.getImageUrl(`/image/spiral_abyss?t=${Date.now()}`);

    this.setupServerCountdownCards('tower', spiral_abyss.servers);
  }

  setupServerCountdownCards(prefix, servers) {
    if (!servers) return;

    const serverKeys = ['asia', 'europe', 'america'];
    serverKeys.forEach(srvKey => {
      const srvData = servers[srvKey];
      if (!srvData || !srvData.iso_utc) return;

      const timerId = `${prefix}-${srvKey}`;

      countdownEngine.register(timerId, srvData.iso_utc, ({ days, hours, minutes, seconds, arabicStr, isExpired }) => {
        const daysEl = document.getElementById(`${timerId}-days`);
        const hoursEl = document.getElementById(`${timerId}-hours`);
        const minsEl = document.getElementById(`${timerId}-mins`);
        const secsEl = document.getElementById(`${timerId}-secs`);
        const textEl = document.getElementById(`${timerId}-text`);
        const pillEl = document.getElementById(`${timerId}-pill`);

        if (daysEl) daysEl.textContent = String(days).padStart(2, '0');
        if (hoursEl) hoursEl.textContent = String(hours).padStart(2, '0');
        if (minsEl) minsEl.textContent = String(minutes).padStart(2, '0');
        if (secsEl) secsEl.textContent = String(seconds).padStart(2, '0');
        if (textEl) textEl.textContent = arabicStr;

        if (pillEl) {
          if (isExpired) {
            pillEl.textContent = 'انتهى';
            pillEl.classList.add('expired');
          } else {
            pillEl.textContent = 'نشط';
            pillEl.classList.remove('expired');
          }
        }
      });
    });
  }

  createEventCard(eventItem, timerId) {
    const card = document.createElement('div');
    card.className = 'event-card';

    const header = document.createElement('div');
    header.className = 'event-header';

    const title = document.createElement('h3');
    title.className = 'event-title';
    title.textContent = eventItem.name || eventItem.title;

    const statusPill = document.createElement('span');
    statusPill.className = 'server-status-pill';
    statusPill.textContent = 'نشط';

    header.appendChild(title);
    header.appendChild(statusPill);
    card.appendChild(header);

    const countdownBadge = document.createElement('div');
    countdownBadge.className = 'event-countdown-badge';
    countdownBadge.id = `${timerId}-badge`;
    countdownBadge.textContent = 'جاري الحساب...';
    card.appendChild(countdownBadge);

    const isoUtc = eventItem.countdown?.iso_utc;
    if (isoUtc) {
      countdownEngine.register(timerId, isoUtc, ({ arabicStr, isExpired }) => {
        countdownBadge.textContent = isExpired ? 'انتهى الحدث' : `⏳ متبقي: ${arabicStr}`;
        if (isExpired) {
          statusPill.textContent = 'منتهي';
          statusPill.classList.add('expired');
          countdownBadge.style.borderColor = 'rgba(244, 63, 94, 0.4)';
          countdownBadge.style.color = 'var(--accent-red)';
        }
      });
    }

    return card;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();
});
