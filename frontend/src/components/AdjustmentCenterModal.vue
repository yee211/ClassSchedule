<script setup>
import { ref, watch } from 'vue';
import { days } from '../utils/schedule.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  records: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'image', 'text', 'revoke']);
const mode = ref('menu');
const description = ref('');
const imageInput = ref(null);

watch(() => props.open, value => {
  if (value) {
    mode.value = 'menu';
    description.value = '';
  }
});

function chooseImage() {
  imageInput.value?.click();
}

function onImage(event) {
  const file = event.target.files[0];
  event.target.value = '';
  if (file) emit('image', file);
}

function submitText() {
  const text = description.value.trim();
  if (text.length >= 5) emit('text', text);
}

function place(weekday, start, end, room) {
  return `${days[weekday - 1]} ${start}-${end}节${room ? ` · ${room}` : ''}`;
}
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="!loading && emit('close')">
    <section class="modal adjustment-center-modal">
      <div class="modal-head">
        <div><p>课程变更</p><h2>{{ mode === 'menu' ? '调课中心' : mode === 'text' ? '自然语言调课' : '调课记录' }}</h2></div>
        <button type="button" class="icon" :disabled="loading" @click="emit('close')">×</button>
      </div>

      <div v-if="mode === 'menu'" class="adjustment-entry-grid">
        <button type="button" class="adjustment-entry" @click="chooseImage">
          <span>▣</span><b>课程图片识别调课</b><small>上传学校调课通知截图</small>
        </button>
        <button type="button" class="adjustment-entry" @click="mode = 'text'">
          <span>✦</span><b>自然语言 AI 调课</b><small>直接描述课程如何调整</small>
        </button>
        <button type="button" class="adjustment-entry" @click="mode = 'records'">
          <span>≡</span><b>调课记录</b><small>查看或撤销已应用的调整</small>
        </button>
        <input ref="imageInput" class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" @change="onImage">
      </div>

      <form v-else-if="mode === 'text'" @submit.prevent="submitText">
        <p class="adjustment-privacy">描述内容会发送至你配置的阿里云百炼模型解析，应用前仍需确认。</p>
        <label>
          调课描述
          <textarea v-model="description" rows="6" maxlength="4000" placeholder="例如：把第3周周一的高等数学1-2节调到周四5-6节，教室改为南204"></textarea>
        </label>
        <div class="modal-actions">
          <button type="button" class="uiverse-button" @click="mode = 'menu'">返回</button><span></span>
          <button class="primary uiverse-button" type="submit" :disabled="loading || description.trim().length < 5">{{ loading ? '解析中…' : 'AI 识别' }}</button>
        </div>
      </form>

      <div v-else class="adjustment-records">
        <p v-if="!records.length" class="empty-records">当前课表还没有调课记录</p>
        <article v-for="record in records" :key="`${record.course_id}-${record.week}`" class="adjustment-record">
          <div><b>{{ record.course_name }}</b><small>第 {{ record.week }} 周</small></div>
          <span>{{ place(record.old_weekday, record.old_start_section, record.old_end_section, record.old_room) }}</span>
          <i>→</i>
          <strong>{{ place(record.weekday, record.start_section, record.end_section, record.room) }}</strong>
          <button type="button" class="danger-link" @click="emit('revoke', record)">撤销</button>
        </article>
        <div class="modal-actions"><button type="button" class="uiverse-button" @click="mode = 'menu'">返回</button><span></span><button type="button" class="uiverse-button" @click="emit('close')">关闭</button></div>
      </div>
    </section>
  </div>
</template>
