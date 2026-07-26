# CantioDAW · AI Agent 音乐制作框架

**AI Agent 驱动的歌声/音乐制作管线**，提供工程 + 音轨式工作流，包含多智能体作曲、自动评价与修正、歌声合成等能力——基于 TypeScript MCP 编排层 + Python 音频核心。

> **离线批处理架构** — 生成 MIDI 和音频文件供导入 DAW 使用。不替代 Ableton、REAPER、FL Studio 等 DAW 的实时录音、混音或现场制作功能。

## 架构

```
自然语言
   ↓
┌─────────────────────────────┐
│  意图 Agent                 │  NL → Music Semantic IR
│  (llm_parse_intent)         │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  作曲 Agent                 │  IR → 编曲方案 (结构/旋律/和声/配器)
│  (llm_compose_from_intent)  │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  参数 Agent                 │  IR → 参数增量
│  (parameter_mapper.py)      │
└─────────────┬───────────────┘
              ↓
     MIDI 生成 /                ← 41 个处理工具
     音轨管理
              ↓
┌─────────────────────────────┐
│  评价 Agent (5 模块)       │  和声 / 旋律 / 节奏 / 音频 / 歌声
│  (critic/*.py)              │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  修正 Agent                 │  诊断 → 修改计划 → 执行 → 验证
│  (revision.ts)             │
└─────────────┬───────────────┘
              ↓
       优化闭环                ← 迭代收敛控制
              ↓
      人类偏好反馈             ← 评分 / A-B 测试 / 采纳率追踪
```

## 管线

```
音频数据集 → 声音训练 → 加载模型 → 作曲 MIDI + 歌词 → 合成 → 混音 → 导出
                          ↑                          ↑
                     SVC / RVC  ← 自动检测 — 模型格式适配器
```

## 快速开始

```bash
# 安装 Python 包
pip install -e .

# 启动 TS Orchestrator MCP 服务器（AI 作曲管线，stdio 通信）
npm run build --prefix ts-orchestrator
node ts-orchestrator/dist/index.js

# 启动 Web UI（数据集管理 + 声音训练）
python -m cantiodaw serve
# 打开 http://127.0.0.1:8080
```

## TS Orchestrator — 56 个工具

编排层通过 stdio 以 MCP 服务器方式运行，暴露 56 个工具（41 个处理工具 + 15 个 LLM 工具）用于工程管理、音乐生成、分析与导出：

### 工程与音轨工具 (8)

| 工具 | 说明 |
|------|------|
| `project_create` | 创建新工程 |
| `project_list` | 列出所有工程 |
| `project_load` | 加载工程详情 |
| `project_delete` | 删除工程 |
| `project_export` | 导出工程为音频 |
| `track_add` | 添加音频/MIDI 音轨 |
| `track_remove` | 删除音轨 |
| `track_update` | 更新音轨属性（音量、静音、名称） |

### MIDI 与合成工具 (4)

| 工具 | 说明 |
|------|------|
| `midi_notes_to_f0` | MIDI 音符转 F0 基频曲线 |
| `midi_lyrics_to_phonemes` | 歌词文本转音素序列 |
| `synthesize` | 从 MIDI + 模型合成歌声 |
| `synthesize_midi` | 合成多轨编曲为 WAV/MIDI |

### 音频处理工具 (3)

| 工具 | 说明 |
|------|------|
| `effect_apply` | 应用音频效果（混响/EQ/压缩） |
| `mix_tracks` | 多轨混音为单音频 |
| `export_stems` | 每轨导出独立分轨文件 |

### 声音训练工具 (2)

| 工具 | 说明 |
|------|------|
| `train_prepare` | 从音频目录准备声音数据集 |
| `train_start` | 开始声音模型训练 |

### 编排工具 (3)

| 工具 | 说明 |
|------|------|
| `compose_song` | 端到端：创建工程 → 添加音轨 → 合成 |
| `train_voice_from_audio` | 完整流程：准备数据 → 训练声音模型 |
| `apply_voice_to_midi` | 应用声音模型到 MIDI 音符 → 合成歌声 |

