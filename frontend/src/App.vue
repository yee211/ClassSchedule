<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

const days = ['周一','周二','周三','周四','周五','周六','周日']
const sectionTimes = [
  ['08:20','09:05'],['09:15','10:00'],['10:20','11:05'],['11:15','12:00'],['14:00','14:45'],
  ['14:55','15:40'],['16:00','16:45'],['16:55','17:40'],['19:00','19:45'],['19:55','20:40'],
]
// 颜色按色相大幅错开，避免相邻课程看起来过于接近。
const courseColors = [
  '#2563EB','#DC2626','#059669','#D97706','#7C3AED','#DB2777','#0891B2','#65A30D',
  '#4F46E5','#EA580C','#0F766E','#B91C1C','#9333EA','#0E7490','#CA8A04','#BE185D',
  '#1D4ED8','#15803D','#C2410C','#86198F','#0369A1','#A16207',
]
const week = ref(1), currentWeek = ref(1), schedules = ref([]), schedule = ref(null), loading = ref(true), message = ref('')
const editorOpen = ref(false), previewOpen = ref(false), previewCourse = ref(null), importerOpen = ref(false), importing = ref(false), importSetup = ref(false), importFile = ref(null), suggestions = ref([]), importError = ref('')
const importStartDate = ref(''), importEndDate = ref('')
const weekMenuOpen = ref(false)
const weekOptions = computed(() => Array.from({length:scheduleWeekCount()}, (_, index) => index + 1))
const emptyCourse = () => ({id:null,name:'',teacher:'',room:'',weekday:1,start_section:1,end_section:2,weeks:'1-16',color:'#5B8DEF'})
const form = reactive(emptyCourse())
const activeCourses = computed(() => schedule.value?.courses.filter(c => !c.weeks?.length || c.weeks.includes(week.value)) || [])
const displayCourses = computed(() => {
  const result=[]
  for(const course of [...activeCourses.value].sort((a,b)=>a.weekday-b.weekday||a.start_section-b.start_section)){
    const previous=result[result.length-1]
    const canMerge=previous && courseKey(previous.name)===courseKey(course.name)
      && previous.teacher===course.teacher && previous.room===course.room
      && previous.weekday===course.weekday && previous.end_section+1===course.start_section
    if(canMerge)previous.end_section=course.end_section
    else result.push({...course})
  }
  return result
})

