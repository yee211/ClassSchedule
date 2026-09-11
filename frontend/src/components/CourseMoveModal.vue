<script setup>
import { days } from '../utils/schedule.js';

defineProps({
  open: { type: Boolean, default: false },
  move: { type: Object, default: null },
  week: { type: Number, default: 1 },
  saving: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'save-week', 'save-all']);
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="!saving && emit('close')">
    <section class="modal move-modal">
      <div class="modal-head">
        <div><p>拖动课程</p><h2>确认调整范围</h2></div>
        <button type="button" class="icon" :disabled="saving" @click="emit('close')">×</button>
      </div>
      <div class="move-summary">
        <b>{{ move?.course?.name }}</b>
        <span>{{ days[(move?.course?.weekday || 1) - 1] }} 第{{ move?.course?.start_section }}-{{ move?.course?.end_section }}节</span>
        <i>↓</i>
        <strong>{{ days[(move?.weekday || 1) - 1] }} 第{{ move?.start_section }}-{{ move?.end_section }}节</strong>
      </div>
      <p class="adjustment-hint">默认只调整当前查看的第 {{ week }} 周，其他周保持原时间。</p>
      <div class="move-actions">
        <button class="uiverse-button" type="button" :disabled="saving" @click="emit('close')">取消</button>
        <button v-if="!move?.course?.adjusted_week" class="uiverse-button" type="button" :disabled="saving" @click="emit('save-all')">修改整学期</button>
        <button class="primary uiverse-button" type="button" :disabled="saving" @click="emit('save-week')">{{ saving ? '保存中…' : `仅调整第 ${week} 周` }}</button>
      </div>
    </section>
  </div>
</template>