### 参数调整工具 (7)

| 工具 | 说明 |
|------|------|
| `adjust_dynamics` | 调整音轨段力度曲线 |
| `adjust_articulation` | 调整演奏法（连奏/断奏）和起音 |
| `adjust_vibrato` | 调整颤音深度和速率 |
| `adjust_micro_timing` | 按音符调整微时间偏移 |
| `adjust_harmonic_color` | 调整和声色彩（性质/调式） |
| `apply_swing` | 对音轨应用摇摆 feel |
| `apply_rubato` | 应用速度伸缩曲线 |

### 版本管理工具 (4)

| 工具 | 说明 |
|------|------|
| `project_snapshot` | 创建版本快照 |
| `diff_versions` | 比较两个版本差异 |
| `rollback_to_version` | 回滚到指定版本 |
| `list_versions` | 列出所有版本快照 |

### 渲染工具 (2)

| 工具 | 说明 |
|------|------|
| `render_preview` | 快速低质量预览渲染 |
| `render_final` | 全质量最终渲染 |

### 反馈工具 (2)

| 工具 | 说明 |
|------|------|
| `feedback_submit` | 提交用户评分 (1-5) |
| `feedback_ab_test` | 提交 A/B 测试偏好 |

### 评价分析工具 (5)

| 工具 | 说明 |
|------|------|
| `analyze_harmony` | 和声功能、张力曲线分析 |
| `analyze_melody` | 动机、轮廓、音程分析 |
| `analyze_rhythm` | Groove、密度、稳定性分析 |
| `analyze_audio` | 频谱、动态、空间分析 |
| `analyze_vocal_quality` | 合成歌声 F0 偏差 vs 目标 MIDI、电音/机械伪影检测、断音检测 |

### 音频修正工具 (1)

*合成后（音频层）——直接操作已渲染的音频，与合成前（谱面层）的 adjust_* 工具不同*

| 工具 | 说明 |
|------|------|
| `adjust_synthesized_pitch` | 对合成音频的时间区间做局部音高修正，无需重渲染整轨 |

### LLM 工具 (15)

| 工具 | 用途 |
|------|------|
| `llm_chat` | 通用 LLM 对话 |
| `llm_stream` | 流式 LLM 对话 |
| `llm_generate_lyrics` | 歌词生成 |
| `llm_compose_song` | 端到端歌曲作曲 |
| `llm_suggest_arrangement` | 编曲建议 |
| `llm_analyze_lyrics` | 歌词分析 |
| `llm_compose_music` | 直接 MIDI 作曲 |
| `llm_list_providers` | 列出 LLM 提供商 |
| `llm_list_models` | 列出可用模型 |
| `llm_usage_stats` | 使用统计 |
| `llm_parse_intent` | 自然语言 → Music Semantic IR |
| `llm_query_knowledge_graph` | 知识图谱查询 |
| `llm_compose_from_intent` | IR → 编曲方案 |
| `llm_analyze_music` | 多领域音乐评价 |
| `llm_request_checkpoint` | 请求人工检查点 |

## Music Semantic IR（音乐语义中间表示）

自然语言与音乐参数之间的核心中间层：

```python
from cantiodaw.music.ir import MusicIR, EmotionVector

# "凌晨三点开车，一个人在城市里，很孤独但最后看到希望"
ir = MusicIR(
    emotion=EmotionVector(loneliness=0.8, hope=0.6, nostalgia=0.7),
    scene=SceneTags(tags=["night", "urban", "driving"]),
    energy=EnergyCurve(start=0.2, end=0.8, shape="linear"),
    style=StyleVector(cinematic=0.8, ambient=0.6),
)
print(ir.to_dict())
```

## 知识图谱

11 个音乐表达概念映射到参数增量（YAML 定义）：

```yaml
- id: tension
  label: 紧张感
  affects:
    - target: harmony.dissonance; delta: 0.3
    - target: rhythm.syncopation; delta: 0.3
```

