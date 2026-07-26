_LANG = "zh"
_TRANSLATIONS = {}

_TRANSLATIONS["zh"] = {
    "lang.name": "中文",
    "lang.zh": "中文",
    "lang.en": "English",
    "window.title": "CantioDAW",
    "project.untitled": "未命名项目",
    "file": "文件",
    "file.new": "新建项目",
    "file.open": "打开项目",
    "file.save": "保存",
    "file.export": "导出音频",
    "file.exit": "退出",
    "edit": "编辑",
    "edit.undo": "撤销",
    "edit.redo": "重做",
    "view": "视图",
    "view.toggle_sidebar": "切换侧边栏",
    "view.toggle_mixer": "切换混音台",
    "view.toggle_pipeline": "切换 AI 流水线",
    "tools": "工具",
    "tools.training": "训练中心",
    "tools.settings": "加载模型",
    "help": "帮助",
    "help.about": "关于",
    "track": "音轨",
    "track.add": "添加音轨",
    "track.remove": "删除音轨",
    "track.name": "音轨名称",
    "track.volume": "音量",
    "track.pan": "声像",
    "track.mute": "静音",
    "track.solo": "独奏",
    "mixer.title": "混音台",
    "pipeline.title": "AI 流水线",
    "pipeline.generate": "生成",
    "pipeline.stop": "停止",
    "pipeline.bpm": "BPM",
    "pipeline.key": "调性",
    "pipeline.mood": "情绪 / 风格",
    "pipeline.ready": "就绪",
    "pipeline.step_intent": "意图",
    "pipeline.step_compose": "作曲",
    "pipeline.step_params": "参数",
    "pipeline.step_midi": "MIDI",
    "pipeline.step_critic": "评判",
    "pipeline.step_revise": "修订",
    "pipeline.critic_pitch": "音高",
    "pipeline.critic_rhythm": "节奏",
    "pipeline.critic_tonal": "调性",
    "pipeline.critic_vocal": "人声",
    "pipeline.critic_structure": "结构",
    "pipeline.critic_overall": "综合",
    "pipeline.processing": "处理中：{step}",
    "pipeline.complete": "完成 ✓",
    "training.title": "训练中心",
    "training.start": "开始训练",
    "training.voice_name": "声音名称",
    "training.dataset": "数据集路径",
    "training.epochs": "轮数",
    "training.batch": "批次大小",
    "training.lora": "LoRA 微调",
    "status.ready": "就绪",
    "status.no_model": "无模型",
    "status.project": "项目：{name}",
    "status.model": "模型：{name}",
    "lang.switch": "语言 / Language",
}

_TRANSLATIONS["en"] = {
    "lang.name": "English",
    "lang.zh": "中文",
    "lang.en": "English",
    "window.title": "CantioDAW",
    "project.untitled": "Untitled Project",
    "file": "File",
    "file.new": "New Project",
    "file.open": "Open Project",
    "file.save": "Save",
    "file.export": "Export Audio",
    "file.exit": "Exit",
    "edit": "Edit",
    "edit.undo": "Undo",
    "edit.redo": "Redo",
    "view": "View",
    "view.toggle_sidebar": "Toggle Sidebar",
    "view.toggle_mixer": "Toggle Mixer",
    "view.toggle_pipeline": "Toggle AI Pipeline",
    "tools": "Tools",
    "tools.training": "Training Center",
    "tools.settings": "Load Model",
    "help": "Help",
    "help.about": "About",
    "track": "Track",
    "track.add": "Add Track",
    "track.remove": "Remove Track",
    "track.name": "Track Name",
    "track.volume": "Volume",
    "track.pan": "Pan",
    "track.mute": "Mute",
    "track.solo": "Solo",
    "mixer.title": "Mixer",
    "pipeline.title": "AI Pipeline",
    "pipeline.generate": "Generate",
    "pipeline.stop": "Stop",
    "pipeline.bpm": "BPM",
    "pipeline.key": "Key",
    "pipeline.mood": "Mood / Style",
    "pipeline.ready": "Ready",
    "pipeline.step_intent": "Intent",
    "pipeline.step_compose": "Compose",
    "pipeline.step_params": "Params",
    "pipeline.step_midi": "MIDI",
    "pipeline.step_critic": "Critic",
    "pipeline.step_revise": "Revise",
    "pipeline.critic_pitch": "Pitch",
    "pipeline.critic_rhythm": "Rhythm",
    "pipeline.critic_tonal": "Tonal",
    "pipeline.critic_vocal": "Vocal",
    "pipeline.critic_structure": "Structure",
    "pipeline.critic_overall": "Overall",
    "pipeline.processing": "Processing: {step}",
    "pipeline.complete": "Complete ✓",
    "training.title": "Training Center",
    "training.start": "Start Training",
    "training.voice_name": "Voice Name",
    "training.dataset": "Dataset Path",
    "training.epochs": "Epochs",
    "training.batch": "Batch Size",
    "training.lora": "LoRA Fine-tune",
    "status.ready": "Ready",
    "status.no_model": "No Model",
    "status.project": "Project: {name}",
    "status.model": "Model: {name}",
    "lang.switch": "语言 / Language",
}


def set_language(lang: str):
    global _LANG
    if lang in _TRANSLATIONS:
        _LANG = lang


def get_language() -> str:
    return _LANG


def get_languages() -> list:
    return list(_TRANSLATIONS.keys())


def tr(key: str, **kwargs) -> str:
    t = _TRANSLATIONS.get(_LANG, {}).get(key)
    if t is None:
        t = _TRANSLATIONS.get("en", {}).get(key, key)
    if kwargs:
        for k, v in kwargs.items():
            t = t.replace(f"{{{k}}}", str(v))
    return t
