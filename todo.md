# CantioDAW · AI Agent 编曲系统

> 构建由 AI Agent 控制的自动编曲系统，基于 CantioDAW 现有代码（ts-orchestrator 56 个 MCP 工具 + Python 核心管线）。

## 核心架构

```
自然语言
   ↓
┌─────────────────────────────┐
│  Intent Agent               │  阶段 2
│  (NL → Music Semantic IR)   │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Composer Agent             │  阶段 3
│  (IR → 曲式/旋律/和声/配器)  │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Parameter Agent            │  阶段 4
│  (IR → Parameter Delta)     │
└─────────────┬───────────────┘
              ↓
      MIDI / DAW Control      ← 现有 41 个 DAW 工具
              ↓
┌─────────────────────────────┐
│  Critic Agent (4 个子系统)  │  阶段 5
│  Harmony / Melody / Rhythm  │
│  / Audio                    │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│  Revision Agent             │  阶段 6
│  (诊断 → 修改计划 → 执行)   │
└─────────────┬───────────────┘
              ↓
          优化闭环             ← 阶段 7 收敛控制
              ↓
      Human Preference        ← 阶段 8 人类反馈学习
```

## 核心原则

1. **不直接生成最终音频** — 所有修改通过参数 delta 作用于已有作品
2. **中间表示 (Music IR)** — 情绪/场景/能量在独立维度表达，不直接映射到参数
3. **增量修改** — 所有工具接受相对值（`+15%`、`delta_cents=40`）
4. **Agent 分治** — 意图、作曲、参数、评价、修订各司其职

---

## 阶段 0：现状盘点（先做，别跳）

- [ ] 把现有工具逐一列出清单：工具名、输入 schema、输出 schema、是否有副作用（修改项目状态 vs 纯查询）
- [ ] 给每个工具打分类标签：`生成类` / `评价类` / `执行类` / `编排类`
- [ ] 标出哪些工具目前是"黑盒"（一次调用做一整套事情）
- [ ] 确认 DAW 工具和 LLM 工具之间的共享状态关系

**代码位置**：`ts-orchestrator/src/mcp/tools.ts` + `src/llm/tools.ts`

---

## 阶段 1：Music Semantic IR（核心中间表示）

建立类似 LLVM IR 的音乐中间层，使意图→参数映射可逆、可组合、可查询。

### 1.1 定义 IR 数据结构

```typescript
// cantiodaw/music/ir.ts
interface MusicIR {
  emotion: EmotionVector;        // 多维情绪 (loneliness: 0.8, hope: 0.6)
  energy: EnergyCurve;           // 能量起点→终点
  style: StyleVector;            // 风格标签 (cinematic: 0.8, electronic: 0.6)
  scene: SceneTags;              // 场景标签 (night, urban, driving)
  arrangement: ArrangementSpec;  // 编曲密度、乐器焦点
  structure: StructurePlan;      // 曲式结构
}
```

- [x] 定义 `EmotionVector` schema（孤独/希望/怀旧/紧张/平静… 可控维数）
- [x] 定义 `EnergyCurve` schema（起点/终点/峰值/谷值/曲线形状）
- [x] 定义 `StyleVector` schema（cinematic / electronic / orchestral / pop / ambient…）
- [x] 定义 `SceneTags` schema（night / urban / driving / rain / morning / forest…）
- [x] 定义 `ArrangementSpec` schema（density / instrument_focus / texture）
- [x] 定义 `StructurePlan` schema（section 列表 + 每段的 IR 引用）

**代码位置**：`cantiodaw/music/ir.py` + `ts-orchestrator/src/music/ir.ts`（双向同步，Python 侧是真理源）

---

## 阶段 2：Agent 角色体系

### 2.1 确定 Agent 分工

| Agent | 职责 | 代码位置 |
|-------|------|---------|
| **Intent Agent** | NL → Music Semantic IR（理解情绪/场景/能量需求） | `ts-orchestrator/src/llm/tools.ts` → `llm_parse_intent` |
| **Composer Agent** | IR → 曲式结构/旋律设计/和声规划/乐器选择 | `ts-orchestrator/src/orchestrator/composer.ts` |
| **Parameter Agent** | IR → 参数 delta（调用具体 adjust_* 工具） | `cantiodaw/music/parameter_mapper.py` |
| **Critic Agent** | 分析生成结果 → 发现多维度问题 | 见阶段 6 |
| **Revision Agent** | 解析 critic 输出 → 生成修改计划 → 执行 | `ts-orchestrator/src/orchestrator/revision.ts` |

