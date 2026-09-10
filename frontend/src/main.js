import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import './styles/accessibility.css'

createApp(App).mount('#app')

// 注册 Service Worker，赋能 PWA 离线缓存、桌面图标与毫秒级秒开
if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('ServiceWorker registration failed:', err);
    });
  });
}
