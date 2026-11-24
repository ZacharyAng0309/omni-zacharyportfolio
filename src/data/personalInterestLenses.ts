export interface PersonalInterestLens {
  id: string;
  title: string;
  shortLabel: string;
  color: string;
  tagline: string;
  description: string;
  approachTitle: string;
  approachSubject: string;
  starterPrompt: string;
}

export const PERSONAL_INTEREST_LENSES: readonly PersonalInterestLens[] = [
  {
    id: 'ai-systems',
    title: 'AI Systems & Multi-Agent Orchestration',
    shortLabel: 'AI & Multi-Agent Systems',
    color: '#06b6d4',
    tagline: 'Autonomous LLM workflows, Vertex AI embeddings & tool-calling agents',
    description:
      'Building deterministic multi-agent pipelines, RAG evaluation harnesses, and local-first AI desktop tools that turn frontier models into reliable production software.',
    approachTitle: 'Co-Design an Agentic AI System or Product Strategy',
    approachSubject: 'AI Systems & Multi-Agent Strategy Inquiry',
    starterPrompt:
      'Hi Zachary — I explored your AI Systems lens and would love to discuss architecting an agentic workflow / LLM product roadmap.',
  },
  {
    id: 'crypto-quant',
    title: 'Crypto & Quantitative Market Structure',
    shortLabel: 'Crypto & Quant Markets',
    color: '#f59e0b',
    tagline: 'On-chain liquidity, algorithmic execution & market microstructure',
    description:
      'Analyzing digital asset market structure, order-flow dynamics, and automated quantitative research pipelines across decentralized and institutional venues.',
    approachTitle: 'Exchange Alpha on Crypto & Quantitative Market Structure',
    approachSubject: 'Crypto & Quantitative Market Structure Discussion',
    starterPrompt:
      'Hi Zachary — I saw your Crypto & Quantitative Market Structure lens and wanted to connect on algorithmic market mechanics and digital asset infrastructure.',
  },
  {
    id: 'cinematic-video',
    title: 'Cinematic Video Editing & Visual Storytelling',
    shortLabel: 'Cinematic Video & Direction',
    color: '#a855f7',
    tagline: 'Keynote-grade pacing, sound design & narrative visual direction',
    description:
      'Crafting high-impact product reveal films, motion choreography, and executive pitch narratives that make complex engineering feel visceral and human.',
    approachTitle: 'Collaborate on Cinematic Product Storytelling & Direction',
    approachSubject: 'Cinematic Video Direction & Product Storytelling',
    starterPrompt:
      'Hi Zachary — Your Cinematic Video Editing & Visual Storytelling lens caught my eye. Let’s talk about directing a high-impact product reveal or narrative showcase.',
  },
  {
    id: 'hackathons-mentorship',
    title: 'Global Hackathons & Mentorship',
    shortLabel: 'Hackathons & Mentorship',
    color: '#10b981',
    tagline: 'Hilti Global Grand Champion • GDSC APU 500+ developer workshops',
    description:
      'Mentoring student builders, judging hackathons, and coaching engineering teams on how to turn 48-hour prototypes into globally competitive executive pitches.',
    approachTitle: 'Invite for Hackathon Judging, Keynote Speaking, or Mentorship',
    approachSubject: 'Hackathon Mentorship / Speaking Invitation',
    starterPrompt:
      'Hi Zachary — Reaching out via your Global Hackathons & Mentorship lens regarding a speaking, judging, or builder mentorship opportunity.',
  },
  {
    id: 'fintech-architecture',
    title: 'Fintech & Enterprise Architecture',
    shortLabel: 'Fintech & Super-Apps',
    color: '#3b82f6',
    tagline: 'Zero-defect digital banking super-apps, ISO 20022 & EMV L2 kernels',
    description:
      'Bridging C-suite commercial strategy with bank-grade Functional Specifications (BRD/FSD), cross-border payment rails, and high-availability mobile wallets.',
    approachTitle: 'Advisory on Fintech Super-Apps & Enterprise BA Architecture',
    approachSubject: 'Fintech & Enterprise Architecture Advisory',
    starterPrompt:
      'Hi Zachary — Connecting through your Fintech & Enterprise Architecture lens to discuss digital banking super-app delivery and enterprise BA strategy.',
  },
] as const;