function notify(text){ message.value=text; window.clearTimeout(notify.timer); notify.timer=window.setTimeout(()=>message.value='',2200) }
function parseWeeks(text){
  const result=[]
  String(text).split(/[,，]/).forEach(part=>{const [a,b]=part.trim().split('-').map(Number); if(a&&b){for(let i=a;i<=b;i++)result.push(i)}else if(a)result.push(a)})
  return [...new Set(result)].filter(n=>n>=1&&n<=30).sort((a,b)=>a-b)
}
function formatWeeks(weeks){
  if(!weeks?.length) return ''
  const ranges=[]; let start=weeks[0], last=start
  for(const n of weeks.slice(1)){if(n===last+1){last=n;continue} ranges.push(start===last?`${start}`:`${start}-${last}`);start=last=n}
  ranges.push(start===last?`${start}`:`${start}-${last}`); return ranges.join(',')
}
async function api(url, options){
  const response=await fetch(url,options); if(!response.ok){let body={};try{body=await response.json()}catch{};throw new Error(body.detail||'请求失败')}
  return response.status===204?null:response.json()
}
async function load(preferredId=schedule.value?.id){
  try{
    const list=await api('/api/schedules'); schedules.value=list
    const savedId=Number(localStorage.getItem('active_schedule_id'))
    schedule.value=list.find(item=>item.id===Number(preferredId)) || list.find(item=>item.id===savedId) || list[0] || null
    if(schedule.value)localStorage.setItem('active_schedule_id',schedule.value.id)
    currentWeek.value=termWeek(schedule.value?.start_date);week.value=currentWeek.value
  }
  catch(error){notify(error.message)} finally{loading.value=false}
}
function selectSchedule(event){
  schedule.value=schedules.value.find(item=>item.id===Number(event.target.value)) || null
  if(schedule.value)localStorage.setItem('active_schedule_id',schedule.value.id)
  currentWeek.value=termWeek(schedule.value?.start_date);week.value=currentWeek.value;weekMenuOpen.value=false
}
async function deleteSchedule(){
  const current=schedule.value
  if(!current)return
  const title=current.term || current.name || '当前课表'
  if(!confirm(`确认删除“${title}”？该课表中的全部课程也会被删除。`))return
  try{
    await api(`/api/schedules/${current.id}`,{method:'DELETE'})
    localStorage.removeItem('active_schedule_id')
    await load(null);notify('课表已删除')
  }catch(error){notify(error.message)}
}
function termWeek(startDate){
  if(!startDate)return 1
  const start=new Date(`${startDate}T00:00:00`), today=new Date();
  const elapsed=Math.floor((today-start)/86400000)
  return Math.max(1,Math.min(scheduleWeekCount(),Math.floor(elapsed/7)+1))
}
function localDate(value){
  const [year,month,day]=String(value || '').slice(0,10).split('-').map(Number)
  return year&&month&&day ? new Date(year,month-1,day) : null
}
function scheduleWeekCount(){
  const start=localDate(schedule.value?.start_date), end=localDate(schedule.value?.end_date)
  if(start&&end){
    const days=Math.floor((end-start)/86400000)+1
    return Math.max(1,Math.min(30,Math.ceil(days/7)))
  }
  const courseWeeks=schedule.value?.courses?.flatMap(course => course.weeks || []) || []
  return Math.min(30, Math.max(20, ...courseWeeks, 20))
}
function isoDate(date){
  return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
}
function defaultEndDate(startValue){
  const start=localDate(startValue); if(!start)return ''
  start.setDate(start.getDate()+20*7-1); return isoDate(start)
}
function weekRange(weekNumber){
  const start=localDate(schedule.value?.start_date)
  if(!start)return '日期待设置'
  start.setDate(start.getDate()+(weekNumber-1)*7)
  const end=new Date(start);end.setDate(end.getDate()+6)
  const format=date=>`${String(date.getMonth()+1).padStart(2,'0')}.${String(date.getDate()).padStart(2,'0')}`
  return `${format(start)}–${format(end)}`
}
function weekDayDate(dayNumber, weekNumber){
  const start=localDate(schedule.value?.start_date)
  if(!start)return '日期待设置'
  start.setDate(start.getDate()+(weekNumber-1)*7+dayNumber-1)
  return `${String(start.getMonth()+1).padStart(2,'0')}.${String(start.getDate()).padStart(2,'0')}`
}
function selectWeek(value){week.value=value;weekMenuOpen.value=false}
function goCurrentWeek(){week.value=currentWeek.value;weekMenuOpen.value=false}
function toggleWeekMenu(){weekMenuOpen.value=!weekMenuOpen.value}
function closeWeekMenu(event){if(!event.target.closest('.week-menu'))weekMenuOpen.value=false}
function openPreview(course){previewCourse.value=course;previewOpen.value=true}
function editPreview(){const course=previewCourse.value;previewOpen.value=false;openEditor(course)}
function openEditor(course){Object.assign(form,emptyCourse(),course||{});form.weeks=formatWeeks(course?.weeks)||'1-16';editorOpen.value=true}
async function save(){
  const payload={schedule_id:schedule.value.id,name:form.name.trim(),teacher:form.teacher.trim(),room:form.room.trim(),weekday:+form.weekday,start_section:+form.start_section,end_section:+form.end_section,weeks:parseWeeks(form.weeks),color:form.color}
  if(payload.end_section<payload.start_section)return notify('结束节次不能早于开始节次')
  try{await api(form.id?`/api/courses/${form.id}`:'/api/courses',{method:form.id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});editorOpen.value=false;notify('课程已保存');await load()}catch(error){notify(error.message)}
}
async function remove(){if(!form.id||!confirm('确认删除这门课程？'))return;try{await api(`/api/courses/${form.id}`,{method:'DELETE'});editorOpen.value=false;notify('课程已删除');await load()}catch(error){notify(error.message)}}
function upload(event){
  const file=event.target.files[0];event.target.value='';if(!file)return
  importerOpen.value=true;importing.value=false;importSetup.value=true;importFile.value=file;suggestions.value=[];importError.value=''
  importStartDate.value=schedule.value?.start_date?.slice(0,10) || ''
  importEndDate.value=schedule.value?.end_date?.slice(0,10) || defaultEndDate(importStartDate.value)
}
async function startImport(){
  if(!importFile.value)return
  if(!importStartDate.value || !importEndDate.value){importError.value='请先填写学期开始日期和结束日期';return}
  if(importEndDate.value<importStartDate.value){importError.value='学期结束日期不能早于开始日期';return}
  importSetup.value=false;importing.value=true;importError.value=''
  const body=new FormData();body.append('file',importFile.value);body.append('start_date',importStartDate.value);body.append('end_date',importEndDate.value)
  try{const result=await api('/api/import',{method:'POST',body});if(result.imported){importerOpen.value=false;await load(result.schedule_id);notify(result.replaced?`已覆盖当前学期，共 ${result.imported} 条课程安排`:`已导入 ${result.imported} 条课程安排`)}else{suggestions.value=result.suggestions;notify(result.engine==='ocr-not-installed'?'文件已上传，请安装 OCR 扩展':'识别完成')}}
  catch(error){importError.value=error.message;notify(error.message)}finally{importing.value=false}
}
function editSuggestion(course){importerOpen.value=false;openEditor(course)}
function courseKey(name){return String(name||'未命名课程').trim().replace(/\s+/g,' ').toLocaleLowerCase()}
const courseColorMap = computed(() => {
  const names=[...new Set((schedule.value?.courses||[]).map(course=>courseKey(course.name)))].sort()
  return new Map(names.map((name,index)=>[name,courseColors[index%courseColors.length]]))
})
function courseColor(name){return courseColorMap.value.get(courseKey(name))||courseColors[0]}
function courseStyle(course){return {gridColumn:`${course.weekday+1}`,gridRow:`${course.start_section+1}/${course.end_section+2}`,'--course':courseColor(course.name)}}
function timeRange(course){return `${sectionTimes[course.start_section-1]?.[0]||''}-${sectionTimes[course.end_section-1]?.[1]||''}`}
const savedBgMode = localStorage.getItem('schedule_bg_mode')
const bgMode = ref(savedBgMode === 'night' ? 'night' : 'transparent')
function toggleNightMode(){
  bgMode.value = bgMode.value === 'night' ? 'transparent' : 'night'
  document.documentElement.setAttribute('data-bg', bgMode.value)
  localStorage.setItem('schedule_bg_mode', bgMode.value)
  notify(bgMode.value === 'night' ? '已开启黑夜模式' : '已关闭黑夜模式')
}
onMounted(()=>{
  document.documentElement.setAttribute('data-bg', bgMode.value)
  load()
  document.addEventListener('click',closeWeekMenu)
})
onUnmounted(()=>document.removeEventListener('click',closeWeekMenu))
</script>

