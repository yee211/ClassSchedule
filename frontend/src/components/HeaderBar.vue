<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

defineProps({
  user: { type: Object, default: null },
  schedule: { type: Object, default: null },
  bgMode: { type: String, default: 'transparent' },
  appVersion: { type: String, default: '2.1.3' },
  isNative: { type: Boolean, default: false },
});

const emit = defineEmits([
  'delete-schedule',
  'add-course',
  'upload',
  'upload-adjustment',
  'logout',
  'toggle-night-mode',
  'check-update',
]);

const userMenuRef = ref(null);

function onUpload(event) {
  emit('upload', event);
}

function onAdjustmentUpload(event) {
  emit('upload-adjustment', event);
}

function closeUserMenu(event) {
  if (userMenuRef.value && userMenuRef.value.open && !userMenuRef.value.contains(event.target)) {
    userMenuRef.value.removeAttribute('open');
  }
}

onMounted(() => {
  document.addEventListener('click', closeUserMenu);
});

onUnmounted(() => {
  document.removeEventListener('click', closeUserMenu);
});
</script>

<template>
  <header class="top glass">
    <div class="brand"><span class="brand-dot"></span><strong>序时</strong></div>
    <div class="top-actions">
      <button
        class="header-action uiverse-button"
        type="button"
        title="添加课程"
        @click="emit('add-course')"
      >
        <span aria-hidden="true">＋</span>
        <span class="action-text">添加课程</span>
        <span class="action-text-short">加课</span>
      </button>
      <label class="header-action upload uiverse-button" title="上传课表">
        <input type="file" accept=".xlsx,.xlsm,.xls" @change="onUpload">
        <span aria-hidden="true">↑</span>
        <span class="action-text">上传课表</span>
        <span class="action-text-short">导入</span>
      </label>
      <label class="header-action upload uiverse-button" title="AI 识别调课通知">
        <input type="file" accept="image/jpeg,image/png,image/webp" @change="onAdjustmentUpload">
        <span aria-hidden="true">⇄</span>
        <span class="action-text">调课通知</span>
        <span class="action-text-short">调课</span>
      </label>
      <button
        v-if="isNative"
        class="header-action uiverse-button"
        type="button"
        title="检查更新"
        @click="emit('check-update')"
      >
        <span aria-hidden="true">🔄</span>
        <span class="action-text">检查更新</span>
        <span class="action-text-short">更新</span>
      </button>
      <a
        v-else
        class="header-action uiverse-button download-apk-btn"
        href="/downloads/%E5%BA%8F%E6%97%B6.apk"
        download="序时.apk"
        title="下载安装 Android App (APK)"
      >
        <span aria-hidden="true">📱</span>
        <span class="action-text">下载 App</span>
        <span class="action-text-short">App</span>
      </a>
      <details v-if="user" ref="userMenuRef" class="user-menu">
        <summary class="user-badge uiverse-button" :title="user.email">
          <span class="user-avatar" aria-hidden="true">{{ user.username?.slice(0, 1)?.toUpperCase() }}</span>
          <span class="user-name">{{ user.username }}</span>
          <span class="user-arrow" aria-hidden="true">⌄</span>
        </summary>
        <div class="user-menu-panel glass">
          <div class="user-menu-meta"><b>{{ user.username }}</b><small>{{ user.email }}</small></div>
          <button v-if="isNative" type="button" @click="emit('check-update'); userMenuRef?.removeAttribute('open')">
            检查更新 (v{{ appVersion }})
          </button>
          <a
            v-else
            href="/downloads/%E5%BA%8F%E6%97%B6.apk"
            download="序时.apk"
            class="user-menu-link"
            @click="userMenuRef?.removeAttribute('open')"
          >
            📱 下载安卓 App (APK)
          </a>
          <button type="button" :disabled="!schedule" @click="emit('delete-schedule'); userMenuRef?.removeAttribute('open')">删除当前课表</button>
          <button type="button" @click="emit('logout')">退出登录</button>
        </div>
      </details>
      <button
        type="button"
        class="night-mode-button uiverse-button"
        :class="{ active: bgMode === 'night' }"
        :aria-label="bgMode === 'night' ? '切换到日间模式' : '切换到黑夜模式'"
        :title="bgMode === 'night' ? '日间模式' : '黑夜模式'"
        :aria-pressed="bgMode === 'night'"
        @click="emit('toggle-night-mode')"
      >
        <span aria-hidden="true">{{ bgMode === 'night' ? '☀️' : '🌙' }}</span>
      </button>
    </div>
  </header>
</template>
