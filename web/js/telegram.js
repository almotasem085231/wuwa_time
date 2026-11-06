/**
 * Wuthering Waves Arabic - Telegram Mini App SDK Adapter
 * Handles WebApp expansion, BackButton navigation, theme syncing,
 * safe area handling, and haptics.
 */

class TelegramAdapter {
  constructor() {
    this.tg = window.Telegram?.WebApp;
    this.isInsideTelegram = !!(this.tg && this.tg.initData);
    this.init();
  }

  init() {
    if (!this.tg) {
      console.log('Running in standard browser mode (Outside Telegram)');
      return;
    }

    try {
      // Announce ready & expand viewport
      this.tg.ready();
      this.tg.expand();

      // Configure Header & Background matching Wuthering Waves Dark Theme
      if (this.tg.setHeaderColor) {
        this.tg.setHeaderColor('#0c111a');
      }
      if (this.tg.setBackgroundColor) {
        this.tg.setBackgroundColor('#070a0f');
      }

      // Safe viewport height variable
      if (this.tg.viewportHeight) {
        document.documentElement.style.setProperty('--tg-viewport-height', `${this.tg.viewportHeight}px`);
      }

      this.tg.onEvent('viewportChanged', () => {
        if (this.tg.viewportHeight) {
          document.documentElement.style.setProperty('--tg-viewport-height', `${this.tg.viewportHeight}px`);
        }
      });

      console.log('Telegram Mini App initialized successfully:', {
        user: this.getUser(),
        platform: this.tg.platform,
        version: this.tg.version
      });
    } catch (e) {
      console.warn('Telegram WebApp setup warning:', e);
    }
  }

  getUser() {
    return this.tg?.initDataUnsafe?.user || null;
  }

  getInitData() {
    return this.tg?.initData || '';
  }

  haptic(style = 'light') {
    try {
      if (this.tg?.HapticFeedback) {
        if (style === 'notification') {
          this.tg.HapticFeedback.notificationOccurred('success');
        } else {
          this.tg.HapticFeedback.impactOccurred(style);
        }
      }
    } catch (e) {
      // Silently ignore if unsupported
    }
  }

  setupBackButton(onBackClick) {
    if (!this.tg?.BackButton) return;

    this.tg.BackButton.onClick(() => {
      this.haptic('light');
      if (onBackClick) onBackClick();
    });
  }

  showBackButton() {
    try {
      this.tg?.BackButton?.show();
    } catch (e) {}
  }

  hideBackButton() {
    try {
      this.tg?.BackButton?.hide();
    } catch (e) {}
  }

  close() {
    try {
      this.tg?.close();
    } catch (e) {}
  }
}

export const tgAdapter = new TelegramAdapter();

