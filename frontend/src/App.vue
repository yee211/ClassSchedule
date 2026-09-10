<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import {
  authApi,
  clearAuth,
  coursesApi,
  getActiveScheduleId,
  getToken,
  importerApi,
  schedulesApi,
  setActiveScheduleId,
  setToken,
} from './api/index.js';
import {
  buildCourseColorMap,
  defaultEndDate,
  emptyCourse,
  formatWeeks,
  parseWeeks,
  scheduleWeekCount,
  termWeek,
} from './utils/schedule.js';

import HeaderBar from './components/HeaderBar.vue';
import ScheduleToolbar from './components/ScheduleToolbar.vue';
import ScheduleGrid from './components/ScheduleGrid.vue';
import CoursePreviewModal from './components/CoursePreviewModal.vue';
import CourseEditorModal from './components/CourseEditorModal.vue';
import ImporterModal from './components/ImporterModal.vue';
import AuthModal from './components/AuthModal.vue';

// 基础状态
const week = ref(1);
const currentWeek = ref(1);
const schedules = ref([]);
const schedule = ref(null);
const loading = ref(true);
const message = ref('');

// 用户认证状态
const user = ref(null);
const authMode = ref('login');
const authError = ref('');
const authLoading = ref(false);
const authForm = reactive({ email: '', username: '', password: '' });

// 弹窗状态
const previewOpen = ref(false);
const previewCourse = ref(null);

const editorOpen = ref(false);
const form = reactive(emptyCourse());

const importerOpen = ref(false);
const importing = ref(false);
const importSetup = ref(false);
const importFile = ref(null);
const importError = ref('');
const importEngine = ref('');
const importStartDate = ref('');
const importEndDate = ref('');

// 计算属性
const weekOptions = computed(() =>
  Array.from({ length: scheduleWeekCount(schedule.value) }, (_, index) => index + 1)
);

const courseColorMap = computed(() => buildCourseColorMap(schedule.value?.courses));

// 提示消息
function notify(text) {
  message.value = text;
  window.clearTimeout(notify.timer);
  notify.timer = window.setTimeout(() => {
    message.value = '';
  }, 2200);
}

// 登出
function logout() {
  clearAuth();
  user.value = null;
  schedule.value = null;
  schedules.value = [];
  loading.value = false;
}

// 登录 / 注册提交
async function submitAuth() {
  authError.value = '';
  const isRegister = authMode.value === 'register';
  const email = authForm.email.trim();
  const username = authForm.username.trim();

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    authError.value = '请输入有效的邮箱地址';
    return;
  }
  if (isRegister && username.length < 2) {
    authError.value = '用户名至少需要 2 个字符';
    return;
  }
  if (authForm.password.length < 6) {
    authError.value = '密码至少需要 6 个字符';
    return;
  }

  authLoading.value = true;
  try {
    const payload = isRegister
      ? { email, username, password: authForm.password }
      : { email, password: authForm.password };
    const result = isRegister ? await authApi.register(payload) : await authApi.login(payload);

    setToken(result.token);
    user.value = result.user;
    authForm.password = '';
    await load();
    notify(isRegister ? '注册成功，欢迎加入' : '欢迎回来');
  } catch (error) {
    authError.value = error.message;
  } finally {
    authLoading.value = false;
  }
}

// 加载课表列表
async function load(preferredId = schedule.value?.id) {
  try {
    const list = await schedulesApi.list();
    schedules.value = list;
    const savedId = getActiveScheduleId();
    schedule.value = list.find(item => item.id === Number(preferredId))
      || list.find(item => item.id === savedId)
      || list[0]
      || null;

    if (schedule.value) {
      setActiveScheduleId(schedule.value.id);
    }
    const totalWeeks = scheduleWeekCount(schedule.value);
    currentWeek.value = termWeek(schedule.value?.start_date, totalWeeks);
    week.value = currentWeek.value;
  } catch (error) {
    notify(error.message);
  } finally {
    loading.value = false;
  }
}

// 切换当前课表
function selectSchedule(event) {
  schedule.value = schedules.value.find(item => item.id === Number(event.target.value)) || null;
  if (schedule.value) {
    setActiveScheduleId(schedule.value.id);
  }
  const totalWeeks = scheduleWeekCount(schedule.value);
  currentWeek.value = termWeek(schedule.value?.start_date, totalWeeks);
  week.value = currentWeek.value;
}

