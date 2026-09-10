import { appApi } from '../api/index.js';

export const CURRENT_VERSION_NAME = '2.1.3';
export const CURRENT_VERSION_CODE = 5;

const IGNORED_VERSION_KEY = 'ignored_update_version_code';
const IGNORED_TIME_KEY = 'ignored_update_time';
const IGNORE_COOLDOWN_MS = 12 * 60 * 60 * 1000; // 稍后提醒冷却时间：12 小时

/**
 * 检查应用是否有新版本
 * @param {boolean} silent 是否为静默检查（如 App 启动时）
 * @returns {Promise<{ hasUpdate: boolean, updateInfo?: object, reason?: string, currentVersion?: string }>}
 */
export async function checkAppUpdate(silent = false) {
  try {
    const remote = await appApi.getVersion();
    if (!remote || typeof remote.versionCode !== 'number') {
      return { hasUpdate: false, reason: 'invalid_remote_data' };
    }

    const hasNewVersion = remote.versionCode > CURRENT_VERSION_CODE;
    if (!hasNewVersion) {
      return { hasUpdate: false, currentVersion: CURRENT_VERSION_NAME };
    }

    // 如果是静默检查且用户曾选择“稍后提醒”此版本（且非强制更新），且在12小时冷却内，则不弹窗打扰
    if (silent && !remote.forceUpdate) {
      const ignoredCode = Number(localStorage.getItem(IGNORED_VERSION_KEY));
      const ignoredTime = Number(localStorage.getItem(IGNORED_TIME_KEY)) || 0;
      const isCooldownActive = Date.now() - ignoredTime < IGNORE_COOLDOWN_MS;

      if (ignoredCode === remote.versionCode && isCooldownActive) {
        return { hasUpdate: false, ignored: true };
      }
    }

    return {
      hasUpdate: true,
      updateInfo: remote,
    };
  } catch (error) {
    if (!silent) {
      throw error;
    }
    return { hasUpdate: false, reason: 'network_error' };
  }
}

/**
 * 记录用户稍后提醒的版本号及时间
 */
export function ignoreUpdateVersion(versionCode) {
  if (versionCode) {
    localStorage.setItem(IGNORED_VERSION_KEY, String(versionCode));
    localStorage.setItem(IGNORED_TIME_KEY, String(Date.now()));
  }
}

/**
 * 清除已忽略记录（用于手动检查时强制重置）
 */
export function clearIgnoredUpdate() {
  localStorage.removeItem(IGNORED_VERSION_KEY);
  localStorage.removeItem(IGNORED_TIME_KEY);
}

/**
 * 唤起系统浏览器下载 APK
 */
export function openDownloadUrl(url) {
  if (!url) return;
  // 在 Capacitor Android 原生环境下，_system 会直接调用系统默认浏览器打开下载
  // 在普通 Web 浏览器下，打开新标签页下载
  const win = window.open(url, '_system');
  if (!win || win.closed || typeof win.closed === 'undefined') {
    // 降级方案
    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
}
