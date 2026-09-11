<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import {
  adjustmentsApi,
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
  findCurrentSchedule,
  formatWeeks,
  isScheduleActiveToday,
  parseWeeks,
  scheduleWeekCount,
  suggestSemesterDates,
  termWeek,
} from './utils/schedule.js';

import HeaderBar from './components/HeaderBar.vue';
import ScheduleToolbar from './components/ScheduleToolbar.vue';
import ScheduleGrid from './components/ScheduleGrid.vue';
import CoursePreviewModal from './components/CoursePreviewModal.vue';
import CourseEditorModal from './components/CourseEditorModal.vue';
import CourseAdjustmentModal from './components/CourseAdjustmentModal.vue';
import AdjustmentImportModal from './components/AdjustmentImportModal.vue';
import CourseMoveModal from './components/CourseMoveModal.vue';
import AdjustmentCenterModal from './components/AdjustmentCenterModal.vue';
import ImporterModal from './components/ImporterModal.vue';
import SemesterModal from './components/SemesterModal.vue';
import AuthModal from './components/AuthModal.vue';
import UpdateModal from './components/UpdateModal.vue';
import SplashScreen from './components/SplashScreen.vue';
import {
  CURRENT_VERSION_NAME,
  checkAppUpdate,
  ignoreUpdateVersion,
  isNativePlatform,
  openDownloadUrl,
} from './utils/version.js';

// 检测运行环境：Android 原生 App vs 网页浏览器
const isNative = ref(isNativePlatform());

// 开屏状态（仅 Android 原生 App 启动时展示，网页端直接进入）
const showSplash = ref(isNative.value);

// 基础状态
const week = ref(1);
const currentWeek = ref(1);
const schedules = ref([]);
const schedule = ref(null);
const loading = ref(true);
const message = ref('');

// 应用更新状态
const updateModalOpen = ref(false);
const updateInfo = ref({});

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
const adjustmentOpen = ref(false);
const adjustmentCourse = ref(null);
const adjustmentForm = reactive({ weekday: 1, start_section: 1, end_section: 2, room: '' });
const adjustmentImportOpen = ref(false);
const adjustmentImportLoading = ref(false);
const adjustmentImportApplying = ref(false);
const adjustmentImportFilename = ref('');
const adjustmentImportError = ref('');
const adjustmentImportItems = ref([]);
const moveModalOpen = ref(false);
const pendingMove = ref(null);
const moveSaving = ref(false);
const adjustmentCenterOpen = ref(false);
const changeLogs = ref([]);
const changeLogsLoading = ref(false);

const previewCourseLogs = computed(() => {
  if (!previewCourse.value?.id) return [];
  const cid = previewCourse.value.id;
  return changeLogs.value.filter(log => {
    if (log.course_id === cid) return true;
    if (Array.isArray(log.details) && log.details.some(d => d.course_id === cid)) return true;
    return false;
  });
});

const importerOpen = ref(false);
const importing = ref(false);
const importSetup = ref(false);
const importFile = ref(null);
const importError = ref('');
const importEngine = ref('');
const importStartDate = ref('');
const importEndDate = ref('');
const importElapsed = ref(0);
let importTimer = null;

const semesterModalOpen = ref(false);
const semesterSaving = ref(false);

// 计算属性
const weekOptions = computed(() =>
  Array.from({ length: scheduleWeekCount(schedule.value) }, (_, index) => index + 1)
);

const courseColorMap = computed(() => buildCourseColorMap(schedule.value?.courses));

async function loadChangeLogs() {
  if (!schedule.value?.id) {
    changeLogs.value = [];
    return;
  }
  changeLogsLoading.value = true;
  try {
    changeLogs.value = await adjustmentsApi.getRecords(schedule.value.id);
  } catch (error) {
    console.error('Failed to load change logs:', error);
  } finally {
    changeLogsLoading.value = false;
  }
}

watch(() => schedule.value?.id, newId => {
  if (newId) loadChangeLogs();
});