// 删除课表
async function deleteSchedule() {
  const current = schedule.value;
  if (!current) return;
  const title = current.term || current.name || '当前课表';
  if (!confirm(`确认删除“${title}”？该课表中的全部课程也会被删除。`)) return;
  try {
    await schedulesApi.delete(current.id);
    setActiveScheduleId(null);
    await load(null);
    notify('课表已删除');
  } catch (error) {
    notify(error.message);
  }
}

function goCurrentWeek() {
  week.value = currentWeek.value;
}

// 课程详情预览与编辑跳转
function openPreview(course) {
  previewCourse.value = course;
  previewOpen.value = true;
}

function editPreview(course) {
  previewOpen.value = false;
  openEditor(course);
}

function openEditor(course) {
  Object.assign(form, emptyCourse(), course || {});
  form.weeks = formatWeeks(course?.weeks) || '1-16';
  editorOpen.value = true;
}

// 保存课程
async function saveCourse() {
  const payload = {
    schedule_id: schedule.value.id,
    name: form.name.trim(),
    teacher: form.teacher.trim(),
    room: form.room.trim(),
    weekday: +form.weekday,
    start_section: +form.start_section,
    end_section: +form.end_section,
    weeks: parseWeeks(form.weeks),
    color: form.color,
  };
  if (payload.end_section < payload.start_section) {
    notify('结束节次不能早于开始节次');
    return;
  }
  try {
    if (form.id) {
      await coursesApi.update(form.id, payload);
    } else {
      await coursesApi.add(payload);
    }
    editorOpen.value = false;
    notify('课程已保存');
    await load();
  } catch (error) {
    notify(error.message);
  }
}

// 删除课程
async function removeCourse() {
  if (!form.id || !confirm('确认删除这门课程？')) return;
  try {
    await coursesApi.delete(form.id);
    editorOpen.value = false;
    notify('课程已删除');
    await load();
  } catch (error) {
    notify(error.message);
  }
}

// 上传与导入向导
function upload(event) {
  const file = event.target.files[0];
  event.target.value = '';
  if (!file) return;
  importerOpen.value = true;
  importing.value = false;
  importSetup.value = true;
  importFile.value = file;
  importError.value = '';
  importEngine.value = '';
  importStartDate.value = schedule.value?.start_date?.slice(0, 10) || '';
  importEndDate.value = schedule.value?.end_date?.slice(0, 10) || defaultEndDate(importStartDate.value);
}

async function startImport() {
  if (!importFile.value) return;
  if (!importStartDate.value || !importEndDate.value) {
    importError.value = '请先填写学期开始日期和结束日期';
    return;
  }
  if (importEndDate.value < importStartDate.value) {
    importError.value = '学期结束日期不能早于开始日期';
    return;
  }
  importSetup.value = false;
  importing.value = true;
  importError.value = '';
  const body = new FormData();
  body.append('file', importFile.value);
  body.append('start_date', importStartDate.value);
  body.append('end_date', importEndDate.value);

  try {
    const result = await importerApi.importFile(body);
    importEngine.value = result.engine || '';
    if (result.imported) {
      importerOpen.value = false;
      await load(result.schedule_id);
      notify(result.replaced ? `已覆盖当前学期，共 ${result.imported} 条课程安排` : `已导入 ${result.imported} 条课程安排`);
    }
  } catch (error) {
    importError.value = error.message;
    notify(error.message);
  } finally {
    importing.value = false;
  }
}

// 日夜模式
const savedBgMode = localStorage.getItem('schedule_bg_mode');
const bgMode = ref(savedBgMode === 'night' ? 'night' : 'transparent');

function toggleNightMode() {
  bgMode.value = bgMode.value === 'night' ? 'transparent' : 'night';
  document.documentElement.setAttribute('data-bg', bgMode.value);
  localStorage.setItem('schedule_bg_mode', bgMode.value);
  notify(bgMode.value === 'night' ? '已开启黑夜模式' : '已关闭黑夜模式');
}

