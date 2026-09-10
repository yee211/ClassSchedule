<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { isScheduleActiveToday, weekRange } from '../utils/schedule.js';

const props = defineProps({
  schedules: { type: Array, default: () => [] },
  schedule: { type: Object, default: null },
  week: { type: Number, default: 1 },
  currentWeek: { type: Number, default: 1 },
  weekOptions: { type: Array, default: () => [] },
});

const emit = defineEmits([
  'update:week',
  'select-schedule',
  'go-current-week',
  'open-semester-settings',
]);

const weekMenuOpen = ref(false);

const isActiveSchedule = computed(() => isScheduleActiveToday(props.schedule));

const isResetActive = computed(() => {
  if (isActiveSchedule.value) {
    return props.week !== props.currentWeek;
  }
  return props.week !== 1;
});

const resetBtnText = computed(() => {
  if (isActiveSchedule.value) {
    return props.week === props.currentWeek ? '本周' : '回到本周';
  }
  return props.week === 1 ? '首周' : '回到首周';
});

function toggleWeekMenu() {
  weekMenuOpen.value = !weekMenuOpen.value;
}

function closeWeekMenu(event) {
  if (!event.target.closest('.week-menu')) {
    weekMenuOpen.value = false;
  }
}

function selectWeek(value) {
  emit('update:week', value);
  weekMenuOpen.value = false;
}

function onGoCurrentWeek() {
  if (isActiveSchedule.value) {
    emit('go-current-week');
  } else {
    emit('update:week', 1);
  }
  weekMenuOpen.value = false;
}

function prevWeek() {
  emit('update:week', Math.max(1, props.week - 1));
}

function nextWeek() {
  emit('update:week', Math.min(props.weekOptions.length, props.week + 1));
}

function onSelectSchedule(event) {
  emit('select-schedule', event);
  weekMenuOpen.value = false;
}

onMounted(() => {
  document.addEventListener('click', closeWeekMenu);
});

onUnmounted(() => {
  document.removeEventListener('click', closeWeekMenu);
});
</script>

<template>
  <section class="toolbar glass" aria-label="课表控制">
    <div class="term-picker">
      <div class="term-meta-row">
        <p class="term-status-line">
          <span>{{ isActiveSchedule ? '当前学期' : '学期' }}</span>
          <span v-if="schedule && !isActiveSchedule" class="history-pill">往期</span>
        </p>
        <button
          v-if="schedule"
          type="button"
          class="term-edit-btn uiverse-button"
          title="设置学期与开学日期"
          @click="emit('open-semester-settings')"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
          <span>设置</span>
        </button>
      </div>
      <label v-if="schedules.length > 1" class="term-select-wrap uiverse-button">
        <span class="sr-only">切换学期</span>
        <select :value="schedule?.id" aria-label="切换学期" @change="onSelectSchedule">
          <option v-for="item in schedules" :key="item.id" :value="item.id">
            {{ item.term || item.name || `课表 ${item.id}` }}
          </option>
        </select>
        <i aria-hidden="true">⌄</i>
      </label>
      <h1 v-else>{{ schedule?.term || '我的课表' }}</h1>
    </div>
    <div class="week-picker">
      <button class="week-nav uiverse-button" aria-label="上一周" :disabled="week <= 1" @click="prevWeek">‹</button>
      <div class="week-menu" @click.stop>
        <button class="week-trigger uiverse-button" :aria-expanded="weekMenuOpen" aria-haspopup="listbox" @click="toggleWeekMenu">
          <span><b>第{{ week }}周</b><small>{{ weekRange(schedule?.start_date, week) }}</small></span>
          <i :class="{ open: weekMenuOpen }">⌄</i>
        </button>
        <div v-if="weekMenuOpen" class="week-menu-panel glass" role="listbox" aria-label="选择周次">
          <div class="week-menu-head">
            <b>选择周次</b>
            <button type="button" class="uiverse-button" @click="onGoCurrentWeek">{{ isActiveSchedule ? '回到本周' : '回到第 1 周' }}</button>
          </div>
          <div class="week-menu-grid">
            <button
              v-for="item in weekOptions"
              :key="item"
              type="button"
              class="week-option"
              :class="{ selected: week === item }"
              :aria-selected="week === item"
              @click="selectWeek(item)"
            >
              <b>第{{ item }}周</b><small>{{ weekRange(schedule?.start_date, item) }}</small>
            </button>
          </div>
        </div>
      </div>
      <button
        class="reset-week uiverse-button"
        :class="{ active: isResetActive }"
        @click="onGoCurrentWeek"
      >
        {{ resetBtnText }}
      </button>
      <button class="week-nav uiverse-button" aria-label="下一周" :disabled="week >= weekOptions.length" @click="nextWeek">›</button>
    </div>
  </section>
</template>

<style scoped>
.term-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.term-status-line {
  margin: 0 !important;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.history-pill {
  font-size: 0.68rem;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.25);
  color: #64748b;
  font-weight: 600;
}
.term-edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px !important;
  font-size: 0.72rem !important;
  border-radius: 999px !important;
  color: #64748b !important;
  cursor: pointer;
}
.term-edit-btn:hover {
  color: #0284c7 !important;
}
</style>

