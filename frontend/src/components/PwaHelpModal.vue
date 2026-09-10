<script setup>
defineProps({
  open: { type: Boolean, default: false },
  canNativeInstall: { type: Boolean, default: false },
});

const emit = defineEmits(['close', 'install']);
</script>

<template>
  <div v-if="open" class="backdrop" @click.self="emit('close')">
    <section class="modal pwa-help-modal">
      <div class="modal-head">
        <div>
          <p>添加到主屏幕指引</p>
          <h2>添加到手机桌面</h2>
        </div>
        <button type="button" class="icon" @click="emit('close')">×</button>
      </div>

      <div v-if="canNativeInstall" class="native-install-box">
        <p>浏览器已准备就绪，可直接调用系统弹窗一键添加：</p>
        <button type="button" class="primary uiverse-button w-full" @click="emit('install')">
          立即一键添加到桌面
        </button>
      </div>

      <div class="pwa-steps">
        <div class="step-card">
          <span class="step-num">1</span>
          <div class="step-content">
            <b>为什么「添加到桌面」是灰色？</b>
            <p>小米手机（MIUI / HyperOS）系统安全策略默认<b>禁止</b>应用创建桌面快捷方式，需手动为小米浏览器开启该权限。</p>
          </div>
        </div>

        <div class="step-card highlight">
          <span class="step-num">2</span>
          <div class="step-content">
            <b>开启步骤（仅需设置一次）：</b>
            <ol>
              <li>打开手机<b>「设置」</b>；</li>
              <li>进入<b>「应用设置」</b> ➜ <b>「应用管理」</b>（或权限管理）；</li>
              <li>在列表中搜索并点击<b>「小米浏览器」</b>；</li>
              <li>进入<b>「权限管理」</b>，找到<b>「桌面快捷方式」</b>（或创建桌面快捷方式）；</li>
              <li>将其勾选为<b>「允许」</b>。</li>
            </ol>
          </div>
        </div>

        <div class="step-card">
          <span class="step-num">3</span>
          <div class="step-content">
            <b>检查桌面布局未锁定：</b>
            <p>确认手机桌面未开启「锁定桌面布局」（在桌面双指捏合 ➜ 桌面设置可查看）。</p>
          </div>
        </div>

        <div class="step-card">
          <span class="step-num">4</span>
          <div class="step-content">
            <b>返回浏览器添加：</b>
            <p>完成权限开启后，返回浏览器刷新页面，点击底部 <b>≡</b> 菜单 ➜ <b>「添加到桌面」</b> 即会恢复彩色并可直接点击！</p>
          </div>
        </div>
      </div>

      <div class="modal-actions">
        <span></span>
        <button class="primary uiverse-button" type="button" @click="emit('close')">我知道了</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.pwa-help-modal {
  max-width: 440px;
}
.native-install-box {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.3);
  padding: 12px;
  border-radius: 12px;
  margin-bottom: 12px;
}
.native-install-box p {
  margin: 0 0 8px;
  font-size: 0.84rem;
  color: #0369a1;
}
.w-full {
  width: 100%;
}
.pwa-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 8px 0;
  max-height: 60vh;
  overflow-y: auto;
}
.step-card {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(226, 232, 240, 0.8);
}
.step-card.highlight {
  background: rgba(254, 243, 199, 0.5);
  border-color: rgba(245, 158, 11, 0.3);
}
.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #38bdf8;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.76rem;
  font-weight: 700;
  flex-shrink: 0;
}
.step-card.highlight .step-num {
  background: #f59e0b;
}
.step-content {
  flex: 1;
}
.step-content b {
  display: block;
  font-size: 0.86rem;
  color: #1e293b;
  margin-bottom: 4px;
}
.step-content p {
  margin: 0;
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.45;
}
.step-content ol {
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 0.8rem;
  color: #475569;
  line-height: 1.5;
}
</style>