// 生命周期
onMounted(async () => {
  document.documentElement.setAttribute('data-bg', bgMode.value);
  window.addEventListener('auth:expired', logout);
  if (getToken()) {
    try {
      user.value = await authApi.me();
      await load();
    } catch {
      logout();
    }
  } else {
    loading.value = false;
  }
});

onUnmounted(() => {
  window.removeEventListener('auth:expired', logout);
});
</script>

<template>
  <iframe
    class="wallpaper-background"
    src="/wallpaper/index.html"
    title="动态壁纸背景"
    aria-hidden="true"
    tabindex="-1"
  ></iframe>
  <div class="ambient-canvas" aria-hidden="true">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>
  </div>

  <main class="shell" v-if="user">
    <HeaderBar
      :user="user"
      :schedule="schedule"
      :bg-mode="bgMode"
      @delete-schedule="deleteSchedule"
      @add-course="openEditor()"
      @upload="upload"
      @logout="logout"
      @toggle-night-mode="toggleNightMode"
    />

    <ScheduleToolbar
      :schedules="schedules"
      :schedule="schedule"
      :week="week"
      :current-week="currentWeek"
      :week-options="weekOptions"
      @update:week="week = $event"
      @select-schedule="selectSchedule"
      @go-current-week="goCurrentWeek"
    />

    <ScheduleGrid
      :schedule="schedule"
      :week="week"
      :loading="loading"
      :color-map="courseColorMap"
      @preview-course="openPreview"
    />
  </main>

  <!-- 登录 / 注册模态弹窗 -->
  <AuthModal
    :open="!user"
    :auth-mode="authMode"
    :auth-form="authForm"
    :auth-error="authError"
    :auth-loading="authLoading"
    @submit="submitAuth"
    @update:auth-mode="authMode = $event"
    @clear-error="authError = ''"
  />

  <!-- 课程预览模态弹窗 -->
  <CoursePreviewModal
    :open="previewOpen"
    :course="previewCourse"
    :color-map="courseColorMap"
    @close="previewOpen = false"
    @edit="editPreview"
  />

  <!-- 课程编辑 / 新建模态弹窗 -->
  <CourseEditorModal
    :open="editorOpen"
    :form="form"
    @close="editorOpen = false"
    @save="saveCourse"
    @delete="removeCourse"
  />

  <!-- 课表导入向导模态弹窗 -->
  <ImporterModal
    :open="importerOpen"
    :importing="importing"
    :import-setup="importSetup"
    :import-file="importFile"
    :import-start-date="importStartDate"
    :import-end-date="importEndDate"
    :import-error="importError"
    :import-engine="importEngine"
    @close="importerOpen = false"
    @update:import-start-date="importStartDate = $event"
    @update:import-end-date="importEndDate = $event"
    @start-import="startImport"
  />

  <Transition name="toast">
    <div v-if="message" class="toast">{{ message }}</div>
  </Transition>
</template>

<style>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.term-select-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 8px rgba(50, 75, 110, 0.06), inset 0 1px 0.5px #fff;
  padding: 3px 12px;
  max-width: 100%;
}

.term-select-wrap select {
  max-width: min(360px, 60vw);
  padding: 2px 24px 2px 0;
  border: 0;
  outline: 0;
  appearance: none;
  background: transparent;
  color: #0f172a;
  font: inherit;
  font-size: 1.15rem;
  font-weight: 700;
  cursor: pointer;
}

.term-select-wrap select option {
  color: #0f172a;
  background: #ffffff;
}

.term-select-wrap i {
  position: absolute;
  right: 10px;
  top: 50%;
  color: #475569;
  font-style: normal;
  pointer-events: none;
  transform: translateY(-55%);
  font-weight: bold;
}

html[data-bg="night"] .term-select-wrap {
  background: rgba(15, 23, 42, 0.65);
  border-color: rgba(148, 163, 184, 0.32);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3), inset 0 1px 0.5px rgba(255, 255, 255, 0.15);
}

html[data-bg="night"] .term-select-wrap select {
  color: #f8fafc;
}

html[data-bg="night"] .term-select-wrap select option {
  color: #f8fafc;
  background: #0f172a;
}

html[data-bg="night"] .term-select-wrap i {
  color: #94a3b8;
}

.week-menu {
  position: relative;
  flex: 0 1 164px;
  min-width: 0;
  z-index: 15;
}

