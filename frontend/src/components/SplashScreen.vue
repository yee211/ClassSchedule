<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

const props = defineProps({
  duration: { type: Number, default: 3 },
});

const emit = defineEmits(['finish']);

const remaining = ref(props.duration);
let timer = null;

function skip() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  emit('finish');
}

onMounted(() => {
  timer = setInterval(() => {
    remaining.value--;
    if (remaining.value <= 0) {
      skip();
    }
  }, 1000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="splash-screen">
    <img
      class="splash-bg"
      src="/xushi-wallpaper.jpg"
      alt="序时 开屏壁纸"
    />
    <div class="splash-gradient"></div>

    <button
      type="button"
      class="splash-skip"
      title="跳过封面"
      @click="skip"
    >
      <span>跳过</span>
      <span class="skip-countdown">{{ remaining }}s</span>
    </button>

    <div class="splash-footer">
      <div class="splash-brand">
        <span class="brand-dot"></span>
        <strong>序时</strong>
      </div>
      <p class="splash-slogan">时序如流 · 亦有星辰守望</p>
    </div>
  </div>
</template>

<style scoped>
.splash-screen {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 99999;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  background-color: #0f172a;
}

.splash-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  animation: kenburns 6s cubic-bezier(0.25, 1, 0.5, 1) forwards;
}

@keyframes kenburns {
  from {
    transform: scale(1);
  }
  to {
    transform: scale(1.06);
  }
}

.splash-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(15, 23, 42, 0.25) 0%,
    transparent 35%,
    rgba(15, 23, 42, 0.3) 70%,
    rgba(15, 23, 42, 0.75) 100%
  );
  pointer-events: none;
}

.splash-skip {
  position: absolute;
  top: max(18px, env(safe-area-inset-top) + 12px);
  right: 18px;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #ffffff;
  padding: 7px 15px;
  border-radius: 999px;
  font-size: 0.86rem;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  transition: all 0.2s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.splash-skip:active {
  transform: scale(0.95);
  background: rgba(15, 23, 42, 0.7);
}

.skip-countdown {
  background: rgba(255, 255, 255, 0.25);
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.splash-footer {
  position: relative;
  z-index: 5;
  margin-top: auto;
  margin-bottom: max(32px, env(safe-area-inset-bottom) + 20px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}

.splash-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.45);
  padding: 6px 18px;
  border-radius: 999px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}

.splash-brand strong {
  font-size: 1.25rem;
  letter-spacing: 2px;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.4);
}

.brand-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 10px #38bdf8;
}

.splash-slogan {
  margin: 0;
  font-size: 0.85rem;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}
</style>
