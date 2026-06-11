# Smart Desktop Pet / 智能桌宠

一个本地优先的 Windows 桌面宠物应用，使用 Python 和 PySide6 开发。

Smart Desktop Pet 会待在桌面上，可以拖动、双击互动、显示气泡、管理待办、提醒 DDL、短聊天、朗读回复、查询天气，并且可以选择性地和本地日记项目联动。

这个项目默认面向私人本地使用。真实 API key、本地配置、聊天记忆、待办数据、日志、TTS 缓存、天气缓存和日记桥接文件都应该留在你自己的电脑上。

## 这个项目是做什么的

Smart Desktop Pet 主要解决这件事：

> 在桌面上放一个轻量的本地陪伴型小桌宠，它可以提醒你、陪你短聊、显示天气，并在你允许时接收一小段脱敏日记上下文。

它不是云服务，不是网页应用，也不需要部署到服务器。

## 功能

* 透明、无边框、始终置顶的桌宠窗口。
* 鼠标拖动移动桌宠。
* 双击桌宠触发简短 AI poke 回复。
* 用气泡显示回复。
* 表情切换：`default`、`happy`、`annoyed`、`upset`。
* 本地 Todo 待办窗口，使用 SQLite 存储。
* DDL 自动提醒和 AI 个性化提醒文案。
* Chat Panel 短聊天输入框。
* 本地 JSONL 聊天记忆和归档。
* 可选：使用 Volcengine / Doubao TTS 朗读气泡文字。
* 可选：使用 wttr.in 查询手动配置位置的天气。
* 可选：接收 AI Diary Feedback 导出的脱敏日记小纸条。

## 关联项目

本项目可以选择性地与 AI Diary Feedback 联动：

[https://github.com/kadywilson/ai_diary](https://github.com/kadywilson/ai_diary)

日记项目可以导出一份用户确认过的本地 JSON bridge 文件，里面只包含脱敏后的上下文，例如简短摘要或建议语气。桌宠只读取这份导出文件，不直接读取原始日记目录、完整日记正文、原始 AI 对话、API key、token 或本机私有路径。

即使没有安装 AI Diary Feedback，也可以正常使用本桌宠项目。

## 项目结构

```text
src/pet_app/
|-- main.py                  # 应用入口
|-- app.py                   # 主控制器
|-- config.py                # 基于环境变量的 AI 配置
|-- ui/                      # PySide6 窗口、气泡、托盘菜单
|-- core/                    # AI、待办、提醒、聊天记忆、TTS、天气
|-- models/                  # 数据模型
`-- utils/                   # 路径、日志、工具函数

assets/                      # 桌宠图片、图标、主题资源
config/                      # 本地 YAML 配置和公开 example 模板
data/                        # 本地运行数据；仓库只提交 .gitkeep
logs/                        # 本地日志；仓库只提交 .gitkeep
scripts/                     # 可选辅助脚本
```

## 安装

建议使用 Windows 10/11、Python 3.11 和 conda。

```bat
conda create -n desktop-pet python=3.11
conda activate desktop-pet
python -m pip install -r requirements.txt
```

## 配置

复制配置模板：

```bat
copy .env.example .env
copy config\persona.example.yaml config\persona.yaml
copy config\chat.example.yaml config\chat.yaml
copy config\voice.example.yaml config\voice.yaml
copy config\weather.example.yaml config\weather.yaml
copy config\theme.example.yaml config\theme.yaml
```

然后编辑复制出来的本地文件，填入你自己的私有配置。

常用 `.env` 配置：

```env
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=your_openai_compatible_model_here

VOLCENGINE_TTS_API_KEY=your_volcengine_tts_api_key_here
VOLCENGINE_TTS_RESOURCE_ID=your_volcengine_resource_id_here
VOLCENGINE_TTS_VOICE_TYPE=your_volcengine_voice_type_here
```

不要提交 `.env` 或真实的 `config/*.yaml`。

## 天气

天气功能使用 wttr.in，不需要 API key。

在 `config/weather.yaml` 中手动配置位置：

```yaml
weather:
  location:
    mode: "manual"
    query: "London"
    display_name: "London"
```

不要把 `query` 留空。空位置请求可能触发 wttr.in 的 IP 推断定位，这不符合本项目的隐私设计。

## 可选联动：AI Diary Feedback

如果你使用 AI Diary Feedback，它可以导出本地 bridge 文件给桌宠：

```text
data/diary_feedback/inbox/latest.json
```

桌宠菜单中的 `Diary Feedback` 会读取这份本地 bridge 文件，并把脱敏上下文追加到当前本地聊天记忆中。

这个 bridge 的边界很窄：

* 不应该包含完整日记正文。
* 不应该包含原始 AI 对话。
* 不应该包含 API key 或 token。
* 不应该包含本机私有路径。
* 不会上传任何内容。

## 启动

日常静默启动：

```text
run_pet_silent.vbs
```

调试启动：

```text
run_pet_debug.bat
```

手动启动：

```bat
conda activate desktop-pet
set PYTHONPATH=src
python -m pet_app.main
```

PowerShell：

```powershell
conda activate desktop-pet
$env:PYTHONPATH = "src"
python -m pet_app.main
```

## 怎么使用

### 戳一戳桌宠

双击桌宠窗口。程序会调用你配置的 AI provider 生成简短回复，并显示在气泡里。如果 AI 配置缺失或调用失败，会使用 fallback，不应该导致程序崩溃。

### 短聊天

从托盘菜单或桌宠右键菜单打开 Chat Panel。聊天记忆保存在本地 `data/chat_memory/` 下，格式是 JSONL。

### 待办和提醒

从菜单打开 Todo 窗口，创建待办并设置截止时间。程序可以在未完成、未过期的待办到期前提醒你。

### 天气

从菜单点击 `Weather Today` 或 `Weather Tomorrow`。天气请求会在后台执行，结果显示在气泡中。

### 语音朗读

可以从菜单切换 Voice On / Voice Off。Voice Off 时不应该调用 TTS API。

### TTS 试听

填好 `.env` 和 `config/voice.yaml` 后，可以生成本地试听音频：

```bat
conda activate desktop-pet
set PYTHONPATH=src
python scripts\preview_tts.py
```

试听文件会生成到 `data/tts_samples/`，不应该提交。

## 隐私与安全

这个仓库只应该包含代码、公开资源、文档和示例配置。

不要提交：

* `.env`
* 真实 `config/*.yaml`
* `data/pet.db`
* `data/chat_memory/`
* `data/diary_feedback/`
* `data/tts_cache/`
* `data/tts_samples/`
* `data/weather_cache/`
* 日志
* 生成音频
* API key 或 token
* 本机私有路径

更多说明：

* `SECURITY.md`
* `AGENTS.md`

## License

MIT License。见 `LICENSE`。
