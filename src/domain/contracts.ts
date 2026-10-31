import { z } from 'zod';

// ============================================================================
// 1. Matt Pocock Utility Types & Exhaustive Matching
// ============================================================================

declare const __brand: unique symbol;
export type Brand<T, B> = T & { readonly [__brand]: B };

export type Prettify<T> = {
  [K in keyof T]: T[K];
} & {};

export function assertNever(x: never, message?: string): never {
  throw new Error(message ?? `Unexpected discriminated variant: ${JSON.stringify(x)}`);
}

// Nominal Branded Identifiers
export type CaseStudyId = Brand<string, 'CaseStudyId'>;
export type CredentialId = Brand<string, 'CredentialId'>;
export type MilestoneId = Brand<string, 'MilestoneId'>;

// ============================================================================
// 2. Schema-First Zod Definitions (Single Source of Truth)
// ============================================================================

export const BaseEntitySchema = z.object({
  id: z.string(),
  createdAt: z.string(),
});

export const SceneChapterSchema = z.enum([
  'prologue',
  'academy',
  'crucible',
  'summit',
  'frontier',
  'epilogue',
  'hero',
  'ai-network',
  'vault',
  'timeline',
  'action',
]);

export const CameraWaypointSchema = z.object({
  position: z.tuple([z.number(), z.number(), z.number()]),
  target: z.tuple([z.number(), z.number(), z.number()]),
  fov: z.number(),
});

export const CaseStudySchema = BaseEntitySchema.extend({
  slug: z.string(),
  title: z.string(),
  subtitle: z.string(),
  category: z.string(),
  role: z.string(),
  impactMetrics: z.array(z.string()),
  description: z.string(),
  problemStatement: z.string(),
  solutionArchitecture: z.array(z.string()),
  techStack: z.array(z.string()),
  externalUrl: z.string().optional(),
  repoUrl: z.string().optional(),
  featuredAward: z.string().optional(),
  accentColor: z.string(),
});

export const CredentialBadgeSchema = BaseEntitySchema.extend({
  title: z.string(),
  issuer: z.string(),
  badgeType: z.string(),
  issueDate: z.string(),
  verificationUrl: z.string().optional(),
  proofThumbnail: z.string().optional(),
  highlights: z.array(z.string()),
  color: z.string(),
});

export const CareerMilestoneSchema = BaseEntitySchema.extend({
  period: z.string(),
  role: z.string(),
  organization: z.string(),
  location: z.string(),
  category: z.string(),
  keyImpacts: z.array(z.string()),
  techOrDomain: z.array(z.string()),
  isHero: z.boolean(), // false for standard enterprise experience like Soft Space
});

export const ContactInquirySchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  subject: z.string().min(1, 'Subject is required'),
  message: z.string().min(1, 'Message is required'),
});

export const SceneControllerStateSchema = z.object({
  scrollProgress: z.number().min(0).max(1),
  activeChapter: SceneChapterSchema,
  isReducedMotion: z.boolean(),
  fps: z.number(),
});

// ============================================================================
// 3. Derived Static TypeScript Types (Single Source of Truth)
// ============================================================================

export type BaseEntity = z.infer<typeof BaseEntitySchema>;
export type SceneChapter = z.infer<typeof SceneChapterSchema>;
export type CameraWaypoint = z.infer<typeof CameraWaypointSchema>;
export type CaseStudy = z.infer<typeof CaseStudySchema>;
export type CredentialBadge = z.infer<typeof CredentialBadgeSchema>;
export type CareerMilestone = z.infer<typeof CareerMilestoneSchema>;
export type ContactInquiry = z.infer<typeof ContactInquirySchema>;
export type SceneControllerState = z.infer<typeof SceneControllerStateSchema>;

// ============================================================================
// 4. Boundary Parsers & Type Guard Validators
// ============================================================================

export function parseCaseStudies(data: unknown): CaseStudy[] {
  return z.array(CaseStudySchema).parse(data);
}

export function parseCredentialBadges(data: unknown): CredentialBadge[] {
  return z.array(CredentialBadgeSchema).parse(data);
}

export function parseCareerMilestones(data: unknown): CareerMilestone[] {
  return z.array(CareerMilestoneSchema).parse(data);
}

// ============================================================================
// 5. Unrigged 3D Scan Calibration Constants
// ============================================================================

export const SCAN_MATERIAL = {
  roughness: 0.55,
  metalness: 0.12,
  colorHex: 0xecf0f3,
} as const;
