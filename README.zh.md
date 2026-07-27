# CantioDAW · AI Agent 音乐制作框架

**AI Agent 驱动的歌声/音乐制作管线**，提供工程 + 音轨式工作流，包含多智能体作曲、自动评价与修正、歌声合成、SoundFont 真实乐器渲染——基于 TypeScript MCP 编排层 + Python 音频核心。

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
│  参数 Agent                 │  IR → Parameter Delta
│  (parameter_mapper.py)      │
└─────────────┬───────────────┘
              ↓
    MIDI 生成 /                ← 57 个 DAW/MIDI 工具
    音轨管理
              ↓
┌─────────────────────────────┐
│  Critic Agent (5 模块)     │  和声 / 旋律 / 节奏 / 音频 / 人声
│  (critic/*.py)              │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Revision Agent             │  诊断 → 修正 → 重检 (自动循环)
│  (revision_execute)         │
└─────────────┬───────────────┘
              ↓
        优化闭环               ← 收敛控制迭代
              ↓
       人类偏好反馈            ← 评分 / A/B 对比 / 收藏 / 重听
```

## 管线

```
音频数据集 → 声音训练 → 加载模型 → 编排 MIDI + 歌词 → 合成 → 混音 → 导出
                          ↑                          ↑
                      SVC / RVC  ← 自动检测 — Model Format Adapter
                                         ↑
                                   SoundFont (SF2/FluidSynth) — 真实乐器合成
```

## 快速开始

```bash
# 安装 Python 包
pip install -e .

# 启动 TS 编排层 MCP 服务器 (AI 作曲管线，通过 stdio 通信)
npm run build --prefix ts-orchestrator
node ts-orchestrator/dist/index.js

# 启动 Web UI (数据集管理 + 声音训练)
python -m cantiodaw serve
# 打开 http://127.0.0.1:8080
```

## TS 编排层 — 70 个工具

编排层作为 MCP 服务器运行在 stdio 上，暴露 70 个工具（57 DAW/MIDI + 13 LLM），覆盖项目管理、音乐生成、分析和导出。所有工具标注了分类标签：`[生成]` / `[评价]` / `[执行]` / `[编排]`。

### 工程与音轨工具 (9)

| 工具 | 分类 | 说明 |
|------|------|------|
| `project_create` | `[执行]` | 创建新工程 |
| `project_list` | `[执行]` | 列出所有工程 |
| `project_load` | `[执行]` | 加载工程详情 |
| `project_delete` | `[执行]` | 删除工程 |
| `project_export` | `[执行]` | 导出工程为音频 |
| `track_add` | `[执行]` | 添加音频/MIDI 音轨 |
| `track_remove` | `[执行]` | 删除音轨 |
| `track_update` | `[执行]` | 更新音轨属性 (音量/静音/名称) |
| `track_add_clip` | `[执行]` | 为音轨添加片段 (MIDI音符/和弦/音频引用) |

### MIDI 与合成工具 (6)

| 工具 | 分类 | 说明 |
|------|------|------|
| `midi_notes_to_f0` | `[执行]` | 将 MIDI 音符转换为 F0 基频曲线 |
| `midi_lyrics_to_phonemes` | `[执行]` | 将歌词文本转换为音素 |
| `synthesize` | `[生成]` | 从 MIDI + 模型合成歌声 |
| `synthesize_midi` | `[生成]` | 通过 SoundFont 或振荡器降级合成多轨编曲 |
| `list_soundfonts` | `[执行]` | 列出可用的 SoundFont (.sf2/.sf3) 文件及乐器 |
| `download_soundfont` | `[执行]` | 下载 FluidR3_GM.sf2 (144 MB) 用于真实乐器合成 |

### 音频处理工具 (3)

| 工具 | 分类 | 说明 |
|------|------|------|
| `effect_apply` | `[执行]` | 应用音频效果 (混响/EQ/压缩) |
| `mix_tracks` | `[执行]` | 混音多条音轨 (MIDI 轨自动通过 SoundFont 合成) |
| `export_stems` | `[执行]` | 按轨导出独立音频分轨 |

### 声音训练工具 (3)

| 工具 | 分类 | 说明 |
|------|------|------|
| `train_prepare` | `[执行]` | 从音频目录准备声音数据集 |
| `train_start` | `[执行]` | 启动声音模型训练 |
| `train_voice_from_audio` | `[执行]` | 完整流程：准备 → 训练声音模型 |

### 编排工具 (4)

| 工具 | 分类 | 说明 |
|------|------|------|
| `compose_song` | `[生成]` | 端到端：创建工程 → 加轨 → 合成 |
| `apply_voice_to_midi` | `[执行]` | 将声音模型应用于 MIDI 音符 → 歌声音频 |
| `revision_execute` | `[编排]` | Critic→修正→重检 收敛循环 (有界迭代) |
| `parameter_reference` | `[执行]` | 查询物理参数映射 (MIDI CC→DAW, 乐器→GM音色号) |

### 参数调整工具 (7)

| 工具 | 分类 | 说明 |
|------|------|------|
| `adjust_dynamics` | `[执行]` | 调整音轨段落动态曲线 |
| `adjust_articulation` | `[执行]` | 调整演奏法 (连奏/断奏) 与起音 |
| `adjust_vibrato` | `[执行]` | 调整颤音深度与速率 |
| `adjust_micro_timing` | `[执行]` | 调整逐音微时间偏移 |
| `adjust_harmonic_color` | `[执行]` | 调整和声色彩/调式偏移 |
| `apply_swing` | `[执行]` | 为音轨添加摇摆感 |
| `apply_rubato` | `[执行]` | 应用 tempo rubato 速度曲线 |

### 版本管理工具 (4)

| 工具 | 分类 | 说明 |
|------|------|------|
| `project_snapshot` | `[执行]` | 创建版本快照 |
| `diff_versions` | `[执行]` | 对比两个工程版本 (仅显示变化的音轨) |
| `rollback_to_version` | `[执行]` | 回滚到指定版本 |
| `list_versions` | `[执行]` | 列出所有版本快照 (磁盘+内存合并) |

### 渲染工具 (2)

| 工具 | 分类 | 说明 |
|------|------|------|
| `render_preview` | `[执行]` | 快速低质量预览渲染 (MIDI 轨自动合成) |
| `render_final` | `[执行]` | 全质量最终渲染 (MIDI 轨自动合成) |

### 偏好反馈工具 (5)

| 工具 | 分类 | 说明 |
|------|------|------|
| `feedback_submit` | `[执行]` | 提交用户评分 (1-5) 关联到版本 |
| `feedback_ab_test` | `[执行]` | 提交 A/B 对比偏好 |
| `list_feedback` | `[执行]` | 列出所有反馈 (评分/AB测试/采纳率/重听次数/收藏) |
| `track_replay` | `[执行]` | 记录版本重听事件 |
| `track_favorite` | `[执行]` | 记录/切换版本收藏状态 |

### 评价分析工具 (6)

| 工具 | 分类 | 说明 |
|------|------|------|
| `analyze_harmony` | `[评价]` | 和声功能分析、张力曲线 |
| `analyze_melody` | `[评价]` | 动机检测、轮廓/音程分析 |
| `analyze_rhythm` | `[评价]` | Groove、密度、稳定性分析 |
| `analyze_audio` | `[评价]` | 频谱、动态、空间分析 |
| `analyze_vocal_quality` | `[评价]` | 音准偏差、电音伪影、断音检测 |
| `adjust_synthesized_pitch` | `[执行]` | 对已合成音频进行局部音准修正 |

### LLM 工具 (13)

| 工具 | 分类 | 用途 |
|------|------|------|
| `llm_chat` | `[执行]` | 通用 LLM 对话 (自动路由) |
| `llm_stream` | `[执行]` | 流式 LLM 对话 |
| `llm_generate_lyrics` | `[生成]` | 歌词生成 |
| `llm_compose_song` | `[生成]` | 端到端歌曲创作 (含合成) |
| `llm_suggest_arrangement` | `[编排]` | 编曲建议 |
| `llm_analyze_lyrics` | `[评价]` | 歌词分析 (情感/主题) |
| `llm_compose_music` | `[生成]` | 从描述直接生成 MIDI 音乐 |
| `llm_list_providers` | `[执行]` | LLM 提供商列表 |
| `llm_list_models` | `[执行]` | 模型列表 |
| `llm_usage_stats` | `[执行]` | 用量统计 (跨重启持久化) |
| `llm_parse_intent` | `[编排]` | NL → Music Semantic IR |
| `llm_query_knowledge_graph` | `[编排]` | 知识图谱概念 → 参数映射查询 |
| `llm_compose_from_intent` | `[生成]` | IR → 编曲方案 + MIDI 音符 |
| `llm_analyze_music` | `[评价]` | 多领域音乐评价 (聚合全部 4 个模块) |
| `llm_request_checkpoint` | `[执行]` | 人工检查点请求 (强制/可选) |

## Music Semantic IR

自然语言与音乐参数之间的核心中间表示：

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

11 个音乐表达概念映射为参数增量 (YAML 定义)：

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

## 参数映射参考

为 AI Agent 提供物理参数参考——通过 `parameter_reference` 工具查询：

```python
from cantiodaw.music.parameter_mapping import (
    MIDI_CC_MAP,           # MIDI CC → DAW 工具映射 (10 个标准 CC)
    INSTRUMENT_TO_PROGRAM, # 乐器名 → GM 音色号 (80+ 乐器)
    PARAMETER_REFERENCE,   # adjust_* 工具参数物理含义参考
    resolve_instrument,    # 解析名称到音色号: "violin" → 40
)
```

## SoundFont 真实乐器合成

MIDI 音轨可通过 SoundFont (.sf2/.sf3) 文件经由 FluidSynth 渲染真实乐器音色，并具备自动振荡器降级：

```python
from cantiodaw.synthesis.soundfont import SoundFontSynth

# 自动从 data/soundfonts/ 检测 SoundFont 文件
synth = SoundFontSynth.create()

# 按 GM 音色号渲染 MIDI 音符 (0=钢琴, 40=小提琴, 48=弦乐)
audio = synth.render(notes, tempo=120, program=0)

# 检查 FluidSynth 是否可用
print(synth.available)  # True=pyfluidsynth 已加载, False=振荡器降级
```

SoundFont 支持：
- **FluidSynth 路径**：安装 `pyfluidsynth` + FluidSynth 原生库 → 真实乐器渲染
- **振荡器降级**：FluidSynth 不可用时自动切换到正弦/三角/锯齿波
- **自动下载**：`download_soundfont` 工具 → FluidR3_GM.sf2 (144 MB, 128 GM 乐器)
- **逐片段音色**：每个 MIDI 片段可独立指定 GM 音色号

## Critic 系统 (5 个分析模块)

| 模块 | 分析范围 | 诊断示例 |
|------|----------|----------|
| **和声** | 和弦功能分布 (T/SD/D)、不协和曲线、解决率 | "过渡段张力不够" |
| **旋律** | 动机重复、轮廓变化、音域分布、音程特征 | "大跳过于频繁" |
| **节奏** | 摇摆量、音符密度、速度稳定性、强拍锁定 | "切分密度过高" |
| **音频** | RMS 能量曲线、频谱亮度、峰值因子、立体声宽度 | "高频亮度不足" |
| **人声** | 音准偏差 vs 目标 MIDI、电音/机械伪影、断音次数 | "平均音准偏差 68 cents — 跑调" |

> **关于 `llm_analyze_music`**：此 LLM 工具对基于规则的评价输出提供**补充解释**，而非替代评价路径。工作流程为：规则评价器 (和声/旋律/节奏/音频/人声) 产出结构化数值诊断 → `llm_analyze_music` 读取这些诊断并生成自然语言的修正建议。规则评价的分数决定严重程度和优先级；LLM 添加上下文解读。如果 LLM 与评价器诊断结果有分歧，以规则评价分数为准 (除非被人类判断覆盖)。

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
| `compose_song` | 创建工程 → 加音轨 → 音素 → 合成 → 导出 |
| `train_voice` | 准备数据集 → 训练模型 |
| `apply_voice` | 转换歌词 → F0 轮廓 → 合成 |
| `mix_export` | 混音 → 导出分轨 |
| `compose_from_intent` | 解析 NL 意图 → 从 IR 作曲 → MIDI 预览 |
| `critic_revise` | 快照 → 修正循环 (自动分析→修正→重检) → 快照 → 预览 |
| `full_pipeline` | NL → IR → 作曲 → 评价 → 修正 (自动循环) → 对比 → 最终导出 |

```bash
node ts-orchestrator/dist/index.js worklist
```

## 端到端场景

### NL → MIDI
```
输入: "一段宁静的钢琴曲"
→ llm_parse_intent → MusicIR
→ llm_compose_from_intent → 含 MIDI 音符的编曲方案
→ export_midi → .mid 文件 (导入 DAW 配合 VST 播放)
```

### 评价闭环
```
生成的 MIDI → analyze_harmony + analyze_melody
→ Critic 发现 ≥1 个问题 → 生成修正建议
```

### 自修正
```
生成 → Critic → revision_execute (自动循环: 分析→修正→重检) → 预览
→ 收敛控制迭代 (最多 5 轮, 阈值 0.8)
```

### 全流程
```
"凌晨三点开车…孤独但希望"
→ 自动作曲 → 自动评价 → 自动修正 (收敛循环) → 最终导出
→ 人类反馈收集 (评分、收藏、重听)
```

## 收敛控制 (修正循环)

`revision_execute` 工具自动运行 critic→修正→重检 循环：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 最大迭代次数 | 5 | 达到此上限后强制停止 |
| 质量阈值 | 0.8 (严重度) | 平均严重度低于阈值时提前终止 |
| 无改善上限 | 3 连续轮次 | 连续指定轮次无改善时停止 |
| 重检 | 每轮迭代 | 每次修正后重新运行全部 critic 并对比 |

当循环停止但未收敛时：
- 若设置了 `request_checkpoint` (type=`mandatory`)，暂停等待人工决策
- 否则输出**当前最佳版本**

## 偏好反馈

采集的数据流经以下路径：

```
用户评分 (1-5) / A/B 对比 / 重听 / 收藏
         ↓
PreferenceCollector  →  JSONL 存储 (feedback.jsonl / abtest.jsonl / replays.jsonl / favorites.jsonl)
         ↓
list_feedback  →  返回全部数据 (评分、AB 测试、重听次数、收藏状态)
         ↓
PreferenceModel.train(samples)  →  学习特征权重
         ↓
PreferenceModel.adjust_critic_score(critic_score, features)
         ↓
加权分数用于 Revision Agent 的收敛检查
```

## DAW 协作

CantioDAW 生成结构化 MIDI —— DAW 完成其余工作：

```
CantioDAW                                 DAW (Ableton / REAPER / FL Studio / Logic)
──────────                                ───────────────────────────────────────────
NL 描述 → AI 编曲方案
       ↓
生成 .mid (多轨)
       ↓                                         导入 .mid 文件
(可选) 运行 Critic → 修正循环                      分配 VST 乐器
       ↓                                         编辑 MIDI 音符、量化
迭代直到满意                                      录制真实声部、混音、FX
       ↓                                         Mastering → 最终导出
导出 .mid ──────────────────────────►
```

### 场景 1：灵感启航

```
你: "一段 cinematic 管弦乐，紧张→恢弘"
CantioDAW: 包含 7 段结构的 .mid 文件
DAW: 打开 .mid → 加载 BBCSO/Spitfire → 立刻试听
     满意？保留。不满意？改提示词，重新生成。
```

### 场景 2：迭代编曲

```
1. 运行 full_pipeline: 作曲 → critic → revision_execute (自动循环) → 导出 .mid
2. DAW 中打开试听
3. 某段和声进行不满意：
   - 方案 A: 调整提示词，只重新生成该段落
   - 方案 B: DAW 中直接编辑 MIDI，保留其他部分
4. 重复直到结构满意
```

### 场景 3：歌声合成前端

```
1. CantioDAW 作曲 + 生成歌词音素
2. synthesize → 原始人声 WAV 分轨
3. 将人声分轨导入 DAW 作为音频轨
4. 在 DAW 中围绕人声构建伴奏
5. 使用 adjust_synthesized_pitch 进行音准修正 (无需重训练)
```

### 场景 4：分析助手

```
DAW: 导出你完成的 MIDI 编曲
CantioDAW: 运行 analyze_harmony / analyze_melody / analyze_rhythm
           → "Bridge 段落: 属和弦占比过低 (12%)"
           → "旋律: 第 17-20 小节大跳过于频繁"
DAW: 回到 DAW 中针对性地修改
```

### 分工总结

| CantioDAW (离线) | DAW (实时) |
|-------------------|------------|
| NL → 结构化编曲 | VST 乐器播放 |
| 多轨 MIDI 生成 | 音频录制与编辑 |
| 和声/旋律/节奏/音频/人声分析 | 混音、FX、母带 |
| 歌声合成 (原始 WAV) | 编曲精细调整 |
| 版本 diff 与回滚 | 现场演奏 |
| SoundFont 真实乐器渲染 | |

## CLI 用法

```bash
# 创建工程
cantiodaw project create --name MySong

# 训练声音模型
cantiodaw train --voice MyVoice --data-dir data/voices/my_voice --epochs 50

# 使用自动检测格式合成
cantiodaw synthesize --model checkpoints/MyVoice/best_model.safetensors \
  --config config.yaml --pitch 60 --duration 2.0 -o output.wav

# 检测模型格式
cantiodaw detect --model so-vits-svc/G_10000.pth
```

## 输出格式

| 格式 | 来源 | 用途 |
|------|------|------|
| **MIDI** (`.mid`) | Composer Agent → `export_midi` | 多轨编曲。导入 DAW 配合 VST 乐器播放 |
| **WAV — SoundFont** (`.wav`) | `synthesize_midi` via FluidSynth | 真实乐器音色 (需 pyfluidsynth + .sf2) |
| **WAV — 合成预览** (`.wav`) | `synthesize_midi` 振荡器降级 | 基本波形快速试听 (无 SoundFont 时) |
| **WAV — 神经 SVC** (`.wav`) | `synthesize` with 已训练模型 | 神经声码器歌声输出 (质量依赖模型训练) |
| **JSON** | Critics, IR, 版本 diff, 反馈工具 | 分析结果、IR 数据、版本对比、偏好记录 |

## 环境变量

```
CANTIODAW_PYTHON    Python 可执行文件路径 (默认: python)
CANTIODAW_ROOT      CantioDAW 项目根目录 (默认: 上级目录)
OLLAMA_API_KEY      Ollama Cloud API key
OLLAMA_MODEL        Ollama 模型名称 (默认: gemma4:31b)
OPENAI_API_KEY      OpenAI API key (可选)
```

## 支持的模型格式 (歌声合成)

| 格式 | 检测方式 | 配置 |
|------|----------|------|
| **CantioDAW HybridSVC** (.safetensors/.pt) | `phoneme_feature_dim` / `spectral_envelope_dim` | `config.yaml` |
| **so-vits-svc** (.pth) | `inter_channels` / `filter_channels` / `n_heads` | `config.json` |
| **RVC v1** (.pth, 256-dim) | `generator.` / `emb_g` keys | `config.json` |
| **RVC v2** (.pth, 768-dim) | `generator.` / `dec.4` / `794` keys | `config.json` |

## 系统要求

- Python 3.9+, PyTorch 2.0+, Node.js 18+
- `pip install -e .` 安装 Python 包
- `npm install` (在 `ts-orchestrator/` 目录) 安装 TypeScript 依赖
- 可选: `pip install pyfluidsynth` 启用 SoundFont 真实乐器合成

## 项目结构

```
cantiodaw/
├── music/                     # Music IR, Knowledge Graph, Parameter Mapping
│   ├── ir.py                 # MusicIR 数据结构 (Python 真理源)
│   ├── knowledge_graph.py    # 知识图谱查询引擎
│   ├── knowledge_graph.yaml  # 11 个概念节点
│   ├── parameter_mapper.py   # 情绪 → 参数映射表
│   ├── parameter_mapping.py  # MIDI CC→DAW, 乐器→GM, adjust_* 参考
│   └── labels.py             # 情绪/场景/风格标签体系
├── critic/                    # 5 模块音乐分析
│   ├── harmony.py            # 和弦功能、张力曲线
│   ├── melody.py             # 动机检测、音程分析
│   ├── rhythm.py             # Groove、密度、稳定性
│   ├── audio.py              # 频谱、动态、空间分析
│   └── vocal.py              # 音准偏差、电音伪影、断音
├── synthesis/                 # 音频合成
│   ├── svs_engine.py         # 歌声合成引擎
│   ├── lyrics_aligner.py     # 歌词-音素对齐
│   ├── soundfont.py          # SoundFontSynth (FluidSynth + 振荡器降级)
│   └── sf2_download.py       # FluidR3_GM.sf2 自动下载
├── preference/                # 人类反馈学习
│   ├── collector.py          # 评分、A/B、采纳、重听、收藏记录
│   └── model.py              # 偏好加权模型
├── versioning/                # 工程版本管理
│   └── version.py            # 快照、diff、回滚 (磁盘+内存)
└── config.yaml               # 工程配置 (路径、合成、训练、WebUI)

ts-orchestrator/
├── src/
│   ├── mcp/tools.ts          # 57 个 DAW/MIDI 工具定义
│   ├── llm/tools.ts          # 13 个 LLM 工具定义
│   ├── llm/prompts/          # Intent 解析器 + Composer prompts
│   ├── music/ir.ts           # TypeScript MusicIR 镜像 + 标签
│   ├── orchestrator/
│   │   ├── composer.ts       # Composer Agent (IR → 编曲)
│   │   ├── revision.ts       # Revision Agent (优先级排序 + 修正)
│   │   ├── workflows.ts      # 7 个预定义工作流
│   │   └── engine.ts         # 工作流执行引擎
│   └── bridge/               # Python ↔ TypeScript 桥接 (stdio JSON-RPC)
```

## 局限性

- **非实时 DAW** — 全部为离线/批处理。不替代 Ableton、REAPER、FL Studio 等软件的实时录音、混音或现场制作。
- **WAV 合成有多个质量层级**: SoundFont (FluidSynth + .sf2 = 真实乐器) > 神经 SVC (依赖训练模型) > 振荡器 (基本波形预览)。
- **依赖 LLM 的作曲** — 编曲质量因模型和提示词而异，结果需人工审阅和编辑。
- **研究级** — 适用于 AI 驱动的作曲与歌声合成实验，不适合直接用于商业音乐制作。

## 许可证

Apache 2.0
