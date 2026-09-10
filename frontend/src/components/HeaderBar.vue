<script setup>
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
  'change-wallpaper',
]);

function onUpload(event) {
  emit('upload', event);
}

function onWallpaperChange(event) {
  emit('change-wallpaper', event);
}
</script>

<template>
  <header class="top glass">
    <div class="brand"><span class="brand-dot"></span><strong>简课</strong></div>
    <div class="top-actions">
      <button
        class="header-action delete-schedule uiverse-button"
        type="button"
        :disabled="!schedule"
        title="删除课表"
        @click="emit('delete-schedule')"
      >
        <span aria-hidden="true">−</span>
        <span class="action-text">删除课表</span>
        <span class="action-text-short">删课</span>
      </button>
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
      <label class="header-action wallpaper-btn uiverse-button" title="更换背景壁纸">
        <input type="file" accept="image/*" @change="onWallpaperChange">
        <span aria-hidden="true">🖼️</span>
        <span class="action-text">换壁纸</span>
        <span class="action-text-short">壁纸</span>
      </label>
      <span class="user-badge" v-if="user" :title="user.email">{{ user.username }}</span>
      <button class="header-action logout uiverse-button" type="button" title="退出登录" @click="emit('logout')">退出</button>
      <button
        type="button"
        class="night-mode-button"
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
