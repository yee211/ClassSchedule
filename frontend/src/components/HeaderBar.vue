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
]);

function onUpload(event) {
  emit('upload', event);
}
</script>

<template>
  <header class="top glass">
    <div><span class="brand-dot"></span><strong>简课</strong></div>
    <div class="top-actions">
      <button
        class="header-action delete-schedule uiverse-button"
        type="button"
        :disabled="!schedule"
        @click="emit('delete-schedule')"
      >
        <span aria-hidden="true">−</span> 删除课表
      </button>
      <button
        class="header-action uiverse-button"
        type="button"
        @click="emit('add-course')"
      >
        <span aria-hidden="true">＋</span> 添加课程
      </button>
      <label class="header-action upload uiverse-button">
        <input type="file" accept=".xlsx,.xlsm,.xls" @change="onUpload">
        <span aria-hidden="true">↑</span> 上传课表
      </label>
      <span class="user-badge" v-if="user" :title="user.email">{{ user.username }}</span>
      <button class="header-action logout uiverse-button" type="button" @click="emit('logout')">退出</button>
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
