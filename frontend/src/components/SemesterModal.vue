<script setup>
import { computed, ref, watch } from 'vue';
import {
  defaultEndDate,
  isScheduleActiveToday,
  localDate,
  scheduleWeekCount,
  termWeek,
} from '../utils/schedule.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  schedule: { type: Object, default: null },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(['close', 'save', 'delete']);

const form = ref({
  name: '',
  term: '',
  start_date: '',
  end_date: '',
});

const errorMsg = ref('');
const noticeMsg = ref('');
const weekCount = ref(20);

function scheduleForm(sched) {
  return {
    name: sched?.name || '',
    term: sched?.term || '',
    start_date: sched?.start_date?.slice(0, 10) || '',
    end_date: sched?.end_date?.slice(0, 10) || '',
  };
}

function resetForm() {
  form.value = scheduleForm(props.schedule);
  weekCount.value = props.schedule?.start_date
    ? scheduleWeekCount(props.schedule)
    : 20;
  errorMsg.value = '';
  noticeMsg.value = '';
}

watch(
  [() => props.open, () => props.schedule],
  ([open]) => {
    if (open) resetForm();
  },
  { immediate: true }
);

const hasChanges = computed(() => {
  return JSON.stringify(form.value) !== JSON.stringify(scheduleForm(props.schedule));
});
const hasInvalidDates = computed(() => Boolean(
  form.value.start_date
  && form.value.end_date
  && form.value.end_date < form.value.start_date
));
const canSave = computed(() => Boolean(
  form.value.name.trim()
  && !hasInvalidDates.value
  && hasChanges.value
  && !props.saving
));

const totalWeeks = computed(() => {
  return scheduleWeekCount({
    start_date: form.value.start_date,
    end_date: form.value.end_date,
    courses: props.schedule?.courses,
  });
});

const statusText = computed(() => {
  if (!form.value.start_date) return '尚未设置开学日期';
  const dummy = {
    start_date: form.value.start_date,
    end_date: form.value.end_date,
  };
  const active = isScheduleActiveToday(dummy);
  if (active) {
    const curr = termWeek(form.value.start_date, totalWeeks.value);
    return `进行中 · 当前为第 ${curr} 周`;
  }
  const start = localDate(form.value.start_date);
  const now = new Date();
  if (start && start > now) {
    return '未开学 · 将在开学后自动生效';
  }
  return '历史学期 · 已结束，浏览时默认显示第 1 周';
});

const isActiveToday = computed(() => {
  return isScheduleActiveToday({
    start_date: form.value.start_date,
    end_date: form.value.end_date,
  });
});

function applyWeekCount() {
  if (!form.value.start_date) {
    errorMsg.value = '请先选择开学日期';
    return;
  }
  const weeks = Math.max(1, Math.min(30, Number(weekCount.value) || 20));
  weekCount.value = weeks;
  form.value.end_date = defaultEndDate(form.value.start_date, weeks);
  errorMsg.value = '';
  noticeMsg.value = `已按 ${weeks} 周推算，结束日期为 ${form.value.end_date}。`;
}

function onSave() {
  errorMsg.value = '';
  noticeMsg.value = '';
  if (!form.value.name.trim()) {
    errorMsg.value = '课表名称不能为空';
    return;
  }
  if (form.value.start_date && form.value.end_date && form.value.end_date < form.value.start_date) {
    errorMsg.value = '学期结束日期不能早于开学日期';
    return;
  }
  emit('save', {
    name: form.value.name.trim(),
    term: form.value.term.trim(),
    start_date: form.value.start_date || null,
    end_date: form.value.end_date || null,
  });
}
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="emit('close')">
    <form class="modal" @submit.prevent="onSave">
      <div class="modal-head">
        <div>
          <p>学期与日期管理</p>
          <h2>学期设置</h2>
        </div>
        <button type="button" class="icon" @click="emit('close')">×</button>
      </div>

      <div class="status-card" :class="{ active: isActiveToday }">
        <span class="status-dot"></span>
        <div class="status-info">
          <b>{{ statusText }}</b>
          <small>根据开学与结束日期推算，课表共 {{ totalWeeks }} 周</small>
        </div>
      </div>

      <label>
        课表名称
        <input v-model="form.name" required maxlength="80" placeholder="例如：我的课表">
      </label>

      <label>
        所属学期
        <input v-model="form.term" maxlength="80" placeholder="例如：2026-2027学年第1学期">
      </label>

      <div class="fields">
        <label>
          开学日期 (周一)
          <input v-model="form.start_date" type="date">
        </label>
        <label>
          学期周数
          <input v-model.number="weekCount" type="number" min="1" max="30" inputmode="numeric">
        </label>
      </div>

      <div class="date-result">
        <label>
          结束日期 (周日)
          <input v-model="form.end_date" type="date" readonly>
        </label>
        <button
          type="button"
          class="uiverse-button date-tag"
          :disabled="!form.start_date || !weekCount || saving"
          @click="applyWeekCount"
        >
          按周数推算结束日期
        </button>
      </div>

      <p v-if="errorMsg" class="import-inline-error">{{ errorMsg }}</p>
      <p v-else-if="noticeMsg" class="date-notice">{{ noticeMsg }}</p>

      <p class="import-help">
        提示：每个学年、学期拥有独立的开学日期与周数。历史学期打开时会自动保持独立定位，不会影响当前学期的“今天”高亮与自动选周。
      </p>

      <div class="modal-actions">
        <button
          v-if="schedule?.id"
          type="button"
          class="danger uiverse-button"
          :disabled="saving"
          @click="emit('delete')"
        >
          删除此课表
        </button>
        <span></span>
        <button class="uiverse-button" type="button" :disabled="saving" @click="emit('close')">取消</button>
        <button class="primary uiverse-button" type="submit" :disabled="!canSave">
          {{ saving ? '保存中…' : hasChanges ? '保存设置' : '已保存' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.status-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.2);
  margin-bottom: 4px;
}
.status-card.active {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.25);
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #94a3b8;
  flex-shrink: 0;
}
.status-card.active .status-dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}
.status-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.status-info b {
  font-size: 0.88rem;
  color: #1e293b;
}
.status-info small {
  font-size: 0.76rem;
  color: #64748b;
}
.input-with-btn {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.input-with-btn input {
  flex: 1;
  margin-top: 0;
}
.btn-inline {
  padding: 0 12px;
  font-size: 0.8rem;
  white-space: nowrap;
}
.date-notice {
  margin: 0;
  color: #047857;
  font-size: 0.8rem;
}
.date-result {
  display: flex;
  align-items: end;
  gap: 8px;
  margin-bottom: 6px;
}
.date-result label {
  flex: 1;
}
.date-tag {
  font-size: 0.78rem;
  padding: 4px 10px;
  border-radius: 999px;
}
</style>
