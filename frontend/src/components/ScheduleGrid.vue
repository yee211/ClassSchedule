<script setup>
import { computed } from 'vue';
import {
  courseKey,
  days,
  defaultSectionTimes,
  timeRange,
  weekDayDate,
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
  gridTemplateRows: `64px repeat(${maxSections.value}, 78px)`,
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
  return {
    gridColumn: `${course.weekday + 1}`,
    gridRow: `${course.start_section + 1}/${course.end_section + 2}`,
    '--course': props.colorMap.get(courseKey(course.name)) || '#5B8DEF',
  };
}
</script>

<template>
  <section class="schedule glass" :class="{ busy: loading }">
    <div v-if="loading" class="state">正在读取课表…</div>
    <div v-else-if="!schedule" class="state">还没有课表</div>
    <div v-else class="grid" :style="gridStyle">
      <div class="corner">节次</div>
      <div v-for="(day, index) in days" :key="day" class="day">
        <b>{{ day }}</b>
        <span>{{ weekDayDate(schedule.start_date, index + 1, week) }}</span>
      </div>
      <template v-for="section in maxSections" :key="section">
        <div class="section" :style="{ gridColumn: 1, gridRow: section + 1 }">
          <b>{{ section }}</b>
          <span>
            {{ defaultSectionTimes[section - 1]?.[0] || '' }}<br>
            {{ defaultSectionTimes[section - 1]?.[1] || '' }}
          </span>
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
        <b>{{ course.name }}</b>
        <span>{{ course.room }} · {{ course.teacher }}</span>
        <small>{{ timeRange(course) }}</small>
      </button>
    </div>
  </section>
</template>