### 2.2 Intent Agent — 意图解析系统

用户输入 → `MusicIR`：

```typescript
// "凌晨三点开车，一个人在城市里，很孤独但最后看到希望"
→ {
  emotion: { loneliness: 0.8, hope: 0.6, nostalgia: 0.7 },
  scene: ["night", "urban", "driving"],
  energy_curve: { start: 0.2, end: 0.8, growth: 0.7 },
  style: { cinematic: 0.8, ambient: 0.6 }
}
```

- [x] 设计 `llm_parse_intent` 的 prompt 模板（基于现有 LLM router，复用 `gemma4:31b`）
- [x] 建立意图分类标签体系（推荐：音乐描述分为"情绪/场景/能量/风格/对比"5 类）
- [x] 建立情绪标签体系（先定 10 个核心情绪，后续可扩展）
- [x] 建立场景标签体系（night / urban / rain / forest / morning / …）
- [x] 建立风格标签体系（cinematic / electronic / orchestral / pop / ambient / …）
- [x] 增量意图：用户说"再悲伤一点" → 在原 IR 上做 `emotion.sadness += 0.2`
- [x] 在 MCP 暴露 `llm_parse_intent` 工具

**代码位置**：
- Prompt 模板：`ts-orchestrator/src/llm/prompts/intent_parser.ts`
- 工具：`ts-orchestrator/src/llm/tools.ts`
- 标签体系：`ts-orchestrator/src/music/labels.ts`

### 2.3 Composer Agent — 作曲编排

接收 `MusicIR`，输出编曲方案：

- [x] 曲式结构生成（Intro → Verse → Chorus → Bridge → Outro）
- [x] 和声规划（调式/和弦进行，基于 emotion 维度和 style 标签）
- [x] 旋律设计（音高轮廓/节奏型/动机发展）
- [x] 乐器选择与配器（基于 style 标签 + arrangement density）
- [x] 整合为可直接执行的"编曲计划"（每个乐器的 MIDI Note 生成方案）
- [x] 暴露 `llm_compose_from_intent` 工具

**代码位置**：`ts-orchestrator/src/orchestrator/composer.ts`

---

## 阶段 3：Music Knowledge Graph

建立双向可查询的知识图谱，使"提高紧张感 → 查所有可调整参数"成为可能。

### 3.1 图谱结构

```
紧张
  ├── Harmony
  │   ├── dissonance ↑
  │   ├── dominant_chord ↑
  │   └── resolution ↓
  ├── Rhythm
  │   ├── syncopation ↑
  │   ├── BPM ↑
  │   └── density ↑
  ├── Sound
  │   ├── distortion ↑
  │   ├── brightness ↑
  │   └── reverb ↓
  └── Dynamics
      ├── compression ↑
      └── contrast ↑
```

### 3.2 实现形式

规则库存储为外部可加载 JSON/YAML（非硬编码）：

```yaml
# cantiodaw/music/knowledge_graph.yaml
nodes:
  - id: tension
    label: "紧张感"
    affects:
      - target: harmony.dissonance
        delta: +0.3
      - target: harmony.dominant_frequency
        delta: +0.4
      - target: rhythm.syncopation
        delta: +0.3
      - target: sound.brightness
        delta: +0.2
      - target: mix.compression
        delta: +0.2
    inverse: # "降低紧张感"用相反值
      - target: harmony.dissonance
        delta: -0.3
      - target: harmony.resolution
        delta: +0.3
```

- [x] 设计节点 schema（id / label / affects / inverse / related）
- [x] 建立核心节点（10-15 个音乐表达概念）
- [x] 实现 `query_graph(concept, direction?) → ParameterDelta[]`
- [x] 实现反向查询 `reverse_query(target_param) → Concept[]`
- [x] 图谱作为外部 YAML 文件加载，允许用户自定义
- [x] 暴露 `llm_query_knowledge_graph` 工具

**代码位置**：`cantiodaw/music/knowledge_graph.py` + `cantiodaw/music/knowledge_graph.yaml`

