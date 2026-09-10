import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import './styles/accessibility.css'

// 在 Vue 挂载前截获 Chrome 原生安装提示；首次进入页面时不自动弹出，
// 留到用户主动点击“添加到手机桌面”时再调用同一个提示。
window.__jiankeInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  window.__jiankeInstallPrompt = event;
  window.dispatchEvent(new CustomEvent('pwa:install-ready'));
});

window.addEventListener('appinstalled', () => {
  window.__jiankeInstallPrompt = null;
  window.dispatchEvent(new CustomEvent('pwa:installed'));
});

createApp(App).mount('#app')

// 注册 Service Worker，赋能 PWA 离线缓存、桌面图标与毫秒级秒开
if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('ServiceWorker registration failed:', err);
    });
  });
}
