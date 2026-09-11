<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '操作确认' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
});

const emit = defineEmits(['confirm', 'cancel']);
</script>

<template>
  <div v-if="open" class="backdrop confirm-backdrop" @click.self="emit('cancel')">
    <section class="modal confirm-modal" role="dialog" aria-modal="true">
      <div class="modal-head">
        <div>
          <p>操作提示</p>
          <h2>{{ title }}</h2>
        </div>
        <button type="button" class="icon" aria-label="关闭" @click="emit('cancel')">×</button>
      </div>

      <div class="confirm-content">
        <p class="confirm-message">{{ message }}</p>
      </div>

      <div class="modal-actions confirm-actions">
        <button class="uiverse-button" type="button" @click="emit('cancel')">
          {{ cancelText }}
        </button>
        <button
          class="uiverse-button"
          :class="danger ? 'danger' : 'primary'"
          type="button"
          @click="emit('confirm')"
        >
          {{ confirmText }}
        </button>
      </div>
    </section>
  </div>
</template>