---

## 阶段 4：Parameter Mapping Engine（参数增量系统）

将 Music IR + Knowledge Graph 输出转化为实际工具参数。

### 4.1 核心原则

- **不使用绝对值**：全部为 delta 相对值
  - 正确：`tempo += 15%`
  - 错误：`tempo = 120`
- **支持链式叠加**：多个意图叠加时参数线性叠加
- **有界约束**：每个参数有 `[min, max]`，防止溢出

### 4.2 映射规则

```typescript
// emotion → harmony
"loneliness" → minor_ratio: +0.4, suspension_ratio: +0.3
"hope" → ascending_contour: +0.5, resolution: +0.6

// emotion → arrangement  
"sadness" → density: -0.3, reverb: +0.4, brightness: -0.3
```

- [x] 建立 `emotion → harmony` 映射表
- [x] 建立 `emotion → melody` 映射表（轮廓/音程偏好/方向）
- [x] 建立 `emotion → rhythm` 映射表（密度/切分/速度）
- [x] 建立 `emotion → instrument` 映射表（音色/音区/织体）
- [x] 建立 `emotion → mix` 映射表（混响/压缩/均衡）
- [x] 映射输出为 `ParameterDelta[]`，直接对应阶段 3 的原子工具参数

**代码位置**：`cantiodaw/music/parameter_mapper.py`

### 4.3 DAW/MIDI 参数映射

- [ ] MIDI 参数映射（CC/velocity/note offset → 物理参数）
- [ ] DAW 参数映射（现有 adjust_* 工具的 delta 化改造）
- [ ] 乐器参数映射（音色库特定参数）

---

## 阶段 5：工具粒度拆分 & 原子工具改造

### 5.1 参数增量化改造

所有现有和新增的 adjust_* 工具的参数必须统一为 delta 语义：

- [x] `adjust_pitch(track_id, start, end, delta_cents)` — **已有**
- [x] `adjust_timing(track_id, start, end, offset_delta_ms)` — **已有**
- [x] `adjust_volume(track_id, start, end, delta_db)` — **已有**
- [x] `adjust_dynamics(track_id, section, curve_delta)` — 新增
- [x] `adjust_articulation(track_id, start, end, style, overlap_delta, attack_delta_ms)` — 新增
- [x] `adjust_vibrato(track_id, start, end, depth_delta, rate_delta)` — 新增
- [x] `adjust_micro_timing(track_id, adjustments: [{note_index, offset_delta_ms}])` — 新增
- [x] `adjust_harmonic_color(section, quality_delta, mode_shift)` — 新增
- [x] `apply_swing(track_id, ratio)` — 新增
- [x] `apply_rubato(track_id, curve: [{beat, tempo_factor}])` — 新增

### 5.2 工具标注

- [ ] 审计阶段 0 标出的"黑盒"工具，逐个拆成原子操作
- [ ] 工具 description 标注四类分工：`生成` / `评价` / `执行` / `编排`
- [ ] 补充前置/后置条件说明

---

## 阶段 6：音乐 Critic 系统（4 个子系统）

解决 Agent 无法"听"的问题。

### 6.1 Harmony Critic

- [x] 和弦功能分析（Tonic / Subdominant / Dominant 分布）
- [x] 张力曲线分析（dissonance 密度随时间变化）
- [x] 解决感评分（V→I 占比，延迟解决次数）
- [x] 离调程度评分

### 6.2 Melody Critic

- [x] 动机重复检测（相似音程序列匹配）
- [x] 旋律发展分析（contour variety / interval variety）
- [x] 音域分布（过低/过高/最适音域占比）
- [x] 音程分布分析（大小跳比例）

### 6.3 Rhythm Critic

- [x] Groove 分析（摇摆量/微时间偏差模式）
- [x] 密度分析（note density / rest ratio 时间序列）
- [x] 稳定性分析（速度波动 / downlock 稳定性）

### 6.4 Audio Critic

- [x] 能量曲线分析（RMS 随时间变化 vs 期望 IR）
- [x] 频谱分析（高频亮度 / 低频密度 / 中频清晰度）
- [x] 动态范围分析（crest factor / loudness range）
- [x] 空间分析（stereo width / reverb tail）

### 6.5 统一输出格式