.week-trigger {
  width: 100%;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 14px;
  border: 1px solid rgba(255, 255, 255, 0.75);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #172033;
  cursor: pointer;
  text-align: left;
  box-shadow: 0 2px 8px rgba(50, 75, 110, 0.06), inset 0 1px 0.5px #fff;
  transition: all 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.week-trigger:hover {
  background: rgba(255, 255, 255, 0.82);
  transform: translateY(-1px);
}

.week-trigger span {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.week-trigger b {
  font-size: 0.88rem;
  line-height: 1.2;
  white-space: nowrap;
}

.week-trigger small {
  margin-top: 2px;
  color: #64748b;
  font-size: 0.66rem;
  line-height: 1.1;
  white-space: nowrap;
}

.week-trigger i {
  font-style: normal;
  color: #64748b;
  font-size: 1.1rem;
  line-height: 1;
  transition: transform 0.22s ease;
}

.week-trigger i.open {
  transform: rotate(180deg);
}

.week-menu-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: min(460px, calc(100vw - 40px));
  padding: 16px;
  border-radius: 22px;
  animation: menu-spring 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 30;
}

@keyframes menu-spring {
  from { opacity: 0; transform: scale(0.94) translateY(-8px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

.week-menu-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  color: #0f172a;
  font-size: 0.88rem;
}

.week-menu-head button {
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 10px;
  padding: 6px 12px;
  background: rgba(56, 189, 248, 0.12);
  color: #0284c7;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.week-menu-head button:hover {
  background: rgba(56, 189, 248, 0.22);
}

.week-menu-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  max-height: min(62vh, 430px);
  overflow: auto;
  padding: 2px;
}

.week-option {
  min-width: 0;
  min-height: 68px;
  padding: 8px 6px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: #1e293b;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(50, 75, 110, 0.05), inset 0 1px 0.5px #fff;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.week-option:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 14px rgba(50, 75, 110, 0.12), inset 0 1px 0.5px #fff;
}

.week-option b, .week-option small {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.week-option b {
  font-size: 0.84rem;
  line-height: 1.3;
}

.week-option small {
  margin-top: 4px;
  color: #64748b;
  font-size: 0.66rem;
}

.week-option.selected {
  border-color: rgba(56, 189, 248, 0.7);
  background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(14, 165, 233, 0.32), inset 0 1.5px 0.5px rgba(255, 255, 255, 0.85);
}

.week-option.selected small {
  color: rgba(255, 255, 255, 0.9);
}

.reset-week {
  border: 1px solid rgba(255, 255, 255, 0.75)!important;
  min-width: 76px!important;
  height: 42px;
  font-size: 0.8rem!important;
  color: #475569!important;
  border-radius: 14px!important;
  background: rgba(255, 255, 255, 0.52)!important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 2px 8px rgba(50, 75, 110, 0.06), inset 0 1px 0.5px #fff;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.reset-week:hover {
  background: rgba(255, 255, 255, 0.85)!important;
  transform: translateY(-1px);
}

.reset-week.active {
  background: linear-gradient(135deg, #1e293b, #0f172a)!important;
  color: #fff!important;
  border-color: rgba(255, 255, 255, 0.15)!important;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2), inset 0 1px 0.5px rgba(255, 255, 255, 0.3);
}


.preview-modal {
  width: min(440px, 100%);
}

.preview-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 18px 0 20px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.55);
}

.preview-details > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.88rem;
}

.preview-details span {
  color: #64748b;
  flex-shrink: 0;
}

.preview-details b {
  color: #0f172a;
  text-align: right;
  word-break: break-word;
}

.color-preview {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.color-preview i {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.8), 0 2px 4px rgba(0, 0, 0, 0.15);
}

.import-setup {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 14px;
}

.import-file {
  margin: 0;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.45);
  color: #0f172a;
  font-size: 0.86rem;
  font-weight: 600;
  word-break: break-all;
}

.import-inline-error {
  margin: 0;
  color: #e11d48;
  font-size: 0.8rem;
}

.import-help {
  margin: 0;
  color: #64748b;
  font-size: 0.78rem;
  line-height: 1.5;
}

.auth-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 18px;
}

.auth-card {
  width: min(400px, 100%);
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  color: #0f172a;
  font-size: 1.05rem;
}

