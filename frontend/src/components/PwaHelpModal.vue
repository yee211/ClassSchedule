<script setup>
import { computed } from 'vue';

defineProps({
  open: { type: Boolean, default: false },
  canNativeInstall: { type: Boolean, default: false },
  installed: { type: Boolean, default: false },
});

const emit = defineEmits(['close', 'install']);

const platform = computed(() => {
  const ua = navigator.userAgent || '';
  const isiPadOs = navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1;
  if (/iPhone|iPad|iPod/i.test(ua) || isiPadOs) return 'ios';
  if (/Android/i.test(ua)) return 'android';
  return 'desktop';
});

const browserName = computed(() => {
  const ua = navigator.userAgent || '';
  if (/CriOS/i.test(ua)) return 'Chrome';
  if (/FxiOS/i.test(ua)) return 'Firefox';
  if (/EdgiOS/i.test(ua)) return 'Edge';
  if (/OPiOS/i.test(ua)) return 'Opera';
  if (/SamsungBrowser/i.test(ua)) return '三星浏览器';
  if (/EdgA|Edg\//i.test(ua)) return 'Edge';
  if (/Firefox|FxiOS/i.test(ua)) return 'Firefox';
  if (/Chrome|Chromium/i.test(ua)) return 'Chrome';
  if (/Safari/i.test(ua)) return 'Safari';
  return '当前浏览器';
});
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="emit('close')">
    <section class="modal pwa-help-modal" role="dialog" aria-modal="true" aria-labelledby="pwa-title">
      <div class="modal-head">
        <div>
          <p>添加到主屏幕</p>
          <h2 id="pwa-title">把简课放到手机桌面</h2>
        </div>
        <button type="button" class="icon" aria-label="关闭" @click="emit('close')">×</button>
      </div>

      <div v-if="installed" class="install-status success" role="status">
        <b>已添加到桌面</b>
        <p>当前已在应用模式中运行，无需重复添加。</p>
      </div>

      <div v-else-if="canNativeInstall" class="native-install-box">
        <p>浏览器支持直接安装，点击后会打开系统自带的安装窗口：</p>
        <button type="button" class="primary uiverse-button w-full" @click="emit('install')">添加到桌面</button>
      </div>

      <div v-if="!installed && !canNativeInstall" class="install-status" role="status">
        <b>{{ browserName }} 需要从浏览器菜单添加</b>
        <p>受浏览器安全限制，网页无法替你展开浏览器菜单。按下面两步即可完成。</p>
      </div>

      <div v-if="!installed && !canNativeInstall" class="pwa-steps">
        <template v-if="platform === 'ios'">
          <div class="step-card"><span class="step-num">1</span><div class="step-content">
            <b>建议使用 Safari 打开</b><p>如果当前不是 Safari，请先通过浏览器菜单选择“在 Safari 中打开”。</p>
          </div></div>
          <div class="step-card highlight"><span class="step-num">2</span><div class="step-content">
            <b>点“分享”后选择“添加到主屏幕”</b><p>Safari 的分享按钮通常在底部工具栏；向下滚动操作列表即可找到。</p>
          </div></div>
        </template>

        <template v-else-if="platform === 'android'">
          <div class="step-card"><span class="step-num">1</span><div class="step-content">
            <b>打开 {{ browserName }} 菜单</b><p>点击浏览器右上角或底部的“⋮ / ≡”菜单按钮。</p>
          </div></div>
          <div class="step-card highlight"><span class="step-num">2</span><div class="step-content">
            <b>选择“安装应用”或“添加到主屏幕”</b><p>不同浏览器名称略有区别，确认名称和图标后点击添加。</p>
          </div></div>
        </template>

        <template v-else>
          <div class="step-card"><span class="step-num">1</span><div class="step-content">
            <b>打开 {{ browserName }} 菜单</b><p>在地址栏或浏览器菜单中查找安装图标。</p>
          </div></div>
          <div class="step-card highlight"><span class="step-num">2</span><div class="step-content">
            <b>选择“安装简课”或“创建快捷方式”</b><p>安装后可从桌面或应用列表直接打开。</p>
          </div></div>
        </template>
      </div>

      <div class="modal-actions"><span></span><button class="primary uiverse-button" type="button" @click="emit('close')">完成</button></div>
    </section>
  </div>
</template>

<style scoped>
.pwa-help-modal { max-width: 440px; }
.native-install-box { margin-bottom: 12px; padding: 12px; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; background: rgba(56, 189, 248, 0.12); }
.native-install-box p, .install-status p { margin: 0 0 8px; color: #0369a1; font-size: 0.84rem; line-height: 1.45; }
.w-full { width: 100%; }
.install-status { margin-bottom: 12px; padding: 12px; border: 1px solid rgba(226, 232, 240, 0.8); border-radius: 12px; background: rgba(255, 255, 255, 0.5); }
.install-status.success { border-color: rgba(34, 197, 94, 0.28); background: rgba(34, 197, 94, 0.1); }
.install-status b { display: block; color: #1e293b; font-size: 0.88rem; }
.install-status p { margin: 4px 0 0; color: #64748b; font-size: 0.8rem; }
.pwa-steps { display: flex; flex-direction: column; gap: 10px; margin: 8px 0; }
.step-card { display: flex; gap: 10px; padding: 10px 12px; border: 1px solid rgba(226, 232, 240, 0.8); border-radius: 12px; background: rgba(255, 255, 255, 0.5); }
.step-card.highlight { border-color: rgba(56, 189, 248, 0.3); background: rgba(56, 189, 248, 0.1); }
.step-num { display: flex; flex: 0 0 22px; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #38bdf8; color: #fff; font-size: 0.76rem; font-weight: 700; }
.step-content { flex: 1; }
.step-content b { display: block; margin-bottom: 4px; color: #1e293b; font-size: 0.86rem; }
.step-content p { margin: 0; color: #64748b; font-size: 0.8rem; line-height: 1.45; }
</style>
