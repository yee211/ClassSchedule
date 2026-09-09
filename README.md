# 简课 (ClassSchedule) 📅✨

> 现代化智能课表管理与可视化系统 —— 优雅透明液态玻璃质感 · 动态 3D WebGL 壁纸底衬 · 日夜模式极速切换 · Excel 课表 AI 智能解析（OpenAI 兼容协议，失败自动回退本地解析）。

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

### 3. 📑 Excel 课表 AI 智能解析
- **仅接收 Excel**：导入入口收敛为 `.xlsx` / `.xlsm`，前后端双重扩展名校验，隔绝不可控版式带来的识别噪声。
- **大模型结构化提取**：通过 OpenAI 兼容协议把工作簿的单元格矩阵（带坐标与合并单元格范围）交给大模型，按固定 JSON Schema 输出课程名、教师、教室、星期、起止节次与展开后的周次数组。
- **厂商无关**：DeepSeek / 通义千问 / Kimi / OpenAI / 本地 Ollama 均可，只改 `.env` 里的 `AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL` 三项，代码零改动。
- **本地兜底不中断**：未配置密钥、网络超时、HTTP 报错或模型输出不合 Schema 时，自动回退到内置的 OOXML 确定性解析器（直接读 `xl/worksheets/*.xml`），导入功能不会因 AI 故障而瘫痪。
- **逐条容错**：模型返回的课程逐条校验，周次越界、节次倒序、名称超长等脏数据就地纠正或跳过，不会拖垮整批导入。
- **连堂自动合并**：同课程同教师同教室且节次连续时合并为一条（1-2 节 + 3-4 节 → 1-4 节）。

### 4. ⏰ 学期与周次时间轴联动
- **日期智能推算**：输入学期开学日期与放假日期后，系统自适应推算当前学期周数（1~30周）及当前周每一天的确切日期（如 `09.07`）。
- **弹性周次选择器**：支持点击周次快速切换预览、一键“回到本周”、单双周过滤、跨节连堂智能合并。
- **课程自由编辑**：支持顶部快速加课，可视化设置课程名称、教师、教室、星期、起止节次、周次范围及自定义颜色。

---

## 🛠️ 技术架构

```
ClassSchedule/
├── app/                  # FastAPI 后端核心
│   ├── ai.py             # AI 解析层：工作簿序列化 + OpenAI 兼容调用 + Schema 校验
│   ├── auth.py           # PBKDF2 密码哈希与 JWT 签发校验
│   ├── db.py             # PostgreSQL 连接、表结构、就地迁移与种子数据
│   ├── main.py           # RESTful API 路由与静态资源托管
│   └── parser.py         # 本地确定性 Excel 解析（AI 失败时的兜底链路）
├── frontend/             # Vue 3 前端工程
│   ├── public/wallpaper/ # Unity WebGL 3D 动态壁纸资源
│   ├── src/
│   │   ├── App.vue       # 课表主界面、交互控制与弹窗系统
│   │   ├── main.js       # 前端入口
│   │   └── style.css     # 液态玻璃核心光学变量与全局样式
│   └── vite.config.js    # Vite 配置文件与 API 反向代理
├── scripts/              # 辅助维护脚本
│   ├── setup_database.py # 数据库初始化检查脚本
│   └── compare_parse.py  # AI 与本地解析结果对照回归脚本
├── deploy/               # 生产容器化部署（Dockerfile + docker-compose + .env）
├── docker-compose.yml    # 开发用 PostgreSQL 17 容器编排
└── requirements.txt      # Python 依赖
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

# 复制环境配置文件并填入数据库密码与 JWT 密钥（必需）
copy .env.example .env
# AI 解析为可选项：在 .env 里填好 AI_API_KEY 即启用；留空则自动使用本地 Excel 解析

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

创建 `.env` 文件来配置运行参数（该文件已加入 `.gitignore`，严防敏感凭证泄露），完整模板见 [.env.example](.env.example)：

```env
# 数据库
DATABASE_URL=postgresql://class_schedule:class_schedule@127.0.0.1:5433/class_schedule
POSTGRES_ADMIN_URL=postgresql://class_schedule:class_schedule@127.0.0.1:5433/postgres

# 鉴权
JWT_SECRET=please-change-this-to-a-long-random-string
JWT_EXPIRE_MINUTES=10080

