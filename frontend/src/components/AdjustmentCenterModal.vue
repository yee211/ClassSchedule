<script setup>
import { ref, watch, computed } from 'vue';
import { days } from '../utils/schedule.js';

const props = defineProps({
  open: { type: Boolean, default: false },
  records: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits(['close', 'image', 'revoke', 'restore', 'delete']);
const mode = ref('menu');
const selectedRecord = ref(null);
const imageInput = ref(null);
const swipedId = ref(null);

let touchStartX = 0;
let touchStartY = 0;

watch(() => props.open, value => {
  if (value) {
    mode.value = 'menu';
    selectedRecord.value = null;
    swipedId.value = null;
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

const filteredRecords = computed(() => {
  return props.records.filter(r => r.action_type === 'batch_import');
});

function viewDetail(record) {
  selectedRecord.value = record;
  mode.value = 'detail';
}

function getRecordDiffs(rec) {
  if (!Array.isArray(rec.details) || !rec.details.length) return [];
  const diffs = [];
  for (const item of rec.details) {
    if (item.label && (item.old !== undefined || item.new !== undefined)) {
      diffs.push({
        label: item.label,
        old: item.old,
        new: item.new,
      });
    } else if (item.old_weekday || item.new_weekday) {
      diffs.push({
        label: '上课时间',
        old: formatPlace(item.old_weekday, item.old_start_section, item.old_end_section),
        new: formatPlace(item.new_weekday, item.new_start_section, item.new_end_section),
      });
      if (item.old_room !== item.new_room) {
        diffs.push({
          label: '教室地点',
          old: item.old_room || '未设置',
          new: item.new_room || '未设置',
        });
      }
    }
  }
  return diffs;
}

function canRevokeRecord(rec) {
  if (rec.can_revoke) return true;
  if (rec.course_id && Array.isArray(rec.details) && rec.details.length > 0) {
    return true;
  }
  return false;
}

function handleRevoke(rec) {
  if (rec.can_revoke && rec.details?.[0]?.week) {
    emit('revoke', rec.details[0]);
  } else if (rec.action_type === 'batch_import') {
    viewDetail(rec);
  } else if (rec.course_id) {
    emit('restore', rec);
  }
}

function onTouchStart(id, event) {
  touchStartX = event.touches[0].clientX;
  touchStartY = event.touches[0].clientY;
}

function onTouchEnd(id, event) {
  const diffX = event.changedTouches[0].clientX - touchStartX;
  const diffY = event.changedTouches[0].clientY - touchStartY;
  if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 35) {
    if (diffX < 0) {
      swipedId.value = id;
    } else if (swipedId.value === id) {
      swipedId.value = null;
    }
  }
}
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="!loading && emit('close')">
    <section class="modal adjustment-center-modal">
      <div class="modal-head">
        <div>
          <p>课程变更</p>
          <h2>{{ mode === 'menu' ? '调课中心' : mode === 'detail' ? '调课详情' : '调课通知记录' }}</h2>
        </div>
        <button type="button" class="icon" :disabled="loading" @click="emit('close')">×</button>
      </div>

      <!-- Menu Mode -->
      <div v-if="mode === 'menu'" class="adjustment-entry-grid">
        <button type="button" class="adjustment-entry" @click="chooseImage">
          <span>▣</span><b>课程图片识别调课</b><small>上传学校调课通知截图自动识别</small>
        </button>
        <button type="button" class="adjustment-entry" @click="mode = 'records'">
          <span>≡</span><b>调课通知记录</b><small>查看学校调课通知与批量调整详情</small>
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
        <div class="adjustment-records-list">
          <p v-if="!filteredRecords.length" class="empty-records">暂无调课通知记录</p>
          <div
            v-for="rec in filteredRecords"
            :key="rec.id"
            class="swipe-card-wrapper"
            @touchstart="onTouchStart(rec.id, $event)"
            @touchend="onTouchEnd(rec.id, $event)"
          >
            <!-- Background Swipe-Delete Button -->
            <button
              type="button"
              class="swipe-delete-btn"
              title="左滑删除记录"
              @click.stop="emit('delete', rec)"
            >
              <span>删除</span>
            </button>

            <!-- Foreground Card -->
            <article
              class="change-log-item swipe-card-front"
              :class="{ 'is-swiped': swipedId === rec.id, [`type-${rec.action_type}`]: true }"
              @click="swipedId === rec.id ? (swipedId = null) : null"
            >
              <div class="change-log-head">
                <span class="badge-tag" :class="`tag-${rec.action_type}`">
                  {{ rec.action_type === 'batch_import' ? '图片调课' : rec.action_type === 'drag_move' ? '位置移动' : '主动编辑' }}
                </span>
                <div class="head-right-actions">
                  <span class="change-log-time">{{ formatTime(rec.created_at) }}</span>
                  <button
                    type="button"
                    class="desktop-delete-btn"
                    title="删除此记录"
                    @click.stop="emit('delete', rec)"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div class="change-log-body">
                <div class="change-log-title">{{ rec.title }}</div>
                <div class="change-log-desc">{{ rec.description }}</div>

                <!-- Diff Chips: Render both time and room changes -->
                <div v-if="getRecordDiffs(rec).length" class="edit-diff-list">
                  <span v-for="(diff, di) in getRecordDiffs(rec)" :key="di" class="diff-tag">
                    {{ diff.label }}: {{ diff.old }} → {{ diff.new }}
                  </span>
                </div>

                <!-- Actions: Detail View & Revoke -->
                <div class="change-log-actions">
                  <button
                    v-if="rec.action_type === 'batch_import'"
                    type="button"
                    class="view-detail-btn"
                    @click="viewDetail(rec)"
                  >
                    查看详情（{{ rec.details?.length || 0 }} 门次） →
                  </button>
                  <button
                    v-if="canRevokeRecord(rec)"
                    type="button"
                    class="revoke-action-btn"
                    @click="handleRevoke(rec)"
                  >
                    撤销改动
                  </button>
                </div>
              </div>
            </article>
          </div>
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
