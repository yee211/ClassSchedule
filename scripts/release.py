"""
序时 (ClassSchedule) 自动化版本发布与打包脚本
运行方式:
    python scripts/release.py <版本号, 如 2.1.3> <版本代码, 如 5> "更新说明1" "更新说明2" ...
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

from dotenv import load_dotenv

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env.release"), override=False)
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
ANDROID_DIR = os.path.join(FRONTEND_DIR, "android")
STATIC_DOWNLOAD_DIR = os.path.join(ROOT_DIR, "static", "downloads")
BUILT_APK = os.path.join(ANDROID_DIR, "app", "build", "outputs", "apk", "release", "app-release.apk")
FRONTEND_DIST = os.path.join(FRONTEND_DIR, "dist")
ANDROID_WEB_ASSETS = os.path.join(ANDROID_DIR, "app", "src", "main", "assets", "public")
APPLICATION_ID = "io.github.yee211.classschedule"
VERSION_FILES = [
    os.path.join(FRONTEND_DIR, "src", "utils", "version.js"),
    os.path.join(ANDROID_DIR, "app", "build.gradle"),
    os.path.join(FRONTEND_DIR, "package.json"),
    os.path.join(FRONTEND_DIR, "package-lock.json"),
    os.path.join(ROOT_DIR, "data", "app_version.json"),
    os.path.join(ROOT_DIR, "README.md"),
]

def calc_md5(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def calc_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
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

    # package-lock.json 的根版本必须与 package.json 保持一致，确保 npm ci 可复现。
    lock_path = os.path.join(FRONTEND_DIR, "package-lock.json")
    with open(lock_path, "r", encoding="utf-8") as f:
        lock = json.load(f)
    lock["version"] = version_name
    if "" in lock.get("packages", {}):
        lock["packages"][""]["version"] = version_name
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("  -> 已更新 frontend/package-lock.json")

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

def run_cmd(cmd: list[str], cwd: str):
    print(f"[*] 执行命令: {' '.join(cmd)} (目录: {cwd})")
    subprocess.run(cmd, check=True, cwd=cwd)


def run_capture(cmd: list[str], cwd: str) -> str:
    result = subprocess.run(cmd, check=True, cwd=cwd, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return result.stdout.strip()


def android_sdk_dir() -> Path:
    configured = os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT")
    if configured:
        candidate = Path(configured)
        if candidate.is_dir():
            return candidate
    properties = Path(ANDROID_DIR) / "local.properties"
    if properties.is_file():
        for line in properties.read_text(encoding="utf-8").splitlines():
            if line.startswith("sdk.dir="):
                value = line.split("=", 1)[1].replace(r"\:", ":").replace(r"\\", "\\")
                candidate = Path(value)
                if candidate.is_dir():
                    return candidate
    raise FileNotFoundError("未找到 Android SDK，请配置 ANDROID_HOME、ANDROID_SDK_ROOT 或 local.properties")


def find_android_tool(name: str) -> str:
    sdk = android_sdk_dir()
    suffix = ".bat" if os.name == "nt" else ""
    pattern = f"{name}{suffix}"
    roots = [sdk / "build-tools", sdk / "cmdline-tools"]
    matches = [path for root in roots if root.is_dir() for path in root.rglob(pattern)]
    if not matches:
        raise FileNotFoundError(f"Android SDK 中未找到 {pattern}")
    return str(max(matches, key=lambda path: path.stat().st_mtime))


def validate_version_files(version_name: str, version_code: int) -> None:
    version_js = Path(FRONTEND_DIR, "src", "utils", "version.js").read_text(encoding="utf-8")
    gradle = Path(ANDROID_DIR, "app", "build.gradle").read_text(encoding="utf-8")
    package = json.loads(Path(FRONTEND_DIR, "package.json").read_text(encoding="utf-8"))
    lock = json.loads(Path(FRONTEND_DIR, "package-lock.json").read_text(encoding="utf-8"))
    remote = json.loads(Path(ROOT_DIR, "data", "app_version.json").read_text(encoding="utf-8"))
    checks = {
        "version.js versionName": f"CURRENT_VERSION_NAME = '{version_name}'" in version_js,
        "version.js versionCode": f"CURRENT_VERSION_CODE = {version_code}" in version_js,
        "build.gradle versionName": f'versionName "{version_name}"' in gradle,
        "build.gradle versionCode": f"versionCode {version_code}" in gradle,
        "package.json": package.get("version") == version_name,
        "package-lock.json": lock.get("version") == version_name and lock.get("packages", {}).get("", {}).get("version") == version_name,
        "app_version.json": remote.get("versionName") == version_name and remote.get("versionCode") == version_code,
    }
    failed = [label for label, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("版本文件不一致: " + ", ".join(failed))


def verify_apk(apk_path: str, version_name: str, version_code: int) -> str:
    apksigner = find_android_tool("apksigner")
    signature = run_capture([apksigner, "verify", "--verbose", "--print-certs", apk_path], cwd=ANDROID_DIR)
    if "Verifies" not in signature or "Number of signers:" not in signature:
        raise RuntimeError("APK 签名验证没有返回有效签名者")
    analyzer = find_android_tool("apkanalyzer")
    app_id = run_capture([analyzer, "manifest", "application-id", apk_path], cwd=ANDROID_DIR)
    actual_name = run_capture([analyzer, "manifest", "version-name", apk_path], cwd=ANDROID_DIR)
    actual_code = run_capture([analyzer, "manifest", "version-code", apk_path], cwd=ANDROID_DIR)
    if (app_id, actual_name, actual_code) != (APPLICATION_ID, version_name, str(version_code)):
        raise RuntimeError(
            f"APK 内版本不符: package={app_id}, versionName={actual_name}, versionCode={actual_code}"
        )
    digest_match = re.search(r"certificate SHA-256 digest: ([0-9a-f]+)", signature, re.IGNORECASE)
    return digest_match.group(1).upper() if digest_match else "UNKNOWN"


def distribute_apk(source: str, version_name: str) -> list[Path]:
    download_dir = Path(STATIC_DOWNLOAD_DIR)
    download_dir.mkdir(parents=True, exist_ok=True)
    names = [f"序时_v{version_name}.apk", "序时.apk", "ClassSchedule.apk", f"时序_v{version_name}.apk", "时序.apk"]
    targets = [download_dir / name for name in names]
    with tempfile.TemporaryDirectory(prefix=".release-", dir=download_dir) as temp_name:
        temp_dir = Path(temp_name)
        staged = []
        backups = {}
        for target in targets:
            item = temp_dir / target.name
            shutil.copy2(source, item)
            staged.append(item)
            if target.exists():
                backup = temp_dir / f"{target.name}.previous"
                shutil.copy2(target, backup)
                backups[target] = backup
        hashes = {calc_sha256(item) for item in staged}
        sizes = {item.stat().st_size for item in staged}
        if len(hashes) != 1 or len(sizes) != 1:
            raise RuntimeError("分发 APK 的大小或 SHA-256 不一致")
        replaced = []
        try:
            for item, target in zip(staged, targets):
                os.replace(item, target)
                replaced.append(target)
        except Exception:
            for target in reversed(replaced):
                backup = backups.get(target)
                if backup and backup.exists():
                    os.replace(backup, target)
                else:
                    target.unlink(missing_ok=True)
            raise
    return targets


def restore_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    if source.exists():
        shutil.copytree(source, target)


def validate_release(version_name: str, version_code: int) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version_name):
        raise ValueError("版本号必须是语义化版本，例如 2.1.7")
    if version_code <= 0:
        raise ValueError("versionCode 必须是正整数")
    try:
        published_text = run_capture(
            ["git", "show", "HEAD:frontend/src/utils/version.js"],
            cwd=ROOT_DIR,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        published_text = Path(FRONTEND_DIR, "src", "utils", "version.js").read_text(encoding="utf-8")
    published_match = re.search(r"CURRENT_VERSION_CODE = (\d+)", published_text)
    if published_match and version_code <= int(published_match.group(1)):
        raise ValueError(f"versionCode 必须大于已提交版本 {published_match.group(1)}")
    required_signing = (
        "ANDROID_KEYSTORE_PATH", "ANDROID_KEYSTORE_PASSWORD",
        "ANDROID_KEY_ALIAS", "ANDROID_KEY_PASSWORD",
    )
    missing = [name for name in required_signing if not os.getenv(name)]
    if missing:
        raise ValueError("正式 APK 缺少签名环境变量: " + ", ".join(missing))
    if not Path(os.environ["ANDROID_KEYSTORE_PATH"]).is_file():
        raise ValueError("ANDROID_KEYSTORE_PATH 指向的签名文件不存在")

def main():
    if len(sys.argv) < 3:
        print("用法: python scripts/release.py <version_name> <version_code> [changelog1] [changelog2] ...")
        print("示例: python scripts/release.py 2.1.3 5 \"修复已知问题\" \"优化界面交互\"")
        sys.exit(1)

    version_name = sys.argv[1]
    version_code = int(sys.argv[2])
    changelog = sys.argv[3:] if len(sys.argv) > 3 else ["常规优化与体验提升"]

    validate_release(version_name, version_code)
    snapshots = {path: Path(path).read_bytes() for path in VERSION_FILES if os.path.exists(path)}

    print("==================================================")
    print(f" 开始发布 序时 App v{version_name} (versionCode: {version_code})")
    print("==================================================")

    with tempfile.TemporaryDirectory(prefix="xushi-release-rollback-") as rollback_name:
        rollback_dir = Path(rollback_name)
        tree_snapshots = []
        for index, directory in enumerate((Path(FRONTEND_DIST), Path(ANDROID_WEB_ASSETS))):
            backup = rollback_dir / str(index)
            if directory.exists():
                shutil.copytree(directory, backup)
            tree_snapshots.append((backup, directory))
        try:
            # 版本同步后严格执行 Vite -> Capacitor -> Gradle -> 校验 -> 原子分发。
            update_version_files(version_name, version_code, changelog)
            validate_version_files(version_name, version_code)
            print("\n[*] 2. 编译前端 Vue 项目 (vite build)...")
            run_cmd(["npm.cmd" if os.name == "nt" else "npm", "run", "build"], cwd=FRONTEND_DIR)
            print("\n[*] 3. 同步前端资源到 Capacitor Android 原生目录...")
            run_cmd(["npx.cmd" if os.name == "nt" else "npx", "cap", "sync", "android"], cwd=FRONTEND_DIR)
            print("\n[*] 4. 编译并签名 Android Release APK...")
            gradle = os.path.join(ANDROID_DIR, "gradlew.bat" if os.name == "nt" else "gradlew")
            run_cmd([gradle, "assembleRelease"], cwd=ANDROID_DIR)
            if not os.path.exists(BUILT_APK):
                raise FileNotFoundError(f"未找到生成的 Release APK: {BUILT_APK}")
            print("\n[*] 5. 验证 APK 签名与内部版本...")
            certificate_sha256 = verify_apk(BUILT_APK, version_name, version_code)
            distributed = distribute_apk(BUILT_APK, version_name)
        except Exception:
            for path, content in snapshots.items():
                Path(path).write_bytes(content)
            for backup, directory in tree_snapshots:
                restore_tree(backup, directory)
            print("[!] 构建失败，已恢复版本元数据、前端构建产物和 Android Web 资源。")
            raise

    apk_versioned = distributed[0]
    size_mb = apk_versioned.stat().st_size / (1024 * 1024)
    md5_val = calc_md5(apk_versioned)

    print("\n[*] 6. 本地安装包构建与校验成功！")
    for item in distributed:
        print(f"  -> {item.name}: {item}")
    print(f"  -> 文件大小: {size_mb:.2f} MB")
    sha256_val = calc_sha256(apk_versioned)
    print(f"  -> MD5 校验: {md5_val}")
    print(f"  -> SHA-256 校验: {sha256_val}")
    print(f"  -> 签名证书 SHA-256: {certificate_sha256}")

    print("\n==================================================")
    print(" 本地构建完成；完成服务器同步与线上复核后才算发布完成。")
    print(" 1. 仅暂存本次版本文件与已验证的 APK 产物")
    print(f" 2. git commit -m \"release: v{version_name} (code: {version_code})\"")
    print(" 3. git push")
    print(" 4. 在宝塔终端执行: cd /www/wwwroot/ClassSchedule && git pull origin main")
    print("==================================================")

if __name__ == "__main__":
    main()