# 首次启动创建的默认账号，用于接管升级前的既有课表数据（登录凭证为邮箱）
DEFAULT_EMAIL=demo@example.com
DEFAULT_USERNAME=demo
DEFAULT_PASSWORD=demo1234

# AI 课表解析（OpenAI 兼容协议）
AI_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=
AI_MODEL=deepseek-chat
AI_TIMEOUT_SECONDS=120
AI_MAX_INPUT_CHARS=60000
```

切换 AI 厂商只需改 `AI_BASE_URL` 与 `AI_MODEL`：

| 厂商 | `AI_BASE_URL` | `AI_MODEL` 示例 |
| :--- | :--- | :--- |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| 本地 Ollama | `http://localhost:11434/v1` | `qwen2.5:7b` |

> `AI_API_KEY` 留空时不报错，导入会自动回退到本地确定性解析，因此项目在未配置任何 AI 密钥的情况下依然完整可用。

**模型选型注意**：请选用普通对话模型，**不要用推理类模型**（`*-flash`、`*-reasoner`、带 thinking 的型号）。实测同一份 39 条课程的课表：

| 模型 | 耗时 | 输出结果 |
| :--- | ---: | :--- |
| `deepseek-v4-flash`（推理） | 115.0s | 34 条 |
| `deepseek-chat`（对话） | **10.9s** | 34 条（完全一致） |

推理模型把时间花在隐藏思考 token 上，对本任务无质量收益；且百秒级耗时易超过 Nginx 默认 60s 的 `proxy_read_timeout`，导致生产环境 504。若确需使用慢模型，请同步上调反向代理的 `proxy_read_timeout` 与 `proxy_send_timeout`。

生产容器化部署请改填 [deploy/.env](deploy/.env)，对应变量由 [deploy/docker-compose.yml](deploy/docker-compose.yml) 注入 `app` 服务。

---

## 📡 主要 API 接口概览

除 `/api/health`、`/api/register`、`/api/login` 外，其余接口均需在请求头带上 `Authorization: Bearer <token>`，且数据严格按 `user_id` 隔离。

| 请求方式 | 路径 | 鉴权 | 描述 |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/health` | — | 服务健康检查（同时探活数据库） |
| `POST` | `/api/register` | — | 注册（邮箱 + 用户名 + 密码），自动建一个空课表并返回 JWT |
| `POST` | `/api/login` | — | 登录（邮箱 + 密码），返回 JWT 与用户信息 |
| `GET` | `/api/me` | ✅ | 获取当前登录用户的 id / email / username |
| `GET` | `/api/schedules` | ✅ | 获取当前用户全部课表及关联课程列表 |
| `DELETE`| `/api/schedules/{id}` | ✅ | 删除课表（级联删除其下全部课程） |
| `POST` | `/api/courses` | ✅ | 新增单门课程安排 |
| `PUT` | `/api/courses/{id}` | ✅ | 更新指定课程信息 |
| `DELETE`| `/api/courses/{id}` | ✅ | 删除指定课程 |
| `POST` | `/api/import` | ✅ | 上传 Excel 课表（`.xlsx` / `.xlsm`）解析入库；同一学期重复导入为幂等覆盖 |

`POST /api/import` 除 `file` 外还接受 `start_date` / `end_date` 表单字段（`YYYY-MM-DD`），用于推算周次日期轴；响应体中的 `engine` 标识本次实际生效的解析链路（`ai` 或 `xlsx-fallback(<原因>)`）。

---

## 🛡️ 安全检查合规声明

本项目已进行全方位安全排查：
- [x] **敏感文件隔离**：`.env`、本地数据目录（`data/`）、开发构建临时文件（`tmp/`、`.vite/`）全部被 `.gitignore` 严格排除。
- [x] **无硬编码机密**：数据库连接、JWT 签名密钥与 AI API Key 均采用动态环境变量加载（`python-dotenv`）。
- [x] **上传即用即删**：导入的 Excel 仅用于本次解析，完成后立即删除，不在服务端长期留存。
- [x] **AI 数据外发可控**：启用 AI 解析时，Excel 单元格文本会提交给 `AI_BASE_URL` 指定的模型服务商；若课表含敏感信息，可改用本地 Ollama，或留空 `AI_API_KEY` 完全走本地解析，不产生任何外发。
- [x] **数据本地化**：课表数据保存在自建 PostgreSQL，除上述用户自主开启的 AI 解析外，无任何第三方数据回传。

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源发布。
