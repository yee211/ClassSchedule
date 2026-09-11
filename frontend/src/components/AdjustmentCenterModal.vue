<script setup>
import { ref, watch, computed } from 'vue';
import { days } from '../utils/schedule.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  records: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'image', 'revoke']);
const mode = ref('menu');
const selectedRecord = ref(null);
const currentTab = ref('all');
const imageInput = ref(null);

watch(() => props.open, value => {
  if (value) {
    mode.value = 'menu';
    selectedRecord.value = null;
    currentTab.value = 'all';
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

function formatPlace(weekday, start, end, room) {
  if (!weekday) return '未设置';
  return `${days[weekday - 1] || '周?'} 第${start}-${end}节${room ? ` · ${room}` : ''}`;
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  if (isNaN(d.getTime())) return isoStr;
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const tabs = [
  { id: 'all', label: '全部' },
  { id: 'batch_import', label: '图片调课' },
  { id: 'drag_move', label: '位置移动' },
  { id: 'manual_edit', label: '主动编辑' },
];

const filteredRecords = computed(() => {
  if (currentTab.value === 'all') return props.records;
  return props.records.filter(r => r.action_type === currentTab.value);
});

function viewDetail(record) {
  selectedRecord.value = record;
  mode.value = 'detail';
}
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="!loading && emit('close')">
    <section class="modal adjustment-center-modal">
      <div class="modal-head">
        <div>
          <p>课程变更</p>
          <h2>{{ mode === 'menu' ? '调课中心' : mode === 'detail' ? '调课详情' : '调课与修改记录' }}</h2>
        </div>
        <button type="button" class="icon" :disabled="loading" @click="emit('close')">×</button>
      </div>

      <!-- Menu Mode -->
      <div v-if="mode === 'menu'" class="adjustment-entry-grid">
        <button type="button" class="adjustment-entry" @click="chooseImage">
          <span>▣</span><b>课程图片识别调课</b><small>上传学校调课通知截图自动识别</small>
        </button>
        <button type="button" class="adjustment-entry" @click="mode = 'records'">
          <span>≡</span><b>调课与修改记录</b><small>查看调课通知、拖拽移动与编辑记录</small>
        </button>
        <input ref="imageInput" class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" @change="onImage">
      </div>

      <!-- Detail Mode: 2 items per row grid (一行两个，再上下排列) -->
      <div v-else-if="mode === 'detail'" class="record-detail-view">
        <div class="detail-header-bar">
          <div>
            <h3>{{ selectedRecord?.title || '批量调课详情' }}</h3>
            <p class="detail-subtitle">
              {{ selectedRecord?.description }}
              <span v-if="selectedRecord?.created_at">· {{ formatTime(selectedRecord.created_at) }}</span>
            </p>
          </div>
          <button type="button" class="back-link-btn" @click="mode = 'records'">← 返回记录</button>
        </div>

        <div v-if="selectedRecord?.details?.length" class="record-detail-grid">
          <div
            v-for="(item, idx) in selectedRecord.details"
            :key="`${item.course_id || idx}-${item.week}`"
            class="detail-grid-card"
          >
            <div class="detail-card-head">
              <span class="detail-course-name">《{{ item.course_name }}》</span>
              <span class="badge-week">第 {{ item.week }} 周</span>
            </div>
            <div class="detail-change-path">
              <div class="change-line old">
                <span class="change-label">原时段</span>
                <span class="change-val">{{ formatPlace(item.old_weekday, item.old_start_section, item.old_end_section, item.old_room) }}</span>
              </div>
              <div class="change-arrow-icon">↓</div>
              <div class="change-line new">
                <span class="change-label">新时段</span>
                <span class="change-val">{{ formatPlace(item.new_weekday, item.new_start_section, item.new_end_section, item.new_room) }}</span>
              </div>
            </div>
            <div class="detail-card-footer">
              <button
                v-if="item.can_revoke"
                type="button"
                class="danger-link"
                @click="emit('revoke', item)"
              >
                撤销此调课
              </button>
              <span v-else class="revoked-tag">原时间生效中</span>
            </div>
          </div>
        </div>
        <p v-else class="empty-records">无详细课程变动数据</p>

        <div class="modal-actions">
          <button type="button" class="uiverse-button" @click="mode = 'records'">返回记录列表</button>
          <span></span>
          <button type="button" class="uiverse-button" @click="emit('close')">关闭</button>
        </div>
      </div>

      <!-- Records Mode -->
      <div v-else class="adjustment-records-container">
        <div class="records-filter-tabs">
          <button
            v-for="t in tabs"
            :key="t.id"
            type="button"
            class="filter-tab-btn"
            :class="{ active: currentTab === t.id }"
            @click="currentTab = t.id"
          >
            {{ t.label }}
          </button>
        </div>

        <div class="adjustment-records-list">
          <p v-if="!filteredRecords.length" class="empty-records">当前分类下暂无记录</p>
          <article
            v-for="rec in filteredRecords"
            :key="rec.id"
            class="change-log-item"
            :class="`type-${rec.action_type}`"
          >
            <div class="change-log-head">
              <span class="badge-tag" :class="`tag-${rec.action_type}`">
                {{ rec.action_type === 'batch_import' ? '图片调课' : rec.action_type === 'drag_move' ? '位置移动' : '主动编辑' }}
              </span>
              <span class="change-log-time">{{ formatTime(rec.created_at) }}</span>
            </div>

            <div class="change-log-body">
              <div class="change-log-title">{{ rec.title }}</div>
              <div class="change-log-desc">{{ rec.description }}</div>

              <!-- Batch Import Details Action -->
              <div v-if="rec.action_type === 'batch_import'" class="change-log-actions">
                <button type="button" class="view-detail-btn" @click="viewDetail(rec)">
                  查看详情（{{ rec.details?.length || 0 }} 门次） →
                </button>
              </div>

              <!-- Drag move with single-week adjustment can_revoke -->
              <div v-else-if="rec.action_type === 'drag_move' && rec.can_revoke && rec.details && rec.details[0]" class="change-log-actions">
                <button
                  type="button"
                  class="danger-link"
                  @click="emit('revoke', rec.details[0])"
                >
                  撤销移动
                </button>
              </div>

              <!-- Manual edit details diff badges -->
              <div v-else-if="rec.action_type === 'manual_edit' && Array.isArray(rec.details)" class="edit-diff-list">
                <span v-for="(diff, di) in rec.details" :key="di" class="diff-tag">
                  {{ diff.label }}: {{ diff.old }} → {{ diff.new }}
                </span>
              </div>
            </div>
          </article>
        </div>

        <div class="modal-actions">
          <button type="button" class="uiverse-button" @click="mode = 'menu'">返回</button>
          <span></span>
          <button type="button" class="uiverse-button" @click="emit('close')">关闭</button>
        </div>
      </div>
    </section>
  </div>
</template>