watch(adjustmentCenterOpen, val => {
  if (val && schedule.value?.id) {
    loadChangeLogs();
  }
});

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
async function load(preferredId = null) {
  try {
    const list = await schedulesApi.list();
    schedules.value = list;

    if (!list.length) {
      schedule.value = null;
      return;
    }

    let selected = null;
    if (preferredId) {
      selected = list.find(item => item.id === Number(preferredId));
    }

    if (!selected) {
      const activeSchedule = findCurrentSchedule(list);
      const savedId = getActiveScheduleId();
      const savedSchedule = list.find(item => item.id === savedId);

      // 若用户曾主动选择过某个学期（无论是否包含今天），优先保持用户的选择
      if (savedSchedule) {
        selected = savedSchedule;
      } else {
        selected = activeSchedule || list[0];
      }
    }

    schedule.value = selected || list[0] || null;

    if (schedule.value) {
      setActiveScheduleId(schedule.value.id);
    }
    const totalWeeks = scheduleWeekCount(schedule.value);
    currentWeek.value = termWeek(schedule.value?.start_date, totalWeeks, schedule.value);
    week.value = currentWeek.value;
  } catch (error) {
    notify(error.message);
  } finally {
    loading.value = false;
  }
}

// 切换当前课表
function selectSchedule(payload) {
  const targetId = typeof payload === 'object' && payload?.target ? Number(payload.target.value) : Number(payload);
  const found = schedules.value.find(item => item.id === targetId);
  if (!found) return;
  schedule.value = found;
  setActiveScheduleId(found.id);
  const totalWeeks = scheduleWeekCount(found);
  currentWeek.value = termWeek(found.start_date, totalWeeks, found);
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
    semesterModalOpen.value = false;
    await load(null);
    notify('课表已删除');
  } catch (error) {
    notify(error.message);
  }
}

// 学期设置
function openSemesterSettings() {
  semesterModalOpen.value = true;
}

