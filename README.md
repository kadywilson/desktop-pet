# Smart Desktop Pet / 智能桌宠

一个本地优先的 Windows 桌面宠物应用。它会待在桌面上，可以拖动、双击互动、显示气泡、管理待办、提醒 DDL、短聊天、朗读回复、查询天气，并且可以和本地日记项目联动。

This is a local-first Windows desktop pet built with Python and PySide6. It can sit on your desktop, react to clicks, show speech bubbles, manage todos, chat briefly, play optional TTS audio, show weather, and receive diary context from a companion project.

## 关联项目 / Related Project

本项目可以和日记项目联动：

- [kadywilson/ai_diary](https://github.com/kadywilson/ai_diary)

`ai_diary` 可以导出一份用户确认过的“今日小纸条”到本项目的本地桥接文件中。桌宠只读取这份导出结果，不直接读取原始日记目录，也不会把日记内容上传到云端。

The companion diary project can export a user-approved daily note into this app's local bridge file. The pet reads only that exported file, not the raw diary folder.

## 功能 / Features

- 透明、无边框、始终置顶的桌宠窗口
- 鼠标拖动移动桌宠
- 双击桌宠触发 AI poke 回复
- 气泡显示回复，点击气泡可隐藏
- 表情图片切换：`default`、`happy`、`annoyed`、`upset`
- 托盘菜单和桌宠右键菜单
- Todo 待办窗口，本地 SQLite 存储
- DDL 自动提醒和 AI 个性化提醒文案
- Chat Panel 短聊天输入框
- 本地 JSONL 聊天记忆和归档
- 可选 TTS 语音朗读
- 手动位置天气查询，使用 wttr.in，无 API key
- 可选日记小纸条联动
- 本地日志和本地缓存

## 隐私设计 / Privacy

这个项目默认面向个人本地使用。

- 不需要登录
- 不做云同步
- 不做遥测
- 不读取系统定位
- 不使用 GPS
- 不使用浏览器定位
- 不使用 IP 自动定位
- 天气位置只从 `config/weather.yaml` 手动读取
- 聊天记忆、待办、日志、TTS 缓存、天气缓存都保存在本地
- `.env`、真实 `config/*.yaml`、`data/` 运行数据和 `logs/` 日志不应该提交到仓库

## 环境要求 / Requirements

- Windows 10 或 Windows 11
- Python 3.11
- Anaconda 或 Miniconda
- PySide6
- 依赖见 `requirements.txt`

## 安装 / Setup

克隆仓库：

```powershell
git clone https://github.com/kadywilson/desktop-pet.git
cd desktop-pet
```

创建并激活 conda 环境：

```powershell
conda create -n desktop-pet python=3.11
conda activate desktop-pet
pip install -r requirements.txt
```

复制本地配置模板：

```powershell
Copy-Item .env.example .env
Copy-Item config/persona.example.yaml config/persona.yaml
Copy-Item config/chat.example.yaml config/chat.yaml
Copy-Item config/voice.example.yaml config/voice.yaml
Copy-Item config/weather.example.yaml config/weather.yaml
Copy-Item config/theme.example.yaml config/theme.yaml
```

然后按自己的环境编辑复制出来的本地文件。不要提交 `.env` 和真实的 `config/*.yaml`。

## API 配置 / API Configuration

聊天 AI 使用 OpenAI-compatible API。把 `.env.example` 复制成 `.env` 后填写：

```text
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=your_openai_compatible_model_here
```

TTS 是可选功能：

```text
VOLCENGINE_TTS_API_KEY=your_volcengine_tts_api_key_here
VOLCENGINE_TTS_RESOURCE_ID=your_volcengine_resource_id_here
VOLCENGINE_TTS_VOICE_TYPE=your_volcengine_voice_type_here
```

如果没有配置 API key，相关 AI/TTS 功能会尽量使用 fallback 或自动禁用，不应该影响基础窗口运行。

## 天气配置 / Weather

天气功能使用 wttr.in，不需要 API key。

在 `config/weather.yaml` 中手动配置位置：

```yaml
weather:
  location:
    mode: "manual"
    query: "London"
    display_name: "London"
```

注意：不要把 `query` 留空。空位置请求可能触发 wttr.in 的 IP 推断定位，这不符合本项目的隐私设计。

## 日记联动 / Diary Bridge

如果你也使用 [kadywilson/ai_diary](https://github.com/kadywilson/ai_diary)，可以让日记项目导出今日小纸条到：

```text
data/diary_feedback/inbox/latest.json
```

桌宠菜单中的 `Diary Feedback` 会读取这份本地桥接文件，并把经过用户确认的上下文追加到当前聊天记忆中。

隐私边界：

- 不读取原始日记目录
- 不导入完整日记正文
- 不上传日记内容
- 不调用 TTS 朗读日记内容
- 不把 diary 项目当作云服务

## 运行 / Run

日常静默启动：

```text
run_pet_silent.vbs
```

调试启动：

```text
run_pet_debug.bat
```

手动启动：

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python -m pet_app.main
```

## TTS 试听 / TTS Preview

填好 `.env` 和 `config/voice.yaml` 后，可以生成本地试听音频：

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python scripts/preview_tts.py
```

试听文件会生成到 `data/tts_samples/`。这些文件是本地生成物，不应该提交。

## 使用方式 / Usage

| 操作 | 效果 |
|---|---|
| 拖动桌宠 | 移动窗口 |
| 双击桌宠 | 触发 poke 回复 |
| 右键桌宠 | 打开功能菜单 |
| 点击气泡 | 隐藏气泡 |
| Show Chat | 显示聊天输入框 |
| Open Todo | 打开待办窗口 |
| Weather Today | 查询今日天气 |
| Diary Feedback | 读取日记小纸条桥接文件 |
| Voice On / Voice Off | 切换 TTS 朗读 |
| Archive Chat Memory | 归档当前聊天记忆 |
| Quit | 退出应用 |

## 项目结构 / Project Layout

```text
src/pet_app/
|-- main.py
|-- app.py
|-- config.py
|-- ui/
|-- core/
|-- models/
`-- utils/
```

- `ui/`：PySide6 窗口、气泡、托盘菜单、Todo 窗口、Chat Panel
- `core/`：AI、待办、提醒、聊天记忆、TTS、天气、日记桥接等业务逻辑
- `models/`：数据模型
- `utils/`：路径、日志等工具
- `assets/`：角色图片、图标、主题资源
- `config/`：本地配置和 `.example.yaml` 模板
- `data/`：本地运行数据
- `logs/`：本地日志

## Notes For English Readers

Smart Desktop Pet is a small local Windows companion app. It is not a web app,
not a cloud service, and not a deployed SaaS project.

To run it:

1. Clone the repository.
2. Create the `desktop-pet` conda environment.
3. Install `requirements.txt`.
4. Copy `.env.example` and `config/*.example.yaml` to local files.
5. Fill in optional API credentials.
6. Start with `run_pet_debug.bat` or `python -m pet_app.main`.

The weather feature uses manual location only. The diary bridge is optional and
works with [kadywilson/ai_diary](https://github.com/kadywilson/ai_diary).
