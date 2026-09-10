<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

const props = defineProps({
  duration: { type: Number, default: 1.0 },
});

const emit = defineEmits(['finish']);

let timer = null;

function dismiss() {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  emit('finish');
}

onMounted(() => {
  timer = setTimeout(() => {
    dismiss();
  }, props.duration * 1000);
});

onUnmounted(() => {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
});
</script>

<template>
  <div class="splash-screen" role="dialog" aria-label="序时 开屏封面" @click="dismiss">
    <img
      class="splash-bg"
      src="/xushi-wallpaper.jpg"
      alt="序时 循时而行 自有序章"
    />
    <div class="splash-ambient"></div>
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
  background-color: #0f172a;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.splash-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  animation: kenburns 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards;
}

@keyframes kenburns {
  from {
    transform: scale(1);
  }
  to {
    transform: scale(1.04);
  }
}

.splash-ambient {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at 50% 80%,
    rgba(255, 255, 255, 0.05) 0%,
    transparent 60%
  );
  pointer-events: none;
}
</style>
