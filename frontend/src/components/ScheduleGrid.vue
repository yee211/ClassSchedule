<script setup>
import { computed, onUnmounted, reactive, ref } from 'vue';
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

const emit = defineEmits(['preview-course', 'move-course', 'move-conflict']);
const gridRef = ref(null);
const drag = reactive({ active: false, pending: false, course: null, weekday: 1, start: 1, pointerId: null, pointerType: '', x: 0, y: 0 });
let holdTimer = null;
let suppressClick = false;
let dragElement = null;

const maxSections = computed(() => {
  const courses = props.schedule?.courses || [];
  const maxInCourses = courses.length ? Math.max(...courses.map(c => c.end_section || 0)) : 10;
  return Math.min(12, Math.max(10, maxInCourses));
});

const gridStyle = computed(() => ({
  gridTemplateRows: `var(--grid-header-height, 46px) repeat(${maxSections.value}, var(--grid-section-height, 68px))`,
}));

const activeCourses = computed(() => {
  return (props.schedule?.courses || [])
    .filter(c => !c.weeks?.length || c.weeks.includes(props.week))
    .map(course => {
      const adjustment = course.adjustments?.find(item => item.week === props.week);
      return adjustment
        ? {
          ...course,
          ...adjustment,
          id: course.id,
          adjustment_id: adjustment.id,
          adjusted_week: props.week,
          original_course: course,
        }
        : course;
    });
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
  const isDragging = drag.active && drag.course?.id === course.id;
  const weekday = isDragging ? drag.weekday : course.weekday;
  const startSection = isDragging ? drag.start : course.start_section;
  const span = course.end_section - course.start_section + 1;
  return {
    gridColumn: `${weekday + 1}`,
    gridRow: `${startSection + 1}/${startSection + span + 1}`,
    '--course': props.colorMap.get(courseKey(course.name)) || '#5B8DEF',
    '--max-lines': span * 4,
  };
}

function activateDrag(element) {
  drag.pending = false;
  drag.active = true;
  suppressClick = true;
  element?.setPointerCapture?.(drag.pointerId);
  updateDragTarget(drag.x, drag.y);
}

function beginDrag(event, course) {
  if (event.button !== undefined && event.button !== 0) return;
  drag.course = course;
  drag.pointerId = event.pointerId;
  drag.pointerType = event.pointerType || 'mouse';
  dragElement = event.currentTarget;
  drag.x = event.clientX;
  drag.y = event.clientY;
  drag.weekday = course.weekday;
  drag.start = course.start_section;
  drag.pending = true;
  if (drag.pointerType === 'touch') holdTimer = window.setTimeout(() => activateDrag(dragElement), 400);
}

function updateDragTarget(clientX, clientY) {
  const grid = gridRef.value;
  if (!grid || !drag.course) return;
  const rect = grid.getBoundingClientRect();
  const corner = grid.querySelector('.corner')?.getBoundingClientRect();
  const day = grid.querySelector('.day')?.getBoundingClientRect();
  const leftWidth = corner?.width || 48;
  const headerHeight = day?.height || 46;
  const dayWidth = (rect.width - leftWidth) / 7;
  const rowHeight = (rect.height - headerHeight) / maxSections.value;
  const duration = drag.course.end_section - drag.course.start_section + 1;
  drag.weekday = Math.max(1, Math.min(7, Math.floor((clientX - rect.left - leftWidth) / dayWidth) + 1));
  drag.start = Math.max(1, Math.min(maxSections.value - duration + 1, Math.floor((clientY - rect.top - headerHeight) / rowHeight) + 1));
}

function continueDrag(event) {
  if (drag.pointerId !== event.pointerId || (!drag.pending && !drag.active)) return;
  if (drag.pending) {
    const distance = Math.hypot(event.clientX - drag.x, event.clientY - drag.y);
    if (drag.pointerType !== 'touch' && distance > 4) {
      activateDrag(dragElement);
      event.preventDefault();
      updateDragTarget(event.clientX, event.clientY);
    } else if (drag.pointerType === 'touch' && distance > 8) {
      window.clearTimeout(holdTimer);
      drag.pending = false;
    }
    return;
  }
  if (drag.active) {
    event.preventDefault();
    updateDragTarget(event.clientX, event.clientY);
  }
}

function finishDrag(event) {
  if (drag.pointerId !== event.pointerId) return;
  window.clearTimeout(holdTimer);
  if (drag.active && drag.course) {
    const duration = drag.course.end_section - drag.course.start_section + 1;
    const end = drag.start + duration - 1;
    const conflict = activeCourses.value.some(course => course.id !== drag.course.id
      && course.weekday === drag.weekday
      && drag.start <= course.end_section && end >= course.start_section);
    if (conflict) emit('move-conflict');
    else if (drag.weekday !== drag.course.weekday || drag.start !== drag.course.start_section) {
      emit('move-course', { course: drag.course, weekday: drag.weekday, start_section: drag.start, end_section: end });
    }
  }
  drag.active = false;
  drag.pending = false;
  drag.course = null;
  drag.pointerId = null;
  dragElement = null;
  window.setTimeout(() => { suppressClick = false; }, 0);
}

function openCourse(course) {
  if (!suppressClick) emit('preview-course', course);
}

onUnmounted(() => window.clearTimeout(holdTimer));
</script>

<template>
  <section class="schedule glass" :class="{ busy: loading }" aria-label="每周课程表" tabindex="0">
    <div v-if="loading" class="state">正在读取课表…</div>
    <div v-else-if="!schedule" class="state">还没有课表</div>
    <div v-else ref="gridRef" class="grid" :class="{ 'is-dragging': drag.active }" :style="gridStyle">
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
        :key="`${course.id}-${course.adjusted_week || 'regular'}`"
        class="course"
        :class="{ dragging: drag.active && drag.course?.id === course.id }"
        :style="courseStyle(course)"
        @click="openCourse(course)"
        @pointerdown="beginDrag($event, course)"
        @pointermove="continueDrag"
        @pointerup="finishDrag"
        @pointercancel="finishDrag"
        @contextmenu.prevent
      >
        <span class="course-text">
          <span v-if="course.adjusted_week" class="course-adjusted">调</span>
          <span class="course-name">{{ course.name }}</span>
          <span class="course-room" v-if="course.room">({{ course.room }})</span>
          <span class="course-teacher" v-if="course.teacher">{{ course.teacher }}</span>
        </span>
      </button>
    </div>
  </section>
</template>
