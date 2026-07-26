import type { LLMRouter } from './router.js';
import type { PythonBridge } from '../bridge/python.js';
import { INTENT_PARSER_SYSTEM_PROMPT, INTENT_UPDATE_SYSTEM_PROMPT } from './prompts/intent_parser.js';
import type { MusicIR, EmotionVector, EnergyCurve, StyleVector } from '../music/ir.js';
import { createMusicIR } from '../music/ir.js';

export interface LLMToolDefinition {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (router: LLMRouter, bridge: PythonBridge, params: Record<string, unknown>, token?: string) => Promise<{
    success: boolean;
    data?: unknown;
    error?: string;
  }>;
}

function ok(data: unknown) {
  return { success: true, data };
}

function err(msg: string) {
  return { success: false, data: null, error: msg };
}

// ── llm_chat ──────────────────────────────────────
const llmChat: LLMToolDefinition = {
  name: 'llm_chat',
  description: 'Send a chat message to the LLM and get a response. Uses automatic provider/model routing.',
  inputSchema: {
    type: 'object',
    properties: {
      messages: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            role: { type: 'string', enum: ['system', 'user', 'assistant'] },
            content: { type: 'string' },
          },
          required: ['role', 'content'],
        },
        description: 'Chat messages (system prompt + user/assistant history)',
      },
      model: { type: 'string', description: 'Specific model to use (optional, router picks default otherwise)' },
      temperature: { type: 'number', default: 0.7 },
      max_tokens: { type: 'integer', default: 2048 },
      provider: { type: 'string', description: 'Specific provider to use (ollama, openai, etc.)' },
    },
    required: ['messages'],
  },
  handler: async (router, _bridge, params) => {
    const messages = params.messages as Array<{ role: string; content: string }>;
    if (!messages?.length) return err('messages required');

    // If provider specified, use that one
    if (params.provider) {
      const p = router.getProvider(params.provider as string);
      if (!p) return err(`Provider "${params.provider}" not registered. Available: ${router.getProviders().map((prov: { config: { name: string } }) => prov.config.name).join(', ')}`);
      router.setStrategy('manual');
    }

    try {
      const result = await router.complete({
        model: (params.model ?? '') as string,
        messages: messages.map((m) => ({
          role: m.role as 'system' | 'user' | 'assistant',
          content: m.content,
        })),
        temperature: (params.temperature ?? 0.7) as number,
        maxTokens: (params.max_tokens ?? 2048) as number,
      });
      return ok({
        content: result.choices[0]?.message?.content ?? '',
        model: result.model,
        provider: result.provider,
        usage: result.usage,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_stream ─────────────────────────────────────
const llmStream: LLMToolDefinition = {
  name: 'llm_stream',
  description: 'Stream a chat response from the LLM. Returns full response after completion.',
  inputSchema: {
    type: 'object',
    properties: {
      messages: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            role: { type: 'string', enum: ['system', 'user', 'assistant'] },
            content: { type: 'string' },
          },
          required: ['role', 'content'],
        },
      },
      model: { type: 'string' },
      temperature: { type: 'number', default: 0.7 },
      max_tokens: { type: 'integer', default: 2048 },
    },
    required: ['messages'],
  },
  handler: async (router, _bridge, params) => {
    const messages = params.messages as Array<{ role: string; content: string }>;
    if (!messages?.length) return err('messages required');

    try {
      const chunks: string[] = [];
      const result = await router.complete({
        model: (params.model ?? '') as string,
        messages: messages.map((m) => ({
          role: m.role as 'system' | 'user' | 'assistant',
          content: m.content,
        })),
        temperature: (params.temperature ?? 0.7) as number,
        maxTokens: (params.max_tokens ?? 2048) as number,
      });
      return ok({
        content: result.choices[0]?.message?.content ?? '',
        model: result.model,
        provider: result.provider,
        usage: result.usage,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_generate_lyrics ───────────────────────────
const llmGenerateLyrics: LLMToolDefinition = {
  name: 'llm_generate_lyrics',
  description: 'Generate song lyrics using LLM. Specify theme, style, language, and structure.',
  inputSchema: {
    type: 'object',
    properties: {
      theme: { type: 'string', description: 'Theme or topic of the song' },
      style: { type: 'string', enum: ['pop', 'rock', 'ballad', 'rap', 'electronic', 'folk', 'rb', 'custom'], default: 'pop' },
      language: { type: 'string', enum: ['en', 'zh', 'jp', 'kr', 'auto'], default: 'en' },
      lines: { type: 'integer', default: 8, description: 'Number of lines' },
      structure: { type: 'string', enum: ['verse+chorus', 'verses_only', 'chorus_only', 'free'], default: 'verse+chorus' },
      mood: { type: 'string', description: 'Mood: happy, sad, energetic, romantic, etc.', default: 'energetic' },
    },
    required: ['theme'],
  },
  handler: async (router, _bridge, params) => {
    const langMap: Record<string, string> = {
      en: 'English', zh: 'Chinese', jp: 'Japanese', kr: 'Korean',
    };
    const langName = langMap[(params.language as string) ?? 'en'] ?? 'English';

    const prompt = `You are a professional songwriter. Write a ${params.style ?? 'pop'} song lyric in ${langName}.

Theme: ${params.theme}
Mood: ${params.mood ?? 'energetic'}
Structure: ${params.structure ?? 'verse+chorus'}
Lines: ${params.lines ?? 8}

Output only the lyrics, no explanations. Use song structure markers like [Verse], [Chorus].`;

    try {
      const result = await router.complete({
        model: '',
        messages: [
          { role: 'system', content: 'You are a professional songwriter and lyricist.' },
          { role: 'user', content: prompt },
        ],
        temperature: 0.8,
        maxTokens: ((params.lines ?? 8) as number) * 40,
      });
      return ok({
        lyrics: result.choices[0]?.message?.content ?? '',
        model: result.model,
        provider: result.provider,
        usage: result.usage,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_compose_song ──────────────────────────────
const llmComposeSong: LLMToolDefinition = {
  name: 'llm_compose_song',
  description: 'End-to-end song composition: generate lyrics with LLM + create project + synthesize using voice model.',
  inputSchema: {
    type: 'object',
    properties: {
      theme: { type: 'string', description: 'Song theme/topic' },
      project_name: { type: 'string', description: 'CantioDAW project name' },
      model_path: { type: 'string', description: 'Voice model .pt/.safetensors path' },
      config_path: { type: 'string', description: 'Model config YAML path' },
      style: { type: 'string', enum: ['pop', 'rock', 'ballad', 'rap', 'electronic', 'folk'], default: 'pop' },
      language: { type: 'string', enum: ['en', 'zh'], default: 'en' },
      bpm: { type: 'number', default: 120 },
      pitch: { type: 'integer', default: 60, description: 'Base MIDI pitch' },
    },
    required: ['theme', 'project_name', 'model_path', 'config_path'],
  },
  handler: async (router, bridge, params, t) => {
    // Step 1: Generate lyrics
    const langName = params.language === 'zh' ? 'Chinese' : 'English';
    const lyricsResult = await router.complete({
      model: '',
      messages: [
        { role: 'system', content: 'You are a songwriter. Output ONLY the lyrics, no explanations.' },
        {
          role: 'user',
          content: `Write a ${params.style} song in ${langName} about "${params.theme}". 4 lines. Use [Verse] and [Chorus] markers.`,
        },
      ],
      temperature: 0.8,
      maxTokens: 300,
    });
    const lyrics = lyricsResult.choices[0]?.message?.content ?? '';

    // Step 2: Convert lyrics to phonemes
    const phonemeLang = params.language === 'zh' ? 'zh' : 'en';
    const phonemeResult = await bridge.call('midi_lyrics_to_phonemes', {
      text: `${phonemeLang}: ${lyrics}`,
    }, t);

    // Step 3: Create project
    const projectResult = await bridge.call('project_create', {
      name: params.project_name,
      bpm: params.bpm ?? 120,
    }, t);
    const projectName = (projectResult.data as { name?: string })?.name ?? params.project_name;

    // Step 4: Add track
    await bridge.call('track_add', {
      project: projectName,
      name: 'Melody',
      type: 'midi',
      color: '#4CAF50',
    }, t);

    // Step 5: Synthesize
    const synthResult = await bridge.call('synthesize', {
      model_path: params.model_path,
      config_path: params.config_path,
      pitch: params.pitch ?? 60,
      duration: 4.0,
      output_path: `${projectName}.wav`,
    }, t);

    return ok({
      project: projectName,
      lyrics,
      phonemes: phonemeResult.data,
      audio: synthResult.data,
      llm_usage: lyricsResult.usage,
      message: `Song "${params.theme}" composed in project "${projectName}". Synthesized to ${projectName}.wav`,
    });
  },
};

// ── llm_suggest_arrangement ───────────────────────
const llmSuggestArrangement: LLMToolDefinition = {
  name: 'llm_suggest_arrangement',
  description: 'Get AI-suggested music arrangement for a song based on style and mood.',
  inputSchema: {
    type: 'object',
    properties: {
      style: { type: 'string', enum: ['pop', 'rock', 'ballad', 'electronic', 'hiphop', 'jazz'], default: 'pop' },
      mood: { type: 'string', default: 'energetic' },
      bpm: { type: 'number', default: 120 },
      instruments: { type: 'string', description: 'Comma-separated available instruments' },
      duration: { type: 'number', default: 180, description: 'Target duration in seconds' },
    },
    required: ['style'],
  },
  handler: async (router, _bridge, params) => {
    try {
      const result = await router.complete({
        model: '',
        messages: [
          {
            role: 'system',
            content: 'You are a professional music producer and arranger. Output structured arrangement suggestions.',
          },
          {
            role: 'user',
            content: `Suggest a music arrangement for a ${params.style} song.
Mood: ${params.mood}
BPM: ${params.bpm}
Duration: ${params.duration}s
${params.instruments ? `Available instruments: ${params.instruments}` : ''}

Provide: intro, verse, chorus, bridge, outro structure with instrument layers and dynamics for each section.`,
          },
        ],
        temperature: 0.7,
        maxTokens: 1000,
      });
      return ok({
        arrangement: result.choices[0]?.message?.content ?? '',
        model: result.model,
        provider: result.provider,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_analyze_lyrics ────────────────────────────
const llmAnalyzeLyrics: LLMToolDefinition = {
  name: 'llm_analyze_lyrics',
  description: 'Analyze lyrics for sentiment, themes, keywords, and suggest musical interpretation.',
  inputSchema: {
    type: 'object',
    properties: {
      lyrics: { type: 'string', description: 'Lyrics text to analyze' },
      analysis_type: {
        type: 'string',
        enum: ['sentiment', 'keywords', 'full', 'musical_interpretation'],
        default: 'full',
      },
    },
    required: ['lyrics'],
  },
  handler: async (router, _bridge, params) => {
    const typeMap: Record<string, string> = {
      sentiment: 'Analyze the sentiment and emotional arc.',
      keywords: 'Extract key themes and keywords.',
      full: 'Analyze sentiment, themes, keywords, and structure.',
      musical_interpretation: 'Suggest musical style, tempo, dynamics, and instrumentation based on lyrics.',
    };
    try {
      const result = await router.complete({
        model: '',
        messages: [
          { role: 'system', content: 'You are a music analyst.' },
          {
            role: 'user',
            content: `${typeMap[(params.analysis_type as string) ?? 'full']}\n\nLyrics:\n${params.lyrics}`,
          },
        ],
        temperature: 0.5,
        maxTokens: 800,
      });
      return ok({
        analysis: result.choices[0]?.message?.content ?? '',
        model: result.model,
        provider: result.provider,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_list_providers ────────────────────────────
const llmListProviders: LLMToolDefinition = {
  name: 'llm_list_providers',
  description: 'List all registered LLM providers and their availability.',
  inputSchema: { type: 'object', properties: {} },
  handler: async (router, _bridge, _params) => {
    const providers = router.getProviders();
    const statuses = await router.testAll();
    return ok({
      providers: providers.map((p) => ({
        name: p.config.name,
        baseUrl: p.config.baseUrl,
        defaultModel: p.config.defaultModel,
        models: p.config.models.length > 0 ? p.config.models : ['(use list_models)'],
        priority: p.config.priority,
        available: statuses[p.config.name] ?? false,
      })),
    });
  },
};

// ── llm_list_models ───────────────────────────────
const llmListModels: LLMToolDefinition = {
  name: 'llm_list_models',
  description: 'List all available models across all registered LLM providers.',
  inputSchema: {
    type: 'object',
    properties: {
      provider: { type: 'string', description: 'Filter by provider name' },
    },
  },
  handler: async (router, _bridge, params) => {
    const allModels = await router.listAllModels();
    const filtered = params.provider
      ? allModels.filter((m: { provider: string }) => m.provider === params.provider)
      : allModels;
    return ok({ models: filtered.slice(0, 100) });
  },
};

// ── llm_compose_music ─────────────────────────────
const llmComposeMusic: LLMToolDefinition = {
  name: 'llm_compose_music',
  description: 'Directly compose/arrange music using LLM: describe a piece and get back a structured arrangement with synthesized audio.',
  inputSchema: {
    type: 'object',
    properties: {
      description: { type: 'string', description: 'Describe the music you want (style, mood, tempo, instruments, structure, etc.)' },
      style: { type: 'string', enum: ['pop', 'rock', 'electronic', 'classical', 'jazz', 'hiphop', 'folk', 'cinematic', 'custom'], default: 'pop' },
      mood: { type: 'string', default: 'happy', description: 'mood: happy, sad, energetic, calm, dark, romantic' },
      tempo: { type: 'integer', default: 120, description: 'BPM' },
      key: { type: 'string', default: 'C', description: 'Musical key (C, G, Dm, etc.)' },
      duration_bars: { type: 'integer', default: 16, description: 'Number of bars' },
      waveform: { type: 'string', enum: ['sine', 'triangle', 'sawtooth', 'square', 'piano'], default: 'sine' },
      output_path: { type: 'string', default: '', description: 'Output WAV path (empty = return metadata only)' },
      sections: { type: 'string', description: 'Desired sections like intro, verse, chorus, bridge, outro' },
    },
    required: ['description'],
  },
  handler: async (router, bridge, params, t) => {
    const sections = (params.sections as string) ?? 'intro, verse, chorus, verse, chorus, bridge, chorus, outro';

    const systemPrompt = `You are a professional music composer and arranger. Output ONLY valid JSON.

Generate a musical arrangement as JSON with this exact structure:
{
  "title": "string",
  "tempo": number,
  "key": "string",
  "timeSignature": "string",
  "sections": [
    {
      "name": "string",
      "bars": number,
      "chords": ["string"],
      "melody": [
        {"pitch": number(0-127), "duration": number(beats), "start": number(beats), "velocity": number(0-127)}
      ]
    }
  ]
}

Rules:
- pitch: MIDI note numbers (C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72)
- duration: in beats (1 = quarter note, 0.5 = eighth, 2 = half, 4 = whole)
- start: beat offset within section
- chords: array of chord names per bar (e.g. "C", "G", "Am", "F")
- melody: 2-8 notes per bar, varied rhythm, musically interesting
- velocity: 40-120
- TOTAL notes across ALL sections: exactly ${params.duration_bars ?? 16} bars worth, distributed proportionally`;

    const userPrompt = `Compose a ${params.style ?? 'pop'} piece in ${params.key ?? 'C'}.
Tempo: ${params.tempo ?? 120} BPM
Mood: ${params.mood ?? 'happy'}
Duration: ${params.duration_bars ?? 16} bars
Sections: ${sections}
${params.description ? `\nAdditional: ${params.description}` : ''}`;

    try {
      const llmResult = await router.complete({
        model: '',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        temperature: 0.7,
        maxTokens: 3000,
      });

      const rawText = llmResult.choices[0]?.message?.content ?? '';
      const jsonMatch = rawText.match(/```(?:json)?\s*([\s\S]*?)```/) || rawText.match(/{[\s\S]*"sections"[\s\S]*}/);
      const jsonStr = jsonMatch?.[1] ?? rawText;
      const arrangement = JSON.parse(jsonStr);

      const allSections = arrangement.sections ?? [];
      const allNotes: Array<{ pitch: number; duration: number; start: number; velocity: number }> = [];
      let beatOffset = 0;

      for (const section of allSections) {
        const sectionNotes = section.melody ?? [];
        for (const note of sectionNotes) {
          allNotes.push({
            pitch: note.pitch,
            duration: note.duration,
            start: beatOffset + (note.start ?? 0),
            velocity: note.velocity ?? 80,
          });
        }
        const sectionBeats = (section.bars ?? 4) * 4;
        beatOffset += sectionBeats;
      }

      if (allNotes.length === 0) {
        return err('LLM generated no notes. Try a simpler description.');
      }

      const synthResult = await bridge.call('synthesize_midi', {
        notes: allNotes,
        tempo: arrangement.tempo ?? params.tempo ?? 120,
        waveform: (params.waveform as string) ?? 'sine',
        sample_rate: 24000,
        output_path: (params.output_path as string) || '',
      }, t);

      return ok({
        title: arrangement.title ?? 'Untitled',
        tempo: arrangement.tempo,
        key: arrangement.key,
        timeSignature: arrangement.timeSignature ?? '4/4',
        sections: allSections.map((s: { name: string; bars: number; chords: string[]; melody?: unknown[] }) => ({
          name: s.name,
          bars: s.bars,
          chords: s.chords,
          noteCount: (s.melody ?? []).length,
        })),
        totalNotes: allNotes.length,
        audio: synthResult.data,
        llm_usage: llmResult.usage,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes('JSON') || msg.includes('token') || msg.includes('parse')) {
        return err(`LLM output was not valid JSON. Try a simpler description. Error: ${msg.slice(0, 200)}`);
      }
      return err(msg);
    }
  },
};

// ── llm_parse_intent ──────────────────────────────
const llmParseIntent: LLMToolDefinition = {
  name: 'llm_parse_intent',
  description: 'Parse natural language music description into Music Semantic IR (emotion, energy, style, scene, arrangement).',
  inputSchema: {
    type: 'object',
    properties: {
      text: { type: 'string', description: 'Natural language music description (e.g. "凌晨三点开车，一个人在城市里，很孤独但最后看到希望")' },
      current_ir: { type: 'object', description: 'Optional existing MusicIR to apply incremental update' },
      language: { type: 'string', enum: ['zh', 'en', 'auto'], default: 'auto' },
    },
    required: ['text'],
  },
  handler: async (router, _bridge, params) => {
    const text = params.text as string;
    if (!text) return err('text is required');
    const currentIr = params.current_ir as Record<string, unknown> | undefined;
    const systemPrompt = currentIr ? INTENT_UPDATE_SYSTEM_PROMPT : INTENT_PARSER_SYSTEM_PROMPT;
    const userContent = currentIr
      ? `当前 MusicIR:\n${JSON.stringify(currentIr, null, 2)}\n\n用户增量指令: ${text}`
      : text;

    try {
      const result = await router.complete({
        model: '',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userContent },
        ],
        temperature: 0.3,
        maxTokens: 2000,
      });
      const rawText = result.choices[0]?.message?.content ?? '';
      const jsonMatch = rawText.match(/```(?:json)?\s*([\s\S]*?)```/) || rawText.match(/{[\s\S]*"emotion"[\s\S]*}/) || rawText.match(/{[\s\S]*}/);
      const jsonStr = jsonMatch?.[1] ?? rawText;
      const ir = JSON.parse(jsonStr);

      let musicIR: MusicIR;
      if (currentIr) {
        musicIR = createMusicIR(JSON.parse(JSON.stringify(currentIr)));
        const delta = ir;
        for (const [k, v] of Object.entries(delta)) {
          if (typeof v === 'object' && v !== null) {
            const existing = (musicIR as unknown as Record<string, unknown>)[k];
            if (typeof existing === 'object' && existing !== null) {
              for (const [subK, subV] of Object.entries(v as Record<string, unknown>)) {
                if (typeof subV === 'number') {
                  const old = (existing as Record<string, number>)[subK] ?? 0;
                  (existing as Record<string, number>)[subK] = Math.max(0, Math.min(1, old + subV));
                } else if (Array.isArray(subV)) {
                  const oldArr = (existing as Record<string, unknown[]>)[subK] ?? [];
                  (existing as Record<string, unknown[]>)[subK] = [...oldArr, ...subV];
                } else {
                  (existing as Record<string, unknown>)[subK] = subV;
                }
              }
            } else {
              (musicIR as unknown as Record<string, unknown>)[k] = v;
            }
          }
        }
      } else {
        musicIR = createMusicIR(ir);
      }

      return ok({
        ir: musicIR,
        raw: ir,
        model: result.model,
        provider: result.provider,
      });
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_query_knowledge_graph ────────────────────
const llmQueryKnowledgeGraph: LLMToolDefinition = {
  name: 'llm_query_knowledge_graph',
  description: 'Query the music knowledge graph for parameter mappings related to a concept (e.g. tension, sadness, hope).',
  inputSchema: {
    type: 'object',
    properties: {
      concept: { type: 'string', description: 'Music concept to query (e.g. tension, calmness, joy, sadness)' },
      direction: { type: 'string', enum: ['affects', 'inverse'], default: 'affects', description: 'Query direction' },
    },
    required: ['concept'],
  },
  handler: async (_router, bridge, params, t) => {
    return bridge.call('knowledge_graph_query', {
      concept: params.concept,
      direction: params.direction ?? 'affects',
    }, t);
  },
};

// ── llm_compose_from_intent ──────────────────────
const llmComposeFromIntent: LLMToolDefinition = {
  name: 'llm_compose_from_intent',
  description: 'Compose a musical arrangement from a MusicIR using the Composer Agent. Returns structured arrangement with sections, chords, melody notes.',
  inputSchema: {
    type: 'object',
    properties: {
      ir: { type: 'object', description: 'MusicIR JSON object' },
      model: { type: 'string', description: 'Optional specific LLM model to use' },
      generate_midi: { type: 'boolean', default: false, description: 'Also generate and synthesize MIDI output' },
    },
    required: ['ir'],
  },
  handler: async (router, bridge, params, t) => {
    const ir = params.ir as Record<string, unknown>;
    if (!ir) return err('ir is required');

    try {
      const { composeFromIR } = await import('../orchestrator/composer.js');
      const arrangement = await composeFromIR(router, ir as unknown as MusicIR, params.model as string | undefined);

      const result: Record<string, unknown> = { arrangement };

      if (params.generate_midi) {
        const { arrangementToMIDINotes } = await import('../orchestrator/composer.js');
        const notes = arrangementToMIDINotes(arrangement);
        result.notes = notes;

        const midiResult = await bridge.call('synthesize_midi', {
          notes: notes.map((n) => ({ pitch: n.pitch, duration: n.duration, start: n.start, velocity: n.velocity })),
          tempo: arrangement.tempo,
          waveform: 'piano',
          sample_rate: 24000,
        }, t);
        if (midiResult.success) {
          result.audio = midiResult.data;
        }
      }

      return ok(result);
    } catch (e: unknown) {
      return err(e instanceof Error ? e.message : String(e));
    }
  },
};

// ── llm_analyze_music ────────────────────────────
const llmAnalyzeMusic: LLMToolDefinition = {
  name: 'llm_analyze_music',
  description: 'Run music analysis (critic) on a project or track. Analyzes harmony, melody, rhythm, and audio quality.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      track_id: { type: 'string', description: 'Track ID to analyze (optional, analyzes all if omitted)' },
      domains: { type: 'array', items: { type: 'string', enum: ['harmony', 'melody', 'rhythm', 'audio'] }, description: 'Analysis domains to run (all if omitted)' },
    },
    required: ['project'],
  },
  handler: async (_router, bridge, params, t) => {
    return bridge.call('analyze_music', {
      project: params.project,
      track_id: params.track_id,
      domains: params.domains,
    }, t);
  },
};

// ── llm_request_checkpoint ───────────────────────
const llmRequestCheckpoint: LLMToolDefinition = {
  name: 'llm_request_checkpoint',
  description: 'Request a human checkpoint during automated workflow. Returns current vs previous version key metric comparison.',
  inputSchema: {
    type: 'object',
    properties: {
      project: { type: 'string', description: 'Project name' },
      message: { type: 'string', description: 'Optional message to display at checkpoint' },
    },
    required: ['project'],
  },
  handler: async (_router, bridge, params, t) => {
    return bridge.call('request_checkpoint', {
      project: params.project,
      message: params.message,
    }, t);
  },
};

// ── llm_usage_stats ───────────────────────────────
const llmUsageStats: LLMToolDefinition = {
  name: 'llm_usage_stats',
  description: 'Get LLM usage statistics (calls, tokens, failures tracked during this session).',
  inputSchema: { type: 'object', properties: {} },
  handler: async (router, _bridge, _params) => {
    return ok(router.getUsageSummary());
  },
};

// ── Registry ──────────────────────────────────────
export const LLM_TOOLS: LLMToolDefinition[] = [
  llmChat,
  llmStream,
  llmGenerateLyrics,
  llmComposeSong,
  llmSuggestArrangement,
  llmAnalyzeLyrics,
  llmComposeMusic,
  llmListProviders,
  llmListModels,
  llmUsageStats,
  llmParseIntent,
  llmQueryKnowledgeGraph,
  llmComposeFromIntent,
  llmAnalyzeMusic,
  llmRequestCheckpoint,
];

export function getLLMTool(name: string): LLMToolDefinition | undefined {
  return LLM_TOOLS.find((t) => t.name === name);
}