<template>
  <iframe class="wallpaper-background" src="/wallpaper/index.html" title="动态壁纸背景" aria-hidden="true" tabindex="-1"></iframe>
  <div class="ambient-canvas" aria-hidden="true">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>
  </div>
  <main class="shell">
    <header class="top glass">
      <div><span class="brand-dot"></span><strong>简课</strong></div>
      <div class="top-actions">
        <button class="header-action delete-schedule uiverse-button" type="button" :disabled="!schedule" @click="deleteSchedule"><span aria-hidden="true">−</span> 删除课表</button>
        <button class="header-action uiverse-button" type="button" @click="openEditor()"><span aria-hidden="true">＋</span> 添加课程</button>
        <label class="header-action upload uiverse-button"><input type="file" accept=".pdf,.xlsx,.xlsm,.png,.jpg,.jpeg,.webp" @change="upload"><span aria-hidden="true">↑</span> 上传课表</label>
        <button type="button" class="night-mode-button" :class="{ active: bgMode === 'night' }" :aria-label="bgMode === 'night' ? '切换到日间模式' : '切换到黑夜模式'" :title="bgMode === 'night' ? '日间模式' : '黑夜模式'" :aria-pressed="bgMode === 'night'" @click="toggleNightMode">
          <span aria-hidden="true">{{ bgMode === 'night' ? '☀️' : '🌙' }}</span>
        </button>
      </div>
    </header>

    <section class="toolbar glass" aria-label="课表控制">
      <div class="term-picker">
        <p>当前学期</p>
        <label v-if="schedules.length > 1" class="term-select-wrap">
          <span class="sr-only">切换学期</span>
          <select :value="schedule?.id" aria-label="切换学期" @change="selectSchedule">
            <option v-for="item in schedules" :key="item.id" :value="item.id">{{ item.term || item.name || `课表 ${item.id}` }}</option>
          </select>
          <i aria-hidden="true">⌄</i>
        </label>
        <h1 v-else>{{ schedule?.term || '我的课表' }}</h1>
      </div>
      <div class="week-picker">
        <button class="week-nav" aria-label="上一周" @click="week=Math.max(1,week-1)">‹</button>
        <div class="week-menu" @click.stop>
          <button class="week-trigger" :aria-expanded="weekMenuOpen" aria-haspopup="listbox" @click="toggleWeekMenu">
            <span><b>第{{ week }}周</b><small>{{ weekRange(week) }}</small></span><i :class="{open:weekMenuOpen}">⌄</i>
          </button>
          <div v-if="weekMenuOpen" class="week-menu-panel glass" role="listbox" aria-label="选择周次">
            <div class="week-menu-head"><b>选择周次</b><button type="button" @click="goCurrentWeek">回到本周</button></div>
            <div class="week-menu-grid">
              <button v-for="item in weekOptions" :key="item" type="button" class="week-option" :class="{selected:week===item}" :aria-selected="week===item" @click="selectWeek(item)">
                <b>第{{ item }}周</b><small>{{ weekRange(item) }}</small>
              </button>
            </div>
          </div>
        </div>
        <button class="reset-week" :class="{active:week!==currentWeek}" @click="goCurrentWeek">{{ week===currentWeek?'本周':'回到本周' }}</button>
        <button class="week-nav" aria-label="下一周" @click="week=Math.min(weekOptions.length,week+1)">›</button>
      </div>
    </section>

    <section class="schedule glass" :class="{busy:loading}">
      <div v-if="loading" class="state">正在读取课表…</div>
      <div v-else-if="!schedule" class="state">还没有课表</div>
      <div v-else class="grid" style="grid-template-rows:64px repeat(10,78px)">
        <div class="corner">节次</div>
        <div v-for="(day,index) in days" :key="day" class="day"><b>{{ day }}</b><span>{{ weekDayDate(index+1,week) }}</span></div>
        <template v-for="section in 10" :key="section">
          <div class="section" :style="{gridColumn:1,gridRow:section+1}"><b>{{ section }}</b><span>{{ sectionTimes[section-1][0] }}<br>{{ sectionTimes[section-1][1] }}</span></div>
          <div v-for="day in 7" :key="day" class="cell" :style="{gridColumn:day+1,gridRow:section+1}"></div>
        </template>
        <button v-for="course in displayCourses" :key="course.id" class="course" :style="courseStyle(course)" @click="openPreview(course)">
          <b>{{ course.name }}</b><span>{{ course.room }} · {{ course.teacher }}</span><small>{{ timeRange(course) }}</small>
        </button>
      </div>
    </section>
  </main>

  <div v-if="previewOpen" class="backdrop" @click.self="previewOpen=false">
    <section class="modal preview-modal">
      <div class="modal-head"><div><p>课程详情</p><h2>{{ previewCourse?.name }}</h2></div><button type="button" class="icon" @click="previewOpen=false">×</button></div>
      <div class="preview-details">
        <div><span>教师</span><b>{{ previewCourse?.teacher || '未填写' }}</b></div>
        <div><span>教室</span><b>{{ previewCourse?.room || '未填写' }}</b></div>
        <div><span>上课时间</span><b>{{ days[(previewCourse?.weekday || 1)-1] }} · {{ timeRange(previewCourse || {}) }}</b></div>
        <div><span>上课周次</span><b>{{ formatWeeks(previewCourse?.weeks) || '每周' }}</b></div>
        <div><span>课程颜色</span><b class="color-preview"><i :style="{background:courseColor(previewCourse?.name)}"></i>{{ courseColor(previewCourse?.name) }}</b></div>
      </div>
      <div class="modal-actions"><span></span><button class="uiverse-button" type="button" @click="previewOpen=false">关闭</button><button class="primary uiverse-button" type="button" @click="editPreview">编辑</button></div>
    </section>
  </div>

  <div v-if="editorOpen" class="backdrop" @click.self="editorOpen=false">
    <form class="modal" @submit.prevent="save">
      <div class="modal-head"><div><p>{{ form.id?'调整课程':'新建课程' }}</p><h2>{{ form.id?'编辑课程':'添加到课表' }}</h2></div><button type="button" class="icon" @click="editorOpen=false">×</button></div>
      <label>课程名称<input v-model="form.name" required maxlength="80" placeholder="例如：计算机网络"></label>
      <div class="fields"><label>教师<input v-model="form.teacher" maxlength="40" placeholder="选填"></label><label>教室<input v-model="form.room" maxlength="40" placeholder="选填"></label></div>
      <div class="fields three"><label>星期<select v-model="form.weekday"><option v-for="(day,i) in days" :value="i+1">{{ day }}</option></select></label><label>开始<select v-model="form.start_section"><option v-for="n in 10" :value="n">第{{ n }}节</option></select></label><label>结束<select v-model="form.end_section"><option v-for="n in 10" :value="n">第{{ n }}节</option></select></label></div>
      <label>上课周次<input v-model="form.weeks" placeholder="1-16，或 1,3,5"></label>
      <label>课程颜色<input v-model="form.color" class="color" type="color"></label>
      <div class="modal-actions"><button v-if="form.id" type="button" class="danger uiverse-button" @click="remove">删除</button><span></span><button class="uiverse-button" type="button" @click="editorOpen=false">取消</button><button class="primary uiverse-button">保存</button></div>
    </form>
  </div>

  <div v-if="importerOpen" class="backdrop" @click.self="importerOpen=false">
    <section class="modal">
      <div class="modal-head"><div><p>导入课表</p><h2>{{ importing?'正在识别':importSetup?'设置学期日期':'确认识别结果' }}</h2></div><button class="icon" @click="importerOpen=false">×</button></div>
      <div v-if="importing" class="scanner"><i></i><span>正在读取课程信息…</span></div>
      <div v-else-if="importSetup" class="import-setup">
        <p class="import-file">已选择：{{ importFile?.name }}</p>
        <div class="fields">
          <label>学期开始日期<input v-model="importStartDate" type="date" required></label>
          <label>学期结束日期<input v-model="importEndDate" type="date" required></label>
        </div>
        <p v-if="importError" class="import-inline-error">{{ importError }}</p>
        <p class="import-help">系统会根据开始日期和结束日期，自动推算每周日期；课表上方会显示当前周每天的日期。</p>
        <div class="modal-actions"><span></span><button class="uiverse-button" type="button" @click="importerOpen=false">取消</button><button type="button" class="primary uiverse-button" @click="startImport">开始识别</button></div>
      </div>
      <div v-else-if="importError" class="empty error">{{ importError }}</div>
      <div v-else-if="suggestions.length" class="suggestions"><p>选择一门候选课程，确认时间后保存</p><button v-for="course in suggestions" class="uiverse-button" @click="editSuggestion(course)"><span>{{ course.name }}</span><b>添加 ›</b></button></div>
      <div v-else class="empty">没有识别到课程，请手动添加或安装 OCR 扩展。</div>
    </section>
  </div>
  <Transition name="toast"><div v-if="message" class="toast">{{ message }}</div></Transition>
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
  display: block;
}

