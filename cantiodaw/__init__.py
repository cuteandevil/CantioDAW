from .version import __version__, __version_info__

from .project import Project, Track, ProjectManager
from .core.audio_engine import AudioEngine
from .core.midi_engine import MIDIEngine, MIDINote
from .core.mixer import Mixer, EffectChain
from .synthesis.svs_engine import SVSConfig, SVSEngine
from .synthesis.lyrics_aligner import LyricsAligner
from .training.voice_trainer import VoiceTrainer, TrainingConfig
from .training.data_manager import VoiceDatasetManager, VoiceSample
from .audio.export import AudioExporter
from .audio.effects import AudioEffects, apply_reverb, apply_eq, apply_compressor
from .utils import detect_model_format, detect_model_info, get_config_path, adapt_config, create_adapter

from .music.ir import MusicIR, EmotionVector, EnergyCurve, StyleVector, SceneTags, ArrangementSpec, StructurePlan, SectionSpec, ParameterDelta
from .music.knowledge_graph import KnowledgeGraph, GraphNode, ParameterEffect
from .music.parameter_mapper import ParameterMapper, ArrangementConfig
from .music.labels import EMOTION_LABELS, SCENE_LABELS, STYLE_LABELS, INTENT_CATEGORIES
from .critic.harmony import HarmonyCritic, HarmonyAnalysis, HarmonyDiagnosis
from .critic.melody import MelodyCritic, MelodyAnalysis, MelodyDiagnosis
from .critic.rhythm import RhythmCritic, RhythmAnalysis, RhythmDiagnosis
from .critic.audio import AudioCritic, AudioAnalysis, AudioDiagnosis
from .preference.collector import PreferenceCollector, UserFeedback, ABTestResult
from .preference.model import PreferenceModel, FeedbackSample
from .project_version import VersionManager, VersionSnapshot