```python
from cantiodaw.music.knowledge_graph import KnowledgeGraph
kg = KnowledgeGraph.load("cantiodaw/music/knowledge_graph.yaml")
effects = kg.query("tension")
concepts = kg.reverse_query("harmony.dissonance")
```

## 评价系统（5 分析模块）

| 模块 | 分析范围 | 诊断示例 |
|------|----------|----------|
| **和声** | 和弦功能分布 (T/SD/D)、不协和曲线、解决率 | "过渡段张力不够" |
| **旋律** | 动机重复、轮廓多样性、音域分布、音程分布 | "大跳音程过多" |
| **节奏** | 摇摆量、音符密度、速度稳定性 | "切分密度过高" |
| **音频** | RMS 能量曲线、频谱亮度、波峰因子、立体声宽度 | "高频亮度不足" |
| **歌声** | 合成音高 vs 目标 MIDI 偏差、电音/机械伪影、断音 | "平均音高偏差 68 音分——跑调" |

> **关于 `llm_analyze_music`**：此 LLM 工具是基于规则评价系统的**补充解读**，不是独立的并行评价路径。工作流为：规则评价（和声/旋律/节奏/音频/歌声）产出结构化数值诊断 → `llm_analyze_music` 读取这些诊断并生成自然语言修改建议。规则评分的 severity 决定优先级，LLM 补充上下文。若 LLM 与规则诊断冲突，以规则评分为准，除非人工介入判断。

### 统一输出格式

```json
{
  "domain": "harmony",
  "problem": "过渡段张力不够",
  "severity": 0.6,
  "diagnosis": ["dominant 和弦占比过低 (12%)"],
  "suggestions": [
    { "action": "adjust_harmonic_color", "params": {"section": "bridge", "quality_delta": "+dominant"} }
  ]
}
```

## 工作流 (7)

| 工作流 | 步骤 |
|--------|------|
| `compose_song` | 创建工程 → 添加音轨 → 音素转换 → 合成 → 导出 |
| `train_voice` | 准备数据集 → 训练模型 |
| `apply_voice` | 歌词转换 → F0 基频 → 合成 |
| `mix_export` | 混音 → 导出分轨 |
| `compose_from_intent` | 解析意图 → 作曲 → MIDI 预览 |
| `critic_revise` | 快照 → 分析 → 快照 → 预览 |
| `full_pipeline` | NL → IR → 作曲 → 评价 → 差异对比 → 最终导出 |

## 端到端场景

### 自然语言 → MIDI
```
输入: "一段宁静的钢琴曲"
→ llm_parse_intent → MusicIR
→ llm_compose_from_intent → 编曲方案 + MIDI 音符
→ export_midi → .mid 文件（导入 DAW 用 VST 音色播放）
```

### 评估闭环
```
生成的 MIDI → analyze_harmony + analyze_melody
→ 评价系统发现 ≥1 个问题 → 给出修改建议
```

### 自修正闭环
```
生成 → 评价 → 修正 Agent → 执行 adjust_* → 预览
→ 迭代，收敛控制（最多 5 轮）
```

### 全流程
```
"凌晨三点开车…孤独但希望"
→ 自动作曲 → 自动评价 → 自动修正 → 最终导出
→ 收集人类反馈
```

## 收敛控制（修正循环）

修正 Agent 迭代运行时遵循以下规则：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最大迭代次数 | 5 轮 | 达到此上限后强制停止 |
| 质量阈值 | 0.8（评分） | 评价评分 ≥ 0.8 时停止，即使还有剩余迭代次数 |
| 无改善上限 | 连续 3 轮 | 连续 3 轮评分未提升即停止并发出警告 |
| 收敛检查 | 每次迭代 | 每次修正后重新跑评价并比较评分 |

循环停止但未收敛时（评分 < 0.8）：
- 如果设置了 `request_checkpoint`，暂停等待人工决策
- 否则输出**历史上评分最好的版本**（不一定是最后一版）

以上为**全局默认值**。可通过 `request_checkpoint` 工具参数按工程覆盖。

## 偏好反馈

数据收集和处理流程：