.term-select-wrap select {
  max-width: min(360px, 38vw);
  padding: 2px 28px 2px 0;
  border: 0;
  outline: 0;
  appearance: none;
  background: transparent;
  color: #172033;
  font: inherit;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;
}

.term-select-wrap i {
  position: absolute;
  right: 4px;
  top: 50%;
  color: #64748b;
  font-style: normal;
  pointer-events: none;
  transform: translateY(-55%);
}

html[data-bg="night"] .term-select-wrap select,
html[data-bg="night"] .term-select-wrap i {
  color: #f8fafc;
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

.import-file {
  margin: 0 0 14px;
  padding: 11px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.58);
  color: #334155;
  font-size: 0.82rem;
  border: 1px solid rgba(255, 255, 255, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.import-help {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 0.75rem;
  line-height: 1.55;
}

.import-inline-error {
  margin: 2px 0 8px;
  color: #e11d48;
  font-size: 0.78rem;
}

.preview-details {
  display: grid;
  gap: 10px;
  margin: 6px 0 10px;
}

.preview-details > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 12px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.75);
  box-shadow: inset 0 1px 0.5px #fff;
}

.preview-details span {
  color: #64748b;
  font-size: 0.82rem;
  font-weight: 500;
}

.preview-details b {
  text-align: right;
  font-size: 0.9rem;
  font-weight: 600;
  color: #0f172a;
}

.color-preview {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-preview i {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2), inset 0 1px 0.5px rgba(255, 255, 255, 0.6);
}

@media (max-width: 680px) {
  .toolbar {
    flex-wrap: wrap;
    gap: 12px;
  }
  .toolbar > div:first-child {
    width: 100%;
  }
  .week-picker {
    width: 100%;
    gap: 4px;
  }
  .term-select-wrap select {
    max-width: calc(100vw - 52px);
    font-size: 1.06rem;
  }
  .week-menu {
    flex: 1;
  }
  .week-menu-panel {
    right: auto;
    left: 0;
    width: min(460px, calc(100vw - 28px));
  }
  .week-menu-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .week-option {
    min-height: 62px;
  }
  .reset-week {
    min-width: 68px!important;
    padding: 0 5px!important;
  }
  .grid {
    grid-template-rows: 58px repeat(10, 68px)!important;
  }
}
</style>