```json
{
  "domain": "harmony",
  "problem": "过渡段张力不够",
  "severity": 0.6,
  "diagnosis": [
    "dominant 和弦占比过低 (12%)",
    "dissonance 峰值未达到前半水平"
  ],
  "suggestions": [
    { "action": "adjust_harmonic_color", "params": {"section": "bridge", "quality_delta": "+dominant"} },
    { "action": "adjust_dynamics", "params": {"section": "bridge", "curve_delta": "+0.2"} }
  ]
}
```

- [ ] MIDI 分析器（基于 music21 / 自建分析引擎）
- [ ] Audio Feature Extractor（复用现有 librosa/pyworld 能力）
- [x] 分数向量输出（每个维度 0-1 标准化评分）
- [x] 自动诊断生成（基于规则的问题→建议映射）

**代码位置**：`cantiodaw/critic/harmony.py` / `melody.py` / `rhythm.py` / `audio.py`
- 每个 critic 作为独立 MCP 工具暴露
- 聚合 `analyze_music(track_id, domains?: [])` 工具一键调用全部

---

## 阶段 7：项目状态化管理

- [x] 为 project / track 设计唯一 ID 体系
- [x] 所有工具的输入输出改为引用 ID，而非直接传原始波形
- [x] 实现版本快照机制：每次修改自动生成一个版本
- [x] 新增 `diff_versions(project_id, v1, v2)` 工具
- [x] 新增 `rollback_to_version(project_id, version)` 工具
- [x] 新增 `list_versions` 工具

---

## 阶段 8：优化闭环 & Revision Agent

### 8.1 Revision Agent

- [x] 解析 Critic 输出 → 生成修改优先级列表
- [x] 自动选择优化方向（优先修最高 severity 问题）
- [x] 调用对应 adjust_* 工具执行修改
- [ ] 修改后自动重跑 critic 验证

**代码位置**：`ts-orchestrator/src/orchestrator/revision.ts`

### 8.2 收敛控制

- [x] 为迭代循环设定上限（单片段最多 5 轮）
- [x] 设定质量阈值：critic 评分达标即停止
- [x] "连续 N 轮无改善则停止并上报"规则
- [x] 每轮迭代前后自动 `diff_versions`，倒退则回滚

### 8.3 双速渲染

- [x] `render_preview`：低采样率/简化路径，几秒内出结果
- [x] `render_final`：确认满意后走完整质量渲染
- [x] 两者接口一致，agent 只传 `"preview"`/`"final"` 参数

---

## 阶段 9：人类反馈学习

### 9.1 数据采集

- [x] 用户评分接口（1-5 分，关联到版本 ID）
- [x] A/B 测试支持（两个版本并排对比，用户选择偏好）
- [ ] 重听/收藏行为记录
- [x] 修改采纳率跟踪（用户接受/拒绝了哪些 critic 建议）

### 9.2 偏好模型

- [x] 数据标注格式定义
- [x] Reward Model 训练（基于用户反馈数据）
- [x] 偏好模型集成到收敛控制（critic 评分中加入偏好加权）

**代码位置**：`cantiodaw/preference/collector.py` + `cantiodaw/preference/model.py`

---

## 阶段 10：人工检查点

- [x] 设计 `request_checkpoint` 工具（`llm_request_checkpoint`）
- [x] checkpoint 返回当前 vs 上一版本的关键指标对比
- [ ] 明确强制/可选 checkpoint 节点

---

## 阶段 11：模型格式配套

- [ ] 评估接入 Applio/DDSP-SVC/Diffusion-SVC 格式
- [ ] 格式检测失败时给出明确诊断信息
- [ ] 搭建 A/B 音质验证集
- [ ] 决策实时音频引擎 vs 离线批处理定位

---

## 阶段 12：SF2 + FluidSynth 真实乐器合成

### 12.1 基础设施 — SoundFontSynth 引擎

- [ ] 新建 `cantiodaw/synthesis/soundfont.py` — SoundFontSynth 封装类
- [ ] `render(notes, tempo, program, bank) → np.ndarray` 批量渲染
- [ ] `list_instruments()` 枚举音色库可用乐器
- [ ] `pip install pyfluidsynth` 添加到 `pyproject.toml` 依赖
- [ ] `config.yaml` 加 `paths.soundfonts_dir`
- [ ] 默认 SF2 自动查找逻辑（`data/soundfonts/` → 振荡器降级）