.auth-head h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.auth-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 0.85rem;
}

.auth-form label {
  display: block;
  margin: 16px 0 0;
  color: #475569;
  font-size: 0.82rem;
  font-weight: 500;
}

.auth-error {
  margin: 14px 0 0;
  color: #e11d48;
  font-size: 0.8rem;
}

.auth-submit {
  width: 100%;
  margin-top: 20px;
  padding: 13px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border-color: rgba(255, 255, 255, 0.15);
}

.auth-submit:hover {
  background: linear-gradient(135deg, #334155, #1e293b);
  color: #ffffff;
}

.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.auth-switch {
  margin: 18px 0 0;
  text-align: center;
  color: #64748b;
  font-size: 0.84rem;
}

.auth-switch button {
  border: 0;
  background: none;
  padding: 0 2px;
  color: #0284c7;
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
}

.auth-switch button:hover {
  text-decoration: underline;
}

.user-badge {
  display: flex;
  align-items: center;
  max-width: 120px;
  height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.2);
  color: #334155;
  font-size: 0.85rem;
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.header-action.logout {
  padding: 12px 18px;
}

html[data-bg="night"] .week-trigger {
  background: rgba(15, 23, 42, 0.55);
  border-color: rgba(148, 163, 184, 0.28);
  color: #f8fafc;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3), inset 0 1px 0.5px rgba(255, 255, 255, 0.15);
}

html[data-bg="night"] .week-trigger:hover {
  background: rgba(30, 41, 59, 0.72);
}

html[data-bg="night"] .week-trigger small,
html[data-bg="night"] .week-trigger i {
  color: #94a3b8;
}

html[data-bg="night"] .week-menu-head b,
html[data-bg="night"] .preview-details b,
html[data-bg="night"] .import-file,
html[data-bg="night"] .auth-brand,
html[data-bg="night"] .auth-head h2 {
  color: #f8fafc;
}

html[data-bg="night"] .week-option {
  background: rgba(15, 23, 42, 0.45);
  border-color: rgba(148, 163, 184, 0.22);
  color: #f1f5f9;
}

html[data-bg="night"] .week-option:hover {
  background: rgba(30, 41, 59, 0.7);
}

html[data-bg="night"] .week-option.selected {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.16);
  color: #38bdf8;
}

html[data-bg="night"] .preview-details,
html[data-bg="night"] .import-file {
  background: rgba(15, 23, 42, 0.42);
  border-color: rgba(148, 163, 184, 0.2);
}

html[data-bg="night"] .user-badge {
  color: #f1f5f9;
  background: rgba(15, 23, 42, 0.32);
  border-color: rgba(148, 163, 184, 0.25);
}

@media (max-width: 680px) {
  .term-picker {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 8px;
  }
  .term-picker p {
    margin: 0;
    font-size: 0.76rem;
    color: #94a3b8;
    white-space: nowrap;
  }
  .term-select-wrap {
    padding: 2px 8px;
    max-width: calc(100vw - 110px);
  }
  .term-select-wrap select {
    max-width: calc(100vw - 136px);
    font-size: 0.95rem;
    padding: 2px 20px 2px 0;
  }
  .week-picker {
    width: 100%;
    gap: 5px;
    justify-content: space-between;
  }
  .week-menu {
    flex: 1;
    min-width: 0;
  }
  .week-trigger {
    height: 38px;
    padding: 4px 8px;
    border-radius: 12px;
  }
  .week-trigger b {
    font-size: 0.82rem;
  }
  .week-trigger small {
    font-size: 0.62rem;
  }
  .week-menu-panel {
    right: auto;
    left: 0;
    width: min(340px, calc(100vw - 24px));
    padding: 12px;
  }
  .week-menu-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }
  .week-option {
    min-height: 52px;
    padding: 6px 4px;
    border-radius: 10px;
  }
  .week-option b {
    font-size: 0.78rem;
  }
  .week-option small {
    font-size: 0.58rem;
  }
  .reset-week {
    height: 38px;
    min-width: 56px !important;
    padding: 0 6px !important;
    font-size: 0.78rem;
    border-radius: 12px;
  }
  .week-nav {
    height: 38px;
    width: 34px;
    flex: 0 0 34px;
    border-radius: 12px;
  }
}
</style>
