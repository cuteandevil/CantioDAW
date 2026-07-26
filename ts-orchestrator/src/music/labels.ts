export const EMOTION_LABELS: Record<string, string> = {
  loneliness: '孤独感 — 疏离、空旷、沉思',
  hope: '希望 — 上升、光明、期待',
  nostalgia: '怀旧 — 回忆、温暖、感伤',
  tension: '紧张 — 不安、悬疑、压迫',
  calmness: '平静 — 安宁、舒缓、冥想',
  sadness: '悲伤 — 哀伤、忧郁、低沉',
  joy: '喜悦 — 欢快、明亮、活泼',
  anger: '愤怒 — 激烈、强劲、冲击',
  fear: '恐惧 — 惊悚、阴暗、不安',
  romance: '浪漫 — 温柔、亲密、甜蜜',
};

export const SCENE_LABELS: string[] = [
  'night', 'urban', 'driving', 'rain', 'morning', 'forest',
  'ocean', 'desert', 'mountain', 'countryside', 'space',
  'underwater', 'fireplace', 'garden', 'street', 'market',
  'temple', 'castle', 'cave', 'airport', 'train',
];

export const STYLE_LABELS: string[] = [
  'cinematic', 'electronic', 'orchestral', 'pop', 'ambient',
  'rock', 'jazz', 'classical', 'folk', 'hiphop', 'rnb',
  'blues', 'metal', 'punk', 'reggae', 'lofi', 'synthwave',
  'world', 'experimental', 'minimal',
];

export const INTENT_CATEGORIES: Record<string, string> = {
  emotion: '用户描述情绪/感受',
  scene: '用户描述场景/环境',
  energy: '用户描述能量/动态变化',
  style: '用户描述风格/流派',
  contrast: '用户描述对比/变化/转折',
};