async function saveSemesterSettings(payload) {
  if (!schedule.value) return;
  semesterSaving.value = true;
  try {
    const updated = await schedulesApi.update(schedule.value.id, payload);
    semesterModalOpen.value = false;
    notify('学期设置已保存');
    await load(updated.id);
  } catch (error) {
    notify(error.message);
  } finally {
    semesterSaving.value = false;
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

function openAdjustment(course) {
  previewOpen.value = false;
  adjustmentCourse.value = course;
  Object.assign(adjustmentForm, {
    weekday: course.weekday,
    start_section: course.start_section,
    end_section: course.end_section,
    room: course.room || '',
  });
  adjustmentOpen.value = true;
}

async function saveAdjustment() {
  const payload = {
    week: week.value,
    weekday: +adjustmentForm.weekday,
    start_section: +adjustmentForm.start_section,
    end_section: +adjustmentForm.end_section,
    room: adjustmentForm.room.trim(),
  };
  if (payload.end_section < payload.start_section) {
    notify('结束节次不能早于开始节次');
    return;
  }
  try {
    await coursesApi.adjust(adjustmentCourse.value.id, week.value, payload);
    adjustmentOpen.value = false;
    notify(`第 ${week.value} 周调课已保存`);
    await load(schedule.value.id);
  } catch (error) {
    notify(error.message);
  }
}

async function cancelAdjustment() {
  if (!confirm(`确认撤销第 ${week.value} 周的调课？`)) return;
  try {
    await coursesApi.cancelAdjustment(adjustmentCourse.value.id, week.value);
    adjustmentOpen.value = false;
    notify('调课已撤销');
    await load(schedule.value.id);
  } catch (error) {
    notify(error.message);
  }
}

async function uploadAdjustmentNotice(file) {
  if (!file || !schedule.value) return;
  adjustmentCenterOpen.value = false;
  adjustmentImportOpen.value = true;
  adjustmentImportLoading.value = true;
  adjustmentImportFilename.value = file.name;
  adjustmentImportError.value = '';
  adjustmentImportItems.value = [];
  try {
    const result = await adjustmentsApi.parse(file, schedule.value.id);
    adjustmentImportItems.value = result.items;
    if (!result.matched) adjustmentImportError.value = '识别成功，但没有记录能与当前课表可靠匹配';
  } catch (error) {
    adjustmentImportError.value = error.message;
  } finally {
    adjustmentImportLoading.value = false;
  }
}

async function revokeAdjustmentRecord(record) {
  const courseName = record.course_name || '课程';
  if (!confirm(`确认撤销“${courseName}”第 ${record.week} 周的调课？`)) return;
  try {
    await coursesApi.cancelAdjustment(record.course_id, record.week);
    notify('调课记录已撤销');
    await load(schedule.value.id);
    await loadChangeLogs();
    if (previewCourse.value && previewCourse.value.id === record.course_id) {
      const refreshed = (schedule.value?.courses || []).find(c => c.id === record.course_id);
      if (refreshed) previewCourse.value = refreshed;
    }
  } catch (error) {
    notify(error.message);
  }
}

async function applyAdjustmentNotice() {
  const selected = adjustmentImportItems.value.filter(item => item.status === 'matched' && item.selected);
  if (!selected.length) return;
  adjustmentImportApplying.value = true;
  try {
    const items = selected.map(item => ({
      course_id: item.course_id,
      week: item.week,
      weekday: item.new_weekday,
      start_section: item.new_start_section,
      end_section: item.new_end_section,
      room: item.new_room,
    }));
    const result = await adjustmentsApi.apply(schedule.value.id, items);
    adjustmentImportOpen.value = false;
    notify(`已应用 ${result.applied} 条调课`);
    await load(schedule.value.id);
    await loadChangeLogs();
  } catch (error) {
    adjustmentImportError.value = error.message;
  } finally {
    adjustmentImportApplying.value = false;
  }
}

function requestCourseMove(move) {
  pendingMove.value = move;
  moveModalOpen.value = true;
}

async function saveCourseMove(scope) {
  const move = pendingMove.value;
  if (!move) return;
  moveSaving.value = true;
  try {
    const orig = move.course.original_course || move.course;
    if (scope === 'week') {
      // If moved back to original unadjusted position, cancel adjustment instead of creating redundant adjustment
      if (orig.weekday === move.weekday
          && orig.start_section === move.start_section
          && orig.end_section === move.end_section
          && (orig.room || '') === (move.course.room || '')) {
        if (move.course.adjusted_week) {
          await coursesApi.cancelAdjustment(move.course.id, week.value);
          notify(`已移回第 ${week.value} 周原位置，自动清除“调”字`);
          moveModalOpen.value = false;
          await load(schedule.value.id);
          await loadChangeLogs();
          return;
        }
      }
      await coursesApi.adjust(move.course.id, week.value, {
        week: week.value,
        weekday: move.weekday,
        start_section: move.start_section,
        end_section: move.end_section,
        room: move.course.room || '',
      });
    } else {
      const base = move.course.original_course || move.course;
      await coursesApi.update(base.id, {
        schedule_id: schedule.value.id,
        name: base.name,
        teacher: base.teacher || '',
        room: base.room || '',
        weekday: move.weekday,
        start_section: move.start_section,
        end_section: move.end_section,
        weeks: base.weeks || [],
        color: base.color,
      }, 'drag');
      if (move.course.adjusted_week) {
        try {
          await coursesApi.cancelAdjustment(base.id, move.course.adjusted_week);
        } catch (_) {}
      }
    }
    moveModalOpen.value = false;
    notify(scope === 'week' ? `第 ${week.value} 周课程已调整` : '整学期课程时间已修改');
    await load(schedule.value.id);
    await loadChangeLogs();
  } catch (error) {
    notify(error.message);
  } finally {
    moveSaving.value = false;
  }
}

const editingAdjustedWeek = ref(null);

function openEditor(course) {
  editingAdjustedWeek.value = course?.adjusted_week || null;
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
      await coursesApi.update(form.id, payload, 'manual');
      if (editingAdjustedWeek.value) {
        try {
          await coursesApi.cancelAdjustment(form.id, editingAdjustedWeek.value);
        } catch (_) {}
        editingAdjustedWeek.value = null;
      }
    } else {
      await coursesApi.add(payload);
    }
    editorOpen.value = false;
    notify('课程已保存');
    await load();
    await loadChangeLogs();
  } catch (error) {
    notify(error.message);
  }
}