```
用户评分 (1-5) / A/B 测试
        ↓
PreferenceCollector  →  JSONL 文件存储 (feedback.jsonl / abtest.jsonl / adoption.jsonl)
        ↓
PreferenceModel.train(samples)  →  学习特征权重
        ↓
PreferenceModel.adjust_critic_score(critic_score, features)
        ↓
加权后的评分用于修正 Agent 的收敛判断
```

**状态**：数据采集已完整实现。偏好模型的输出当前用于调整修正收敛过程中的评价评分。**尚未**在生成阶段（作曲 Agent 或意图 Agent）被读取——这是规划中的后续工作。

## 与 DAW 配合使用

CantioDAW 产出结构化 MIDI，DAW 做其他所有事情。工作流：

```
CantioDAW                                 DAW (Ableton / REAPER / FL Studio / Logic)
──────────                                ───────────────────────────────────────────
自然语言 → AI 编曲
       ↓
生成多轨 .mid
       ↓                                         导入 .mid 文件
(可选) 跑 Critic → Revision                      挂 VST 音源
       ↓                                         编辑 MIDI 音符、量化
迭代直到满意                                      录音、混音、加效果
       ↓                                         母带 → 导出成品
导出 .mid ────────────────────────────►
```

### 场景 1：灵感启动

```
你: "一段 cinematic 管弦乐，紧张→恢弘"
CantioDAW: 7 段编曲的 .mid 文件
DAW: 打开 .mid → 挂 BBCSO/Spitfire → 直接听
     满意就继续，不满意改 prompt 重新生成
```

AI 在几秒内给你一个结构化起点，不需要面对空白工程焦虑。

### 场景 2：迭代编曲

```
1. 跑 full_pipeline: 作曲 → 评价 → 修正 → 导出 .mid
2. 在 DAW 里打开试听
3. 如果某段和弦进行不对：
   - A 方案：改 prompt，只重新生成那段
   - B 方案：在 DAW 里直接改 MIDI，其他保留
4. 反复直到结构满意
```

CantioDAW 管**宏观结构**（曲式、和声、情绪走向），DAW 管**微观细节**（音色、演奏法、混音）。

### 场景 3：歌声合成前置

```
1. CantioDAW 作曲 + 生成歌词音素
2. synthesize → 原始歌声 WAV 分轨
3. 导入 DAW 作为人声音轨
4. 在 DAW 里围绕人声做配器
5. 用 adjust_* 工具调音准/时间，不用重新训练模型
```

### 场景 4：分析助手

```
DAW: 导出做好的 MIDI
CantioDAW: 跑 analyze_harmony / analyze_melody / analyze_rhythm
           → "桥段：属和弦占比过低 (12%)"
           → "旋律：第 17-20 小节大跳过多"
DAW: 回去修那些小节
```

评价系统提供**客观诊断**，你在 DAW 里直接操作修正。

### 分工总结

| CantioDAW 负责（离线） | DAW 负责（实时） |
|------------------------|------------------|
| 自然语言 → 结构化编曲 | VST 音源回放 |
| 多轨 MIDI 生成 | 音频录音与编辑 |
| 和声/旋律/节奏分析 | 混音、效果、母带 |
| 歌声合成（原始 WAV） | 编曲精修 |
| 版本差异与回滚 | 现场演奏 |

## CLI 使用

```bash
# 创建工程
cantiodaw project create --name MySong

# 训练声音模型
cantiodaw train --voice MyVoice --data-dir data/voices/my_voice --epochs 50

# 合成（自动检测模型格式）
cantiodaw synthesize --model checkpoints/MyVoice/best_model.safetensors \
  --config config.yaml --pitch 60 --duration 2.0 -o output.wav

# 检测模型格式
cantiodaw detect --model so-vits-svc/G_10000.pth
```

## 输出格式