### 12.2 替换 `synthesize_midi` 路径

- [ ] `python_bridge.py` 改造：传 `soundfont_path`/`program`/`bank` → SoundFontSynth，无参数时降级振荡器
- [ ] `tools.ts` `synthesizeMIDI` 加 soundfont/program/bank 参数
- [ ] 保留振荡器 fallback：`pyfluidsynth` 不可用或不传 path 时走老路

### 12.3 接入混音/渲染管线

- [ ] `_mix_project` 共享函数改造：MIDI 轨道 → SoundFontSynth → 混入 mixer
- [ ] `mix_tracks`/`render_preview`/`render_final` 加可选 `soundfont_path` 参数
- [ ] MIDI 轨道 clip 支持独立 `program`，同一轨道不同 clip 可用不同乐器

### 12.4 默认音色库部署

- [ ] 集成 FluidR3_GM.sf2 自动下载工具
- [ ] 验证：`synthesize_midi` 出真实乐器 → `mix_tracks` 混入 → `render_preview` 输出 WAV
- [ ] 多乐器编排验证：钢琴 + 弦乐 + 贝斯 三条 MIDI 轨并行渲染

---

## MVP 开发顺序

### 第一阶段（目标：NL → MIDI）

- [x] 阶段 0 现状盘点完成 — 实际代码远超 29 个工具（56 个），但正式的审计文档未写
- [x] Music Semantic IR 定义完成（至少包含 emotion + energy + style）
- [x] `llm_parse_intent` 实现并暴露（Intent Agent 最小版本）
- [x] 基础 `llm_compose_from_intent` 实现（Composer Agent 最小版本）
- [ ] 验证：输入"一段宁静的钢琴曲" → 产出可播放 MIDI

### 第二阶段（目标：评价闭环）

- [x] Harmony Critic 最小版本（和弦功能分析 + 张力曲线）
- [x] Melody Critic 最小版本（动机重复检测 + 音域分析）
- [x] Critic 统一输出格式实现
- [ ] 验证：generated MIDI → critic → 发现至少一个问题

### 第三阶段（目标：自修正闭环）

- [x] Revision Agent 实现
- [x] 收敛控制实现（上限 + 阈值 + 回滚）
- [x] `render_preview` 实现
- [ ] 验证：Generate → Critic → Revise → Preview 完整闭环跑通

### 第四阶段（目标：全流程）

- [x] 全部 4 个 Critic 子系统完成
- [x] Knowledge Graph 完成
- [x] Parameter Mapping Engine 完成（全 emotion 覆盖）
- [x] 人类反馈采集系统完成
- [ ] 最终验证："凌晨三点开车…孤独但希望" → 全自动编曲→评价→修正→输出

---

## 未列入 todo 但已实现的功能

| 功能 | 位置 |
|------|------|
| `analyze_vocal_quality` 工具 | `tools.ts` |
| `adjust_synthesized_pitch` 工具 | `tools.ts` |
| `vocal.py` critic 模块 | `cantiodaw/critic/vocal.py` |
| `synthesize_midi`（振荡器合成） | `tools.ts` |
| `llm_compose_music`（端到端 NL→音频） | `llm/tools.ts` |
| `OrchestrationEngine` 工作流引擎 | `orchestrator/engine.ts` |
| 6 个预定义工作流 | `orchestrator/workflows.ts` |
| SVS（歌声合成）引擎 | `cantiodaw/synthesis/svs_engine.py` |
| 歌词对齐器 | `cantiodaw/synthesis/lyrics_aligner.py` |
| `llm_generate_lyrics` | `llm/tools.ts` |
| `llm_suggest_arrangement` | `llm/tools.ts` |
| `llm_analyze_lyrics` | `llm/tools.ts` |
| `llm_analyze_music`（聚合 critic） | `llm/tools.ts` |
| `export_stems`（单轨导出） | `mcp/tools.ts` |
| `effect_apply`（效果器链） | `mcp/tools.ts` |
| `project_snapshot` | `mcp/tools.ts` |
| `feedback_submit` / `feedback_ab_test` | `mcp/tools.ts` |
