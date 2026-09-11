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
  'open-adjustments',
  'logout',
  'toggle-night-mode',
  'check-update',
]);

const userMenuRef = ref(null);
const courseMenuRef = ref(null);

function onUpload(event) {
  courseMenuRef.value?.removeAttribute('open');
  emit('upload', event);
}

function closeMenus(event) {
  if (userMenuRef.value && userMenuRef.value.open && !userMenuRef.value.contains(event.target)) {
    userMenuRef.value.removeAttribute('open');
  }
  if (courseMenuRef.value && courseMenuRef.value.open && !courseMenuRef.value.contains(event.target)) {
    courseMenuRef.value.removeAttribute('open');
  }
}

onMounted(() => {
  document.addEventListener('click', closeMenus);
});

onUnmounted(() => {
  document.removeEventListener('click', closeMenus);
});
</script>

<template>
  <header class="top glass">
    <div class="brand"><span class="brand-dot"></span><strong>序时</strong></div>
    <div class="top-actions">
      <details ref="courseMenuRef" class="course-menu user-menu">
        <summary class="header-action uiverse-button" title="课程设置">
          <span aria-hidden="true">☰</span>
          <span class="action-text">课程设置</span>
          <span class="action-text-short">课程</span>
          <span class="user-arrow" aria-hidden="true">⌄</span>
        </summary>
        <div class="course-menu-panel user-menu-panel glass">
          <button type="button" @click="emit('add-course'); courseMenuRef?.removeAttribute('open')">＋ 添加课程</button>
          <label class="upload">
            <input type="file" accept=".xlsx,.xlsm,.xls" @change="onUpload">
            <span>↑ 导入课表</span>
          </label>
          <button type="button" @click="emit('open-adjustments'); courseMenuRef?.removeAttribute('open')">⇄ 调课</button>
          <button class="danger-menu-item" type="button" :disabled="!schedule" @click="emit('delete-schedule'); courseMenuRef?.removeAttribute('open')">删除当前课表</button>
        </div>
      </details>
      <a
        v-if="!isNative"
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
