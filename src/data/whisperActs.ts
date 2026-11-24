export function formatSmpteTimecode(
  scrollProgress: number,
  totalSeconds: number = 90,
  fps: number = 24
): string {
  const clamped = Math.min(1, Math.max(0, scrollProgress));
  const totalFrames = Math.round(clamped * totalSeconds * fps);
  const frame = totalFrames % fps;
  const totalWholeSeconds = Math.floor(totalFrames / fps);
  const seconds = totalWholeSeconds % 60;
  const minutes = Math.floor(totalWholeSeconds / 60) % 60;
  const hours = Math.floor(totalWholeSeconds / 3600);

  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}:${pad(frame)}`;
}

export interface WhisperActConfig {
  actIndex: number;
  sectionId: string;
  actBadge: string;
  sceneSlate: string;
  shortCutLabel: string;
  timecodeStart: string;
  stageName: string;
  title: string;
  hook: string;
  companionWhisper: string;
  transitWhisper: string;
  accentColor: string;
}

export const WHISPER_ACTS: readonly WhisperActConfig[] = [
  {
    actIndex: 0,
    sectionId: 'hero',
    actBadge: 'Act 01 • Titanium Atelier',
    sceneSlate: 'SC 01',
    shortCutLabel: 'Atelier',
    timecodeStart: '00:00:00:00',
    stageName: 'Executive Strategy Stage',
    title: 'Architect of Enterprise Intelligence.',
    hook: '1st Place Hilti Global Champion & First-Class Honours engineer bridging C-suite strategy with production AI.',
    companionWhisper: '“Walk with me through six chapters—from Malaysia foundations to Swiss summits and production AI.”',
    transitWhisper: '“Stepping onto the skybridge—walking from the Titanium Atelier into the journey ahead.”',
    accentColor: '#d4b483',
  },
  {
    actIndex: 1,
    sectionId: 'timeline',
    actBadge: 'Act 02 • The Academy',
    sceneSlate: 'SC 02',
    shortCutLabel: 'Academy',
    timecodeStart: '00:00:18:00',
    stageName: 'Cathedral Knowledge Archive',
    title: 'Academic Foundations & Career Ascent.',
    hook: 'Pull any milestone volume from the shelf to illuminate its pages on the lectern.',
    companionWhisper: '“Every volume on this shelf marks a late-night build, a dual First-Class milestone, or Soft Space BA rigor.”',
    transitWhisper: '“Crossing the skybridge into the Cathedral Knowledge Archive—from dual First-Class honours to enterprise fintech rigor.”',
    accentColor: '#dba052',
  },
  {
    actIndex: 2,
    sectionId: 'vault',
    actBadge: 'Act 03 • The Crucible',
    sceneSlate: 'SC 03',
    shortCutLabel: 'Crucible',
    timecodeStart: '00:00:36:00',
    stageName: 'Keynote Stadium Arena',
    title: 'Cloud Mastery & GDSC Community.',
    hook: '14 Google Cloud & Vertex AI quests and 500+ student attendees across GDSC APU workshops.',
    companionWhisper: '“Here is where theory met pressure-tested cloud craft and organizing GDSC APU workshops for 500+ student builders.”',
    transitWhisper: '“Crossing the skybridge toward Google Cloud mastery and GDSC APU community workshops for 500+ attendees.”',
    accentColor: '#38bdf8',
  },
  {
    actIndex: 3,
    sectionId: 'summit',
    actBadge: 'Act 04 • The Alpine Summit',
    sceneSlate: 'SC 04',
    shortCutLabel: 'Summit',
    timecodeStart: '00:00:54:00',
    stageName: 'Pilatus Alpine Sunrise (2,128m)',
    title: '1st Place Worldwide • Team Sweetzerland.',
    hook: 'Triumphing over 53 international university teams from Schaan HQ to the Swiss Alps.',
    companionWhisper: '“Leading Team Sweetzerland at Hilti Schaan HQ taught me how bold strategy wins on a global stage.”',
    transitWhisper: '“Climbing higher now—ahead lies Mount Pilatus and the global championship finale.”',
    accentColor: '#ffcf6d',
  },
  {
    actIndex: 4,
    sectionId: 'ai-solutions',
    actBadge: 'Act 05 • The Frontier',
    sceneSlate: 'SC 05',
    shortCutLabel: 'Frontier',
    timecodeStart: '00:01:12:00',
    stageName: 'Cyber-Amber Reactor Vault',
    title: 'Production AI & Enterprise Systems.',
    hook: 'Select any system core to explode its 3 architectural strata: UI, AI Core, and Settlement.',
    companionWhisper: '“Tap any core to inspect the exact UI, AI orchestration, and ISO-20022 layers running in production.”',
    transitWhisper: '“Descending from the Alps into the live production reactors of my enterprise AI systems.”',
    accentColor: '#f97316',
  },
  {
    actIndex: 5,
    sectionId: 'contact',
    actBadge: 'Act 06 • The Horizon',
    sceneSlate: 'SC 06',
    shortCutLabel: 'Horizon',
    timecodeStart: '00:01:30:00',
    stageName: 'Solar Eclipse Observatory',
    title: 'Initiate Collaboration.',
    hook: 'Select any personal lens to morph the Horizon Observatory or transmit a direct dispatch.',
    companionWhisper: '“Thanks for walking my story with me—let’s architect something enduring next.”',
    transitWhisper: '“One last bridge ahead—meet me at the Horizon Observatory to initiate collaboration.”',
    accentColor: '#5eead4',
  },
] as const satisfies readonly WhisperActConfig[];
