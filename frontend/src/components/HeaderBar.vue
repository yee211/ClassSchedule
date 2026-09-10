<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

defineProps({
  user: { type: Object, default: null },
  schedule: { type: Object, default: null },
  bgMode: { type: String, default: 'transparent' },
});

const emit = defineEmits([
  'delete-schedule',
  'add-course',
  'upload',
  'logout',
  'toggle-night-mode',
]);

const userMenuRef = ref(null);

function onUpload(event) {
  emit('upload', event);
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
    <div class="brand"><span class="brand-dot"></span><strong>简课</strong></div>
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
      <details v-if="user" ref="userMenuRef" class="user-menu">
        <summary class="user-badge uiverse-button" :title="user.email">
          <span class="user-avatar" aria-hidden="true">{{ user.username?.slice(0, 1)?.toUpperCase() }}</span>
          <span class="user-name">{{ user.username }}</span>
          <span class="user-arrow" aria-hidden="true">⌄</span>
        </summary>
        <div class="user-menu-panel glass">
          <div class="user-menu-meta"><b>{{ user.username }}</b><small>{{ user.email }}</small></div>
          <button type="button" :disabled="!schedule" @click="emit('delete-schedule')">删除当前课表</button>
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