| 格式 | 来源 | 用途 |
|------|------|------|
| **MIDI** (`.mid`) | 作曲 Agent → `export_midi` | 多轨编曲。导入 DAW 配合 VST 音源播放 |
| **WAV — 合成预览** (`.wav`) | `synthesize_midi` | 基础波形（按音轨类型使用正弦/三角/锯齿波）。编曲结构快速预览，不适合生产 |
| **WAV — 神经网络 SVC** (`.wav`) | `synthesize` + 训练好的 SVC/RVC 模型 | 神经声码器歌声合成输出，质量取决于声音模型训练程度 |
| **JSON** | 评价、IR、版本差异工具 | 分析结果、IR 数据、版本差异 |

## 环境变量

```
CANTIODAW_PYTHON    Python 可执行路径（默认: python）
CANTIODAW_ROOT      CantioDAW 项目根目录（默认: 父目录）
OLLAMA_API_KEY      Ollama Cloud API 密钥
OLLAMA_MODEL        Ollama 模型名（默认: gemma4:31b）
OPENAI_API_KEY      OpenAI API 密钥（可选）
```

## 支持的模型格式（歌声合成）

| 格式 | 检测特征 | 配置文件 |
|------|----------|----------|
| **CantioDAW HybridSVC** (.safetensors/.pt) | `phoneme_feature_dim` / `spectral_envelope_dim` | `config.yaml` |
| **so-vits-svc** (.pth) | `inter_channels` / `filter_channels` / `n_heads` | `config.json` |
| **RVC v1** (.pth, 256-dim) | `generator.` / `emb_g` keys | `config.json` |
| **RVC v2** (.pth, 768-dim) | `generator.` / `dec.4` / `794` keys | `config.json` |

## 依赖

- Python 3.9+, PyTorch 2.0+, Node.js 18+
- `pip install -e .`（Python 包）
- `npm install` 在 `ts-orchestrator/` 目录（TypeScript 依赖）

## 项目结构

```
cantiodaw/
├── music/                  # Music IR、知识图谱、参数映射器
│   ├── ir.py              # MusicIR 数据结构（Python 真理源）
│   ├── knowledge_graph.py # 图谱查询引擎
│   ├── knowledge_graph.yaml # 11 个概念节点
│   ├── parameter_mapper.py # 情绪 → 参数映射表
│   └── labels.py          # 情绪/场景/风格标签分类
├── critic/                 # 5 模块音乐分析
│   ├── harmony.py         # 和弦功能、张力曲线
│   ├── melody.py          # 动机检测、音程分析
│   ├── rhythm.py          # Groove、密度、稳定性
│   ├── audio.py           # 频谱、动态、空间分析
│   └── vocal.py           # 合成歌声音准、伪影分析
├── preference/             # 人类反馈学习
│   ├── collector.py       # 评分、A/B 测试、采纳率追踪
│   └── model.py           # 偏好权重模型
└── project_version.py     # 版本快照、差异对比、回滚

ts-orchestrator/
├── src/
│   ├── mcp/tools.ts       # 41 个处理工具定义
│   ├── llm/tools.ts       # 15 个 LLM 工具定义
│   ├── llm/prompts/       # 意图解析 + 作曲 prompt
│   ├── music/ir.ts        # TypeScript MusicIR 镜像
│   ├── orchestrator/
│   │   ├── composer.ts    # 作曲 Agent (IR → 编曲)
│   │   ├── revision.ts    # 修正 Agent (排优先级 + 修复)
│   │   └── workflows.ts   # 7 个预定义工作流
│   └── bridge/            # Python ↔ TypeScript 桥接
```

## 已知限制

- **非实时 DAW** — 所有处理均为离线/批处理。不替代 Ableton、REAPER、FL Studio 等用于实时录音、混音或现场制作。
- **WAV 合成质量是双轨的**：`synthesize_midi` 使用基础振荡器（正弦/三角/锯齿波）用于编曲预览；神经网络 SVC `synthesize` 的质量完全取决于训练好的声音模型。两者是不同的路径，有不同的质量特性。
- **LLM 作曲质量依赖** — 编曲质量因模型和 prompt 而异，结果需要人工审核和编辑。
- **研究级品质** — 适合实验 AI 作曲和歌声合成，并非开箱即用的商业音乐制作工具。

## 协议

Apache 2.0
