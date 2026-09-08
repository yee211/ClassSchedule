# 简课 (ClassSchedule) 📅✨

> 现代化智能课表管理与可视化系统 —— 优雅透明液态玻璃质感 · 动态 3D WebGL 壁纸底衬 · 日夜模式极速切换 · 智能全格式课表解析 (PDF / Excel / 图片 OCR)。

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg?style=flat-square&logo=vue.js)](https://vuejs.org)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF.svg?style=flat-square&logo=vite)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg?style=flat-square&logo=postgresql)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](#开源协议)

---

## 🌟 核心特性

### 1. 💎 透明液态玻璃拟态设计 (Liquid Glassmorphism)
- **光学微棱高光与双层内阴影**：面板采用极净透明微白渐变（`rgba(255,255,255, 0.04~0.22)`），搭配锐利受光微棱线（`inset 0 1.5px`）与背光微蓝折射暗部，呈现立体通透的水晶切面厚度感。
- **彩色果冻水晶课程卡片**：告别单调纯色块，卡片自带水润通透质感、微光高光内边与文字阴影，并在 Hover 时伴随 Spring 曲线弹性上浮及流光掠影（Fluid Sheen）扫光特效。
- **色相错开防视觉疲劳**：内置大色相差调色盘，相邻课程色彩智能区分，清晰醒目。

### 2. 🌌 动态 3D WebGL 壁纸与日夜模式联动
- **原生内嵌动态壁纸**：课表底层无缝集成全屏 Unity WebGL 3D 动态壁纸，支持桌面级视差渲染与音频响应监听。
- **一键日夜模式切换**：
  - ☀️ **日间模式**：高透光水晶面板，清爽透亮；
  - 🌙 **夜间模式**：自动压暗壁纸亮度（`brightness 0.34`），界面平滑切至深邃深色玻璃面板，保护夜间视力。
- **配置持久化**：用户界面偏好自动记录至本地 `localStorage`，刷新不丢失。

### 3. 📑 全格式课表智能提取与导入
- **Excel 结构化速读**：直接底层读取 `.xlsx`、`.xlsm` 工作表，优先解析“课程明细速查表”，秒级批量录入整学期课表。
- **PDF 原生矢量文本解析**：基于 PyMuPDF (`fitz`) 精确抓取 PDF 矢量文字块与行列矩阵，免去 OCR 转换误差。
- **OCR 图像识别（可选扩展）**：支持图片格式（PNG/JPG/WEBP）或扫描版 PDF，通过 PaddleOCR 提取文本并智能推算候选课程，弹窗复核后快速入库。

### 4. ⏰ 学期与周次时间轴联动
- **日期智能推算**：输入学期开学日期与放假日期后，系统自适应推算当前学期周数（1~30周）及当前周每一天的确切日期（如 `09.07`）。
- **弹性周次选择器**：支持点击周次快速切换预览、一键“回到本周”、单双周过滤、跨节连堂智能合并。
- **课程自由编辑**：支持顶部快速加课，可视化设置课程名称、教师、教室、星期、起止节次、周次范围及自定义颜色。

---

## 🛠️ 技术架构

```
ClassSchedule/
├── app/                  # FastAPI 后端核心
│   ├── db.py             # PostgreSQL 数据库连接、表结构与种子数据
│   ├── main.py           # RESTful API 路由与静态资源托管
│   └── ocr.py            # PDF / Excel / OCR 课表解析引擎
├── frontend/             # Vue 3 前端工程
│   ├── public/wallpaper/ # Unity WebGL 3D 动态壁纸资源
│   ├── src/
│   │   ├── App.vue       # 课表主界面、交互控制与弹窗系统
│   │   ├── main.js       # 前端入口
│   │   └── style.css     # 液态玻璃核心光学变量与全局样式
│   └── vite.config.js    # Vite 配置文件与 API 反向代理
├── scripts/              # 辅助维护脚本
│   ├── setup_database.py # 数据库初始化检查脚本
│   └── inspect_pdf.py    # PDF 页面结构与表格分析排查工具
├── docker-compose.yml    # PostgreSQL 17 容器化编排
├── requirements.txt      # Python 核心依赖
└── requirements-ocr.txt  # OCR 可选依赖 (PaddleOCR)
```

---

## 🚀 快速启动

### 准备工作
- **Python**: 3.10 ~ 3.12
- **Node.js**: 20+ & npm
- **Docker**（用于一键运行 PostgreSQL）

### 1. 克隆项目
```bash
git clone https://github.com/yee211/ClassSchedule.git
cd ClassSchedule
```

### 2. 启动数据库
使用 Docker Compose 快速拉起本地 PostgreSQL 17：
```bash
docker compose up -d postgres
```

### 3. 配置与启动后端
```bash
# 创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# (可选) 复制环境配置文件
copy .env.example .env

# 启动 FastAPI 服务 (开发热重载)
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端开发环境
```bash
cd frontend
npm install
npm run dev
```
打开浏览器访问 `http://localhost:5173`。Vite 会将 `/api` 请求自动反向代理至后端 `8000` 端口。

---

## 📦 生产构建与单服务托管

项目支持由 FastAPI 直接托管构建完成的静态前端资源，无需单独配置 Nginx：

```bash
# 构建前端
cd frontend
npm run build
cd ..

# 启动单体生产服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
访问 `http://localhost:8000` 即可使用完整的课表系统。

---

## 🔒 环境变量与安全配置

创建 `.env` 文件来配置连接信息（该文件已加入 `.gitignore`，严防敏感凭证泄露）：

```env
DATABASE_URL=postgresql://class_schedule:class_schedule@127.0.0.1:5433/class_schedule
POSTGRES_ADMIN_URL=postgresql://class_schedule:class_schedule@127.0.0.1:5433/postgres
```

---

## 📡 主要 API 接口概览

| 请求方式 | 路径 | 描述 |
| :--- | :--- | :--- |
| `GET` | `/api/health` | 服务健康检查 |
| `GET` | `/api/schedules` | 获取所有课表及关联课程列表 |
| `POST` | `/api/courses` | 新增单门课程安排 |
| `PUT` | `/api/courses/{id}` | 更新指定课程信息 |
| `DELETE`| `/api/courses/{id}` | 删除指定课程 |
| `POST` | `/api/import` | 上传课表文件（PDF/Excel/图片）并解析录入 |

---

## 🛡️ 安全检查合规声明

本项目已进行全方位安全排查：
- [x] **敏感文件隔离**：`.env`、本地数据上传目录（`data/`）、开发构建临时文件（`tmp/`、`.vite/`）全部被 `.gitignore` 严格排除。
- [x] **无硬编码机密**：数据库连接均采用动态环境变量加载（`python-dotenv`）。
- [x] **数据安全合规**：课表数据保存在本地 PostgreSQL，无外部第三方未经授权的数据回传。

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源发布。
