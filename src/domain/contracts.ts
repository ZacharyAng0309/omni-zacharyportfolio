export interface BaseEntity {
  id: string;
  createdAt: string;
}

export type SceneChapter = 'hero' | 'summit' | 'ai-network' | 'vault' | 'timeline' | 'action';

export interface CameraWaypoint {
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

export interface CaseStudy extends BaseEntity {
  slug: string;
  title: string;
  subtitle: string;
  category: string;
  role: string;
  impactMetrics: string[];
  description: string;
  problemStatement: string;
  solutionArchitecture: string[];
  techStack: string[];
  externalUrl?: string;
  repoUrl?: string;
  featuredAward?: string;
  accentColor: string;
}

export interface CredentialBadge extends BaseEntity {
  title: string;
  issuer: string;
  badgeType: string;
  issueDate: string;
  verificationUrl?: string;
  proofThumbnail?: string;
  highlights: string[];
  color: string;
}

export interface CareerMilestone extends BaseEntity {
  period: string;
  role: string;
  organization: string;
  location: string;
  category: string;
  keyImpacts: string[];
  techOrDomain: string[];
  isHero: boolean; // false for standard enterprise experience like Soft Space
}

export interface ContactInquiry {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface SceneControllerState {
  scrollProgress: number; // 0.0 to 1.0
  activeChapter: SceneChapter;
  isReducedMotion: boolean;
  fps: number;
}
