"""
序时 (ClassSchedule) 自动化版本发布与打包脚本
运行方式:
    python scripts/release.py <版本号, 如 2.1.3> <版本代码, 如 5> "更新说明1" "更新说明2" ...
"""
import sys
import os
import json
import re
import hashlib
import subprocess
import shutil

import urllib.parse

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
ANDROID_DIR = os.path.join(FRONTEND_DIR, "android")
STATIC_DOWNLOAD_DIR = os.path.join(ROOT_DIR, "static", "downloads")
BUILT_APK = os.path.join(ANDROID_DIR, "app", "build", "outputs", "apk", "debug", "app-debug.apk")

def calc_md5(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()

def update_version_files(version_name: str, version_code: int, changelog: list):
    print(f"[*] 1. 更新各处版本配置文件为 v{version_name} (code: {version_code})...")

    # 1.1 frontend/src/utils/version.js
    version_js_path = os.path.join(FRONTEND_DIR, "src", "utils", "version.js")
    with open(version_js_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r"export const CURRENT_VERSION_NAME = '.*?';", f"export const CURRENT_VERSION_NAME = '{version_name}';", content)
    content = re.sub(r"export const CURRENT_VERSION_CODE = \d+;", f"export const CURRENT_VERSION_CODE = {version_code};", content)
    with open(version_js_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  -> 已更新 frontend/src/utils/version.js")

    # 1.2 frontend/android/app/build.gradle
    build_gradle_path = os.path.join(ANDROID_DIR, "app", "build.gradle")
    with open(build_gradle_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r"versionCode \d+", f"versionCode {version_code}", content)
    content = re.sub(r'versionName ".*?"', f'versionName "{version_name}"', content)
    with open(build_gradle_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  -> 已更新 frontend/android/app/build.gradle")

    # 1.3 frontend/package.json
    pkg_json_path = os.path.join(FRONTEND_DIR, "package.json")
    with open(pkg_json_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    pkg["version"] = version_name
    with open(pkg_json_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("  -> 已更新 frontend/package.json")

    # 1.4 data/app_version.json
    app_version_path = os.path.join(ROOT_DIR, "data", "app_version.json")
    with open(app_version_path, "r", encoding="utf-8") as f:
        ver_info = json.load(f)
    ver_info["versionCode"] = version_code
    ver_info["versionName"] = version_name
    ver_info["title"] = f"发现新版本 v{version_name}"
    
    # 支持带版本号的中文命名（序时）及标准 URL 编码
    apk_filename = f"序时_v{version_name}.apk"
    quoted_apk = urllib.parse.quote(apk_filename)
    ver_info["downloadUrl"] = f"https://gh-proxy.com/https://raw.githubusercontent.com/yee211/ClassSchedule/main/static/downloads/{quoted_apk}"
    ver_info["backupDownloadUrl"] = f"https://api.tanzeng.xyz/downloads/{quoted_apk}"

    if changelog:
        ver_info["changelog"] = changelog
    with open(app_version_path, "w", encoding="utf-8") as f:
        json.dump(ver_info, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("  -> 已更新 data/app_version.json")

    # 1.5 README.md
    readme_path = os.path.join(ROOT_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        readme = re.sub(r"Release-v\d+\.\d+\.\d+", f"Release-v{version_name}", readme)
        readme = re.sub(r"Android 客户端 \(v\d+\.\d+\.\d+\)", f"Android 客户端 (v{version_name})", readme)
        quoted_apk = urllib.parse.quote(f"序时_v{version_name}.apk")
        readme = re.sub(r"%E5%BA%8F%E6%97%B6_v\d+\.\d+\.\d+\.apk", quoted_apk, readme)
        readme = re.sub(r"序时_v\d+\.\d+\.\d+\.apk", f"序时_v{version_name}.apk", readme)
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme)
        print("  -> 已更新 README.md")

def run_cmd(cmd, cwd):
    print(f"[*] 执行命令: {cmd} (目录: {cwd})")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"[!] 命令执行失败: {cmd}")
        sys.exit(res.returncode)

def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/release.py <version_name> <version_code> [changelog1] [changelog2] ...")
        print("示例: python scripts/release.py 2.1.3 5 \"修复已知问题\" \"优化界面交互\"")
        sys.exit(1)

    version_name = sys.argv[1]
    version_code = int(sys.argv[2])
    changelog = sys.argv[3:] if len(sys.argv) > 3 else ["常规优化与体验提升"]

    print(f"==================================================")
    print(f" 开始发布 序时 App v{version_name} (versionCode: {version_code})")
    print(f"==================================================")

    # 步骤 1: 更新配置文件
    update_version_files(version_name, version_code, changelog)

    # 步骤 2: 前端打包
    print("\n[*] 2. 编译前端 Vue 项目 (vite build)...")
    run_cmd("npm run build", cwd=FRONTEND_DIR)

    # 步骤 3: 同步前端资源到 Android
    print("\n[*] 3. 同步前端构建产物到 Capacitor Android 原生目录...")
    run_cmd("npx cap sync android", cwd=FRONTEND_DIR)

    # 步骤 4: 编译 Android 原生 APK
    print("\n[*] 4. 调用 Gradle 编译 Android 原生 APK...")
    gradle_cmd = "gradlew.bat assembleDebug" if os.name == "nt" else "./gradlew assembleDebug"
    run_cmd(gradle_cmd, cwd=ANDROID_DIR)

    # 步骤 5: 拷贝并生成多版本分发包 (序时_v{ver}.apk, 序时.apk, ClassSchedule.apk)
    if not os.path.exists(BUILT_APK):
        print(f"[!] 未找到生成的 APK 文件: {BUILT_APK}")
        sys.exit(1)

    os.makedirs(STATIC_DOWNLOAD_DIR, exist_ok=True)
    apk_versioned = os.path.join(STATIC_DOWNLOAD_DIR, f"序时_v{version_name}.apk")
    apk_latest = os.path.join(STATIC_DOWNLOAD_DIR, "序时.apk")
    apk_legacy = os.path.join(STATIC_DOWNLOAD_DIR, "ClassSchedule.apk")
    apk_alias_ver = os.path.join(STATIC_DOWNLOAD_DIR, f"时序_v{version_name}.apk")
    apk_alias_lat = os.path.join(STATIC_DOWNLOAD_DIR, "时序.apk")

    shutil.copy2(BUILT_APK, apk_versioned)
    shutil.copy2(BUILT_APK, apk_latest)
    shutil.copy2(BUILT_APK, apk_legacy)
    shutil.copy2(BUILT_APK, apk_alias_ver)
    shutil.copy2(BUILT_APK, apk_alias_lat)

    size_mb = os.path.getsize(apk_versioned) / (1024 * 1024)
    md5_val = calc_md5(apk_versioned)

    print("\n[*] 5. 安装包生成与分发成功！")
    print(f"  -> 序时版本包: {apk_versioned}")
    print(f"  -> 序时最新包: {apk_latest}")
    print(f"  -> 兼容包: {apk_legacy}")
    print(f"  -> 文件大小: {size_mb:.2f} MB")
    print(f"  -> MD5 校验: {md5_val}")

    print("\n==================================================")
    print(" 编译与打包流水线全部完成！后续推送指引：")
    print(" 1. git add .")
    print(f" 2. git commit -m \"release: v{version_name} (code: {version_code})\"")
    print(" 3. git push")
    print(" 4. 在宝塔终端执行: cd /www/wwwroot/ClassSchedule && git pull origin main")
    print("==================================================")

if __name__ == "__main__":
    main()
