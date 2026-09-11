<script setup>
import { computed } from 'vue';
import {
  courseKey,
  days,
  formatWeeks,
  timeRange,
} from '../utils/schedule.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  course: { type: Object, default: null },
  colorMap: { type: Map, default: () => new Map() },
});

const emit = defineEmits(['close', 'edit', 'adjust']);

const courseHexColor = computed(() => {
  if (!props.course) return '#5B8DEF';
  return props.colorMap.get(courseKey(props.course.name)) || '#5B8DEF';
});
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="emit('close')">
    <section class="modal preview-modal">
      <div class="modal-head">
        <div>
          <p>课程详情</p>
          <h2>{{ course?.name }}</h2>
        </div>
        <button type="button" class="icon" @click="emit('close')">×</button>
      </div>
      <div class="preview-details">
        <div><span>教师</span><b>{{ course?.teacher || '未填写' }}</b></div>
        <div><span>教室</span><b>{{ course?.room || '未填写' }}</b></div>
        <div>
          <span>上课时间</span>
          <b>{{ days[(course?.weekday || 1) - 1] }} · {{ timeRange(course || {}) }}</b>
        </div>
        <div><span>上课周次</span><b>{{ formatWeeks(course?.weeks) || '每周' }}</b></div>
        <div>
          <span>课程颜色</span>
          <b class="color-preview">
            <i :style="{ background: courseHexColor }"></i>
            {{ courseHexColor }}
          </b>
        </div>
      </div>
      <div class="modal-actions">
        <span></span>
        <button class="uiverse-button" type="button" @click="emit('close')">关闭</button>
        <button class="uiverse-button" type="button" @click="emit('adjust', course)">
          {{ course?.adjusted_week ? '修改调课' : '调课' }}
        </button>
        <button class="primary uiverse-button" type="button" @click="emit('edit', course)">编辑</button>
      </div>
    </section>
  </div>
</template>
