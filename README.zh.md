# CantioDAW

AI-Powered Singing Voice Production DAW — 智能歌声制作工作站，支持多智能体 AI 编曲、实时歌声转换（SVC/RVC/DDSP-SVC）和可扩展的 MCP 插件系统。

---

## 功能

- **AI 多智能体编曲管线**：Intent → Compose → Params → MIDI → Critic → Revise 闭环
- **歌声转换**：原生支持 SVC、RVC、DDSP-SVC 三种格式
- **双界面**：现代 Web UI（Flask）+ PyQt6 桌面 GUI，支持中英文切换
- **MCP 协议**：56 个工具（41 DAW + 15 LLM）+ 7 个预设工作流
- **偏好学习**：人工反馈收集与模型微调
- **独立可执行文件**：预编译二进制，无需自行构建

---

## 快速安装

### Windows

```powershell
curl -LO https://github.com/cuteandevil/CantioDAW/releases/latest/download/CantioDAW-v0.1.0-release.zip
Expand-Archive -Path CantioDAW-v0.1.0-release.zip -DestinationPath ./cantiodaw
cd cantiodaw
./cantiodaw-mcp.exe --test
```

---

## 使用方法

```bash
# 启动 MCP 服务（任何 MCP 客户端可连接）
cantiodaw-mcp.exe

# 指定端口并启动 Web UI
cantiodaw-mcp.exe --port 8080 --webui

# 测试模式 - 验证所有工具和工作流
cantiodaw-mcp.exe --test

# 启动 PyQt6 桌面 GUI
cantiodaw-mcp.exe --gui
```

---

## 下载

最新发布包请访问 [Releases 页面](https://github.com/cuteandevil/CantioDAW/releases)。

| 文件 | 大小 | 说明 |
|------|------|------|
| CantioDAW-v0.1.0-release.zip | 32.5 MB | 独立 exe + python_bridge.py，解压即用 |
| CantioDAW-v0.1.0-source.zip | 0.2 MB | 完整源代码（开发用） |

---

## 系统要求

| 组件 | 要求 |
|------|------|
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20.04+ |
| Node.js | ≥ 18（运行 exe 不需要） |
| Python | ≥ 3.9（SVC/RVC 推理需要） |
| PyTorch | ≥ 2.0 |
| GPU（可选） | CUDA 11.8+ |
| AI 后端 | Ollama 或 OpenAI API |

---

## 开发

源代码托管在私有仓库 [CantioDAW-dev](https://github.com/cuteandevil/CantioDAW-dev)。

```bash
git clone https://github.com/cuteandevil/CantioDAW-dev.git
cd CantioDAW-dev
pip install -e ".[all]"

cd ts-orchestrator
npm install
npm run release
```

---

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    MCP Client                        │
├─────────────────────────────────────────────────────┤
│                  cantiodaw-mcp                       │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Web UI   │  │ PyQt GUI │  │ Pipeline Engine  │  │
│  ├───────────┤  ├──────────┤  ├──────────────────┤  │
│  │  Flask    │  │ Desktop  │  │ Intent→Compose→  │  │
│  │  REST API │  │ Native   │  │ Params→MIDI→     │  │
│  │  SSE      │  │ Cross-   │  │ Critic→Revise    │  │
│  │           │  │ platform │  │                   │  │
│  └───────────┘  └──────────┘  └──────────────────┘  │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │   SVC     │  │   RVC    │  │   DDSP-SVC      │  │
│  │  Adapter  │  │  Adapter │  │    Adapter       │  │
│  └───────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 许可证

MIT License

---

*CantioDAW — 用智慧歌唱。*