async function deleteChangeLog(record) {
  if (!confirm(`确认删除此条变更记录？`)) return;
  try {
    await adjustmentsApi.deleteRecord(record.id);
    notify('记录已删除');
    await loadChangeLogs();
  } catch (error) {
    notify(error.message);
  }
}

async function removeCourseAdjustment(course) {
  if (!course?.adjusted_week) return;
  if (!confirm(`确认清除《${course.name}》第 ${course.adjusted_week} 周的调课标记，恢复原排课？`)) return;
  try {
    await coursesApi.cancelAdjustment(course.id, course.adjusted_week);
    notify('已清除“调”字标记，恢复原时间');
    await load(schedule.value.id);
    await loadChangeLogs();
    if (previewCourse.value && previewCourse.value.id === course.id) {
      const refreshed = (schedule.value?.courses || []).find(c => c.id === course.id);
      if (refreshed) previewCourse.value = refreshed;
    }
  } catch (error) {
    notify(error.message);
  }
}

async function restoreCourseRecord(record) {
  if (!record.course_id) return;
  const course = (schedule.value?.courses || []).find(c => c.id === record.course_id);
  if (!course) {
    notify('原课程已不存在');
    return;
  }
  const timeDiff = Array.isArray(record.details) ? record.details.find(d => d.field === 'time') : null;
  const roomDiff = Array.isArray(record.details) ? record.details.find(d => d.field === 'room') : null;
  if (!timeDiff && !roomDiff) {
    notify('未找到可恢复的变更项');
    return;
  }
  if (!confirm(`确认撤销改动，将《${course.name}》直接回滚至此记录修改前的状态？`)) return;
  try {
    const orig = course.original_course || course;
    const targetWeekday = timeDiff?.old_weekday ? timeDiff.old_weekday : orig.weekday;
    const targetStart = timeDiff?.old_start_section ? timeDiff.old_start_section : orig.start_section;
    const targetEnd = timeDiff?.old_end_section ? timeDiff.old_end_section : orig.end_section;
    const targetRoom = roomDiff && roomDiff.old !== '未设置' ? roomDiff.old : (course.room || orig.room || '');

    const recordWeek = record.week || (Array.isArray(record.details) ? record.details[0]?.week : null);

    // If single-week move or adjustment
    if (record.action_type === 'drag_move' || (record.action_type === 'manual_edit' && recordWeek)) {
      const w = recordWeek || week.value;
      // If target matches original unadjusted course, cancel adjustment completely
      if (targetWeekday === orig.weekday && targetStart === orig.start_section && targetEnd === orig.end_section && targetRoom === (orig.room || '')) {
        await coursesApi.cancelAdjustment(course.id, w);
      } else {
        await coursesApi.adjust(course.id, w, {
          week: w,
          weekday: targetWeekday,
          start_section: targetStart,
          end_section: targetEnd,
          room: targetRoom,
        });
      }
    } else {
      // All-weeks course update
      const payload = {
        schedule_id: schedule.value.id,
        name: course.name,
        teacher: course.teacher || '',
        room: targetRoom,
        weekday: targetWeekday,
        start_section: targetStart,
        end_section: targetEnd,
        weeks: orig.weeks || course.weeks || [],
        color: course.color,
      };
      await coursesApi.update(course.id, payload, 'manual');
    }

    // Clean up this record and all subsequent records for this course (chain rollback)
    const subsequentLogs = (changeLogs.value || []).filter(l => {
      const cid = l.course_id || (Array.isArray(l.details) ? l.details[0]?.course_id : null);
      return cid === course.id && l.id >= record.id;
    });
    for (const sub of subsequentLogs) {
      try {
        await adjustmentsApi.deleteRecord(sub.id);
      } catch (_) {}
    }

    notify('已成功撤销并回滚至该次修改前的状态');
    await load(schedule.value.id);
    await loadChangeLogs();
    if (previewCourse.value && previewCourse.value.id === course.id) {
      const refreshed = (schedule.value?.courses || []).find(c => c.id === course.id);
      if (refreshed) previewCourse.value = refreshed;
    }
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
    await loadChangeLogs();
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

  // 智能推测学期日期：优先看文件名是否含有学年学期标识（如 2025-2026-1 等）
  const suggestedFromName = suggestSemesterDates(file.name);
  if (suggestedFromName) {
    importStartDate.value = suggestedFromName.start;
    importEndDate.value = suggestedFromName.end;
  } else if (schedule.value && isScheduleActiveToday(schedule.value)) {
    importStartDate.value = schedule.value.start_date?.slice(0, 10) || '';
    importEndDate.value = schedule.value.end_date?.slice(0, 10) || defaultEndDate(importStartDate.value);
  } else {
    const currentYear = new Date().getFullYear();
    const currentSuggested = suggestSemesterDates(`${currentYear}-${currentYear + 1}-1`);
    importStartDate.value = currentSuggested?.start || '';
    importEndDate.value = currentSuggested?.end || defaultEndDate(importStartDate.value);
  }
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
  importElapsed.value = 0;
  window.clearInterval(importTimer);
  importTimer = window.setInterval(() => { importElapsed.value += 1; }, 1000);
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
    window.clearInterval(importTimer);
    importTimer = null;
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

// 应用更新控制（仅在 Android 原生 App 内弹窗推送）
async function handleCheckUpdate(silent = false) {
  if (!isNative.value) {
    if (!silent) {
      notify('网页端已连接云端实时更新，刷新页面即可获取最新内容');
    }
    return;
  }
  try {
    const result = await checkAppUpdate(silent);
    if (result.hasUpdate) {
      updateInfo.value = result.updateInfo;
      updateModalOpen.value = true;
    } else if (!silent) {
      notify(`当前已是最新版本 (v${CURRENT_VERSION_NAME})`);
    }
  } catch (error) {
    if (!silent) {
      notify(error.message || '检查更新失败，请稍后重试');
    }
  }
}

function onConfirmUpdate(url) {
  const target = typeof url === 'string' && url ? url : updateInfo.value?.downloadUrl;
  if (target) {
    openDownloadUrl(target);
  }
}

function onIgnoreUpdate() {
  if (updateInfo.value?.versionCode) {
    ignoreUpdateVersion(updateInfo.value.versionCode);
  }
  updateModalOpen.value = false;
}

// 生命周期
onMounted(async () => {
  document.documentElement.setAttribute('data-bg', bgMode.value);
  window.addEventListener('auth:expired', logout);
  if (isNative.value) {
    handleCheckUpdate(true);
  }
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
  window.clearInterval(importTimer);
});
</script>

<template>
  <!-- 开屏封面（仅在 Android 原生 App 启动时展示，轻触或1秒后平滑进入） -->
  <Transition name="splash-fade">
    <SplashScreen v-if="isNative && showSplash" :duration="1.0" @finish="showSplash = false" />
  </Transition>

  <video
    class="video-wallpaper"
    src="/wallpaper.mp4"
    poster="/wallpaper-fallback.jpg"
    autoplay
    muted
    loop
    playsinline
    preload="metadata"
    aria-hidden="true"
  ></video>
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
      :app-version="CURRENT_VERSION_NAME"
      :is-native="isNative"
      @delete-schedule="deleteSchedule"
      @add-course="openEditor()"
      @upload="upload"
      @open-adjustments="adjustmentCenterOpen = true"
      @logout="logout"
      @toggle-night-mode="toggleNightMode"
      @check-update="handleCheckUpdate(false)"
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
      @open-semester-settings="openSemesterSettings"
    />

    <ScheduleGrid
      :key="schedule?.id"
      :schedule="schedule"
      :week="week"
      :loading="loading"
      :color-map="courseColorMap"
      @preview-course="openPreview"
      @move-course="requestCourseMove"
      @move-conflict="notify('目标时段存在课程，不能移动到这里')"
    />
  </main>

  <!-- 登录 / 注册模态弹窗 -->
  <AuthModal
    :open="!user"
    :auth-mode="authMode"
    :auth-form="authForm"
    :auth-error="authError"
    :auth-loading="authLoading"
    :app-version="CURRENT_VERSION_NAME"
    :is-native="isNative"
    @submit="submitAuth"
    @update:auth-mode="authMode = $event"
    @clear-error="authError = ''"
    @check-update="handleCheckUpdate(false)"
  />

  <!-- 课程预览模态弹窗 -->
  <CoursePreviewModal
    :open="previewOpen"
    :course="previewCourse"
    :color-map="courseColorMap"
    :records="previewCourseLogs"
    @close="previewOpen = false"
    @edit="editPreview"
    @adjust="openAdjustment"
    @restore="restoreCourseRecord"
    @revoke="revokeAdjustmentRecord"
    @delete="deleteChangeLog"
    @remove-adjustment="removeCourseAdjustment"
  />

  <!-- 课程编辑 / 新建模态弹窗 -->
  <CourseEditorModal
    :open="editorOpen"
    :form="form"
    @close="editorOpen = false"
    @save="saveCourse"
    @delete="removeCourse"
  />

  <CourseAdjustmentModal
    :open="adjustmentOpen"
    :course="adjustmentCourse"
    :week="week"
    :form="adjustmentForm"
    :existing="Boolean(adjustmentCourse?.adjusted_week)"
    @close="adjustmentOpen = false"
    @save="saveAdjustment"
    @cancel-adjustment="cancelAdjustment"
  />

  <AdjustmentImportModal
    :open="adjustmentImportOpen"
    :loading="adjustmentImportLoading"
    :applying="adjustmentImportApplying"
    :filename="adjustmentImportFilename"
    :error="adjustmentImportError"
    :items="adjustmentImportItems"
    @close="adjustmentImportOpen = false"
    @apply="applyAdjustmentNotice"
  />

  <AdjustmentCenterModal
    :open="adjustmentCenterOpen"
    :records="changeLogs"
    :loading="changeLogsLoading"
    @close="adjustmentCenterOpen = false"
    @image="uploadAdjustmentNotice"
    @revoke="revokeAdjustmentRecord"
    @restore="restoreCourseRecord"
    @delete="deleteChangeLog"
  />

  <CourseMoveModal
    :open="moveModalOpen"
    :move="pendingMove"
    :week="week"
    :saving="moveSaving"
    @close="moveModalOpen = false"
    @save-week="saveCourseMove('week')"
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
    :import-elapsed="importElapsed"
    @close="importerOpen = false"
    @update:import-start-date="importStartDate = $event"
    @update:import-end-date="importEndDate = $event"
    @start-import="startImport"
  />

  <!-- 学期与开学日期设置模态弹窗 -->
  <SemesterModal
    :open="semesterModalOpen"
    :schedule="schedule"
    :saving="semesterSaving"
    @close="semesterModalOpen = false"
    @save="saveSemesterSettings"
    @delete="deleteSchedule"
  />

  <!-- 版本升级提示模态弹窗（仅在 Android 原生 App 内展示推送） -->
  <UpdateModal
    v-if="isNative"
    :open="updateModalOpen"
    :update-info="updateInfo"
    :current-version="CURRENT_VERSION_NAME"
    @close="updateModalOpen = false"
    @ignore="onIgnoreUpdate"
    @confirm="onConfirmUpdate"
  />

  <Transition name="toast">
    <div v-if="message" class="toast" role="status" aria-live="polite">{{ message }}</div>
  </Transition>
</template>

<style>
.splash-fade-leave-active {
  transition: opacity 0.45s cubic-bezier(0.4, 0, 0.2, 1), transform 0.45s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}
.splash-fade-leave-to {
  opacity: 0;
  transform: scale(1.06);
}

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
  border-radius: 30em;
  color: #172033;
  cursor: pointer;
  text-align: left;
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
  min-width: 76px;
  height: 42px;
  font-size: 0.84rem;
  font-weight: 600;
  color: #1e293b;
  border-radius: 30em;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.reset-week.active {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.35) 0%, rgba(129, 140, 248, 0.35) 100%) !important;
  color: #0369a1 !important;
  border-color: rgba(56, 189, 248, 0.6) !important;
  box-shadow: 0 6px 16px -2px rgba(14, 165, 233, 0.25), inset 0 1.5px 0.5px #fff !important;
}

