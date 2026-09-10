<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { weekRange } from '../utils/schedule.js';

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
]);

const weekMenuOpen = ref(false);

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
  emit('go-current-week');
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
      <p>当前学期</p>
      <label v-if="schedules.length > 1" class="term-select-wrap">
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
      <button class="week-nav" aria-label="上一周" :disabled="week <= 1" @click="prevWeek">‹</button>
      <div class="week-menu" @click.stop>
        <button class="week-trigger" :aria-expanded="weekMenuOpen" aria-haspopup="listbox" @click="toggleWeekMenu">
          <span><b>第{{ week }}周</b><small>{{ weekRange(schedule?.start_date, week) }}</small></span>
          <i :class="{ open: weekMenuOpen }">⌄</i>
        </button>
        <div v-if="weekMenuOpen" class="week-menu-panel glass" role="listbox" aria-label="选择周次">
          <div class="week-menu-head">
            <b>选择周次</b>
            <button type="button" @click="onGoCurrentWeek">回到本周</button>
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
        class="reset-week"
        :class="{ active: week !== currentWeek }"
        @click="onGoCurrentWeek"
      >
        {{ week === currentWeek ? '本周' : '回到本周' }}
      </button>
      <button class="week-nav" aria-label="下一周" :disabled="week >= weekOptions.length" @click="nextWeek">›</button>
    </div>
  </section>
</template>
