/**
 * 课表业务计算与格式化工具函数。
 */

export const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

// 默认 1~12 节作息时间表
export const defaultSectionTimes = [
  ['08:20', '09:05'], ['09:15', '10:00'], ['10:20', '11:05'], ['11:15', '12:00'],
  ['14:00', '14:45'], ['14:55', '15:40'], ['16:00', '16:45'], ['16:55', '17:40'],
  ['19:00', '19:45'], ['19:55', '20:40'], ['20:50', '21:35'], ['21:45', '22:30'],
];

// 高辨识度课程调色板（参考主流课表高饱和清新配色）
export const courseColors = [
  '#F59E0B', '#F43F5E', '#F97316', '#A855F7', '#06B6D4', '#84CC16',
  '#3B82F6', '#EC4899', '#10B981', '#6366F1', '#EAB308', '#14B8A6',
  '#8B5CF6', '#D946EF', '#2563EB', '#059669',
];

export const emptyCourse = () => ({
  id: null,
  name: '',
  teacher: '',
  room: '',
  weekday: 1,
  start_section: 1,
  end_section: 2,
  weeks: '1-16',
  color: '#5B8DEF',
});

export function parseWeeks(text) {
  const result = [];
  String(text || '').split(/[,，]/).forEach(part => {
    const [a, b] = part.trim().split('-').map(Number);
    if (a && b) {
      for (let i = a; i <= b; i++) result.push(i);
    } else if (a) {
      result.push(a);
    }
  });
  return [...new Set(result)].filter(n => n >= 1 && n <= 30).sort((a, b) => a - b);
}

export function formatWeeks(weeks) {
  if (!weeks?.length) return '';
  const ranges = [];
  let start = weeks[0], last = start;
  for (const n of weeks.slice(1)) {
    if (n === last + 1) {
      last = n;
      continue;
    }
    ranges.push(start === last ? `${start}` : `${start}-${last}`);
    start = last = n;
  }
  ranges.push(start === last ? `${start}` : `${start}-${last}`);
  return ranges.join(',');
}

export function localDate(value) {
  const [year, month, day] = String(value || '').slice(0, 10).split('-').map(Number);
  return year && month && day ? new Date(year, month - 1, day) : null;
}

export function isoDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function defaultEndDate(startValue) {
  const start = localDate(startValue);
  if (!start) return '';
  start.setDate(start.getDate() + 20 * 7 - 1);
  return isoDate(start);
}

export function scheduleWeekCount(schedule) {
  const start = localDate(schedule?.start_date);
  const end = localDate(schedule?.end_date);
  if (start && end) {
    const daysDiff = Math.floor((end - start) / 86400000) + 1;
    return Math.max(1, Math.min(30, Math.ceil(daysDiff / 7)));
  }
  const courseWeeks = schedule?.courses?.flatMap(course => course.weeks || []) || [];
  return Math.min(30, Math.max(20, ...courseWeeks, 20));
}

export function termWeek(startDate, totalWeeks = 20) {
  if (!startDate) return 1;
  const start = new Date(`${startDate}T00:00:00`);
  const today = new Date();
  const elapsed = Math.floor((today - start) / 86400000);
  return Math.max(1, Math.min(totalWeeks, Math.floor(elapsed / 7) + 1));
}

export function weekRange(startDate, weekNumber) {
  const start = localDate(startDate);
  if (!start) return '日期待设置';
  start.setDate(start.getDate() + (weekNumber - 1) * 7);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const format = date => `${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
  return `${format(start)}–${format(end)}`;
}

export function weekDayDate(startDate, dayNumber, weekNumber) {
  const start = localDate(startDate);
  if (!start) return '日期待设置';
  start.setDate(start.getDate() + (weekNumber - 1) * 7 + dayNumber - 1);
  return `${String(start.getMonth() + 1).padStart(2, '0')}.${String(start.getDate()).padStart(2, '0')}`;
}

export function weekMonth(startDate, weekNumber) {
  const start = localDate(startDate);
  if (!start) return '';
  start.setDate(start.getDate() + (weekNumber - 1) * 7);
  return `${String(start.getMonth() + 1).padStart(2, '0')}月`;
}

export function weekDayNumber(startDate, dayNumber, weekNumber) {
  const start = localDate(startDate);
  if (!start) return '';
  start.setDate(start.getDate() + (weekNumber - 1) * 7 + dayNumber - 1);
  return String(start.getDate()).padStart(2, '0');
}

export function shortDay(day) {
  return String(day || '').replace('周', '');
}

export function isDayToday(startDate, dayNumber, weekNumber) {
  const start = localDate(startDate);
  if (!start) return false;
  start.setDate(start.getDate() + (weekNumber - 1) * 7 + dayNumber - 1);
  const now = new Date();
  return start.getFullYear() === now.getFullYear()
    && start.getMonth() === now.getMonth()
    && start.getDate() === now.getDate();
}

export function cleanSectionTime(timeStr) {
  return String(timeStr || '').replace(/^0/, '');
}

export function courseKey(name) {
  return String(name || '未命名课程').trim().replace(/\s+/g, ' ').toLocaleLowerCase();
}

export function buildCourseColorMap(courses) {
  const names = [...new Set((courses || []).map(course => courseKey(course.name)))].sort();
  return new Map(names.map((name, index) => [name, courseColors[index % courseColors.length]]));
}

export function timeRange(course, sectionTimes = defaultSectionTimes) {
  if (!course) return '';
  const start = sectionTimes[course.start_section - 1]?.[0] || '';
  const end = sectionTimes[course.end_section - 1]?.[1] || '';
  return start && end ? `${start}-${end}` : '';
}