html[data-bg="night"] .reset-week.active {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(129, 140, 248, 0.25) 100%) !important;
  color: #f8fafc !important;
  border-color: rgba(56, 189, 248, 0.5) !important;
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

.header-action.logout {
  padding: 12px 18px;
}

html[data-bg="night"] .week-trigger {
  color: #f8fafc;
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
    gap: 6px;
    box-sizing: border-box;
    min-width: 0;
  }
  .term-picker p {
    margin: 0;
    font-size: 0.72rem;
    color: #94a3b8;
    white-space: nowrap;
  }
  .term-select-wrap {
    padding: 2px 6px;
    max-width: calc(100vw - 90px);
    border-radius: 8px;
  }
  .term-select-wrap select {
    max-width: calc(100vw - 110px);
    font-size: 0.86rem;
    padding: 2px 16px 2px 2px;
  }
  .week-picker {
    width: 100%;
    gap: 3px;
    justify-content: space-between;
    box-sizing: border-box;
    min-width: 0;
  }
  .week-menu {
    flex: 1;
    min-width: 0;
    position: relative;
  }
  .week-trigger {
    height: 28px;
    padding: 2px 6px;
    border-radius: 20px;
    gap: 4px;
    box-sizing: border-box;
    width: 100%;
  }
  .week-trigger b {
    font-size: 0.74rem;
    line-height: 1.15;
  }
  .week-trigger small {
    font-size: 0.55rem;
    line-height: 1.1;
    letter-spacing: -0.2px;
  }
  .week-trigger i {
    font-size: 0.82rem;
  }
  /* 周次选择面板向左偏移，与工具栏左侧对齐，消除右侧溢出 */
  .week-menu-panel {
    right: auto;
    left: -29px;
    width: min(316px, calc(100vw - 20px));
    max-width: calc(100vw - 20px);
    padding: 10px;
    border-radius: 16px;
    box-sizing: border-box;
  }
  .week-menu-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
  }
  .week-option {
    min-height: 42px;
    padding: 3px 2px;
    border-radius: 12px;
  }
  .week-option b {
    font-size: 0.72rem;
  }
  .week-option small {
    font-size: 0.52rem;
  }
  .reset-week {
    height: 28px;
    min-width: auto;
    padding: 0 7px;
    font-size: 0.70rem;
    border-radius: 20px;
    flex-shrink: 0;
    white-space: nowrap;
  }
  .week-nav {
    height: 28px;
    width: 26px;
    flex: 0 0 26px;
    border-radius: 20px;
    font-size: 0.88rem;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

@media (max-width: 360px) {
  .week-menu-panel {
    left: -28px;
    width: calc(100vw - 16px);
    max-width: calc(100vw - 16px);
    padding: 8px;
  }
  .reset-week {
    padding: 0 5px;
    font-size: 0.66rem;
    letter-spacing: -0.2px;
  }
}

.splash-fade-leave-active {
  transition: opacity 0.4s cubic-bezier(0.25, 1, 0.5, 1), transform 0.4s cubic-bezier(0.25, 1, 0.5, 1);
}
.splash-fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}
</style>
