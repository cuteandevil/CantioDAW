import { createDefaultRouter } from '../dist/llm/config.js';
import { PythonBridge } from '../dist/bridge/python.js';

const router = createDefaultRouter();
const bridge = new PythonBridge();

const sysPrompt =
  'Output ONLY valid JSON. A 4-bar piano melody in C major at 120bpm. ' +
  'Format: {"tempo":120,"key":"C","sections":[{"name":"v","bars":4,"chords":["C","G","Am","F"],' +
  '"melody":[{"pitch":60,"duration":1,"start":0,"velocity":90},{"pitch":64,"duration":1,"start":1,"velocity":85},{"pitch":67,"duration":2,"start":2,"velocity":95},{"pitch":72,"duration":4,"start":4,"velocity":100}]}]}';

const r = await router.complete({
  model: 'gemma4:31b',
  messages: [
    { role: 'system', content: 'You output ONLY valid JSON. No explanations.' },
    { role: 'user', content: sysPrompt },
  ],
  temperature: 0.2,
  maxTokens: 1000,
});

const text = r.choices[0].message.content.trim();
console.log('=== LLM raw output ===');
console.log(text.substring(0, 600));
console.log('======================');

const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/) || text.match(/{[\s\S]*"sections"[\s\S]*}/);
const jsonStr = (jsonMatch?.[1] ?? text).trim();
const json = JSON.parse(jsonStr);
const notes = [];
let beatOff = 0;
for (const sec of json.sections ?? []) {
  for (const n of sec.melody ?? []) {
    notes.push({ pitch: n.pitch, duration: n.duration, start: beatOff + (n.start ?? 0), velocity: n.velocity ?? 80 });
  }
  beatOff += (sec.bars ?? 4) * 4;
}

console.log(`Notes: ${notes.length}`);
if (notes.length > 0) {
  const out = await bridge.call('synthesize_midi', {
    notes,
    tempo: json.tempo ?? 120,
    waveform: 'piano',
    output_path: 'D:\\composed_test.wav',
  });
  console.log('Audio:', JSON.stringify(out.data, null, 2));
} else {
  console.log('No notes generated');
}

await bridge.close();
