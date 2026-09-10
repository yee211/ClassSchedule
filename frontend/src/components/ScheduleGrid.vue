<script setup>
import { computed } from 'vue';
import {
  cleanSectionTime,
  courseKey,
  days,
  defaultSectionTimes,
  isDayToday,
  shortDay,
  timeRange,
  weekDayNumber,
  weekMonth,
} from '../utils/schedule.js';

const props = defineProps({
  schedule: { type: Object, default: null },
  week: { type: Number, default: 1 },
  loading: { type: Boolean, default: false },
  colorMap: { type: Map, default: () => new Map() },
});

const emit = defineEmits(['preview-course']);

const maxSections = computed(() => {
  const courses = props.schedule?.courses || [];
  const maxInCourses = courses.length ? Math.max(...courses.map(c => c.end_section || 0)) : 10;
  return Math.min(12, Math.max(10, maxInCourses));
});

const gridStyle = computed(() => ({
  gridTemplateRows: `var(--grid-header-height, 46px) repeat(${maxSections.value}, var(--grid-section-height, 68px))`,
}));

const activeCourses = computed(() => {
  return props.schedule?.courses?.filter(c => !c.weeks?.length || c.weeks.includes(props.week)) || [];
});

const displayCourses = computed(() => {
  const result = [];
  const sorted = [...activeCourses.value].sort((a, b) => a.weekday - b.weekday || a.start_section - b.start_section);
  for (const course of sorted) {
    const previous = result[result.length - 1];
    const canMerge = previous
      && courseKey(previous.name) === courseKey(course.name)
      && previous.teacher === course.teacher
      && previous.room === course.room
      && previous.weekday === course.weekday
      && previous.end_section + 1 === course.start_section;
    if (canMerge) {
      previous.end_section = course.end_section;
    } else {
      result.push({ ...course });
    }
  }
  return result;
});

function courseStyle(course) {
  const span = course.end_section - course.start_section + 1;
  return {
    gridColumn: `${course.weekday + 1}`,
    gridRow: `${course.start_section + 1}/${course.end_section + 2}`,
    '--course': props.colorMap.get(courseKey(course.name)) || '#5B8DEF',
    '--max-lines': span * 4,
  };
}
</script>

<template>
  <section class="schedule glass" :class="{ busy: loading }" aria-label="每周课程表" tabindex="0">
    <div v-if="loading" class="state">正在读取课表…</div>
    <div v-else-if="!schedule" class="state">还没有课表</div>
    <div v-else class="grid" :style="gridStyle">
      <div class="corner">
        <span class="corner-month">{{ weekMonth(schedule.start_date, week) }}</span>
        <span class="corner-label">节次</span>
      </div>
      <div
        v-for="(day, index) in days"
        :key="day"
        class="day"
        :class="{ 'is-today': isDayToday(schedule.start_date, index + 1, week, schedule) }"
      >
        <span class="day-date">{{ weekDayNumber(schedule.start_date, index + 1, week) }}</span>
        <b class="day-name">{{ shortDay(day) }}</b>
      </div>
      <template v-for="section in maxSections" :key="section">
        <div class="section" :style="{ gridColumn: 1, gridRow: section + 1 }">
          <b class="section-num">{{ section }}</b>
          <div class="section-times">
            <span>{{ cleanSectionTime(defaultSectionTimes[section - 1]?.[0]) }}</span>
            <span>{{ cleanSectionTime(defaultSectionTimes[section - 1]?.[1]) }}</span>
          </div>
        </div>
        <div
          v-for="day in 7"
          :key="day"
          class="cell"
          :style="{ gridColumn: day + 1, gridRow: section + 1 }"
        ></div>
      </template>
      <button
        v-for="course in displayCourses"
        :key="course.id"
        class="course"
        :style="courseStyle(course)"
        @click="emit('preview-course', course)"
      >
        <span class="course-text">
          <span class="course-name">{{ course.name }}</span>
          <span class="course-room" v-if="course.room">({{ course.room }})</span>
          <span class="course-teacher" v-if="course.teacher">{{ course.teacher }}</span>
        </span>
      </button>
    </div>
  </section>
</template>
