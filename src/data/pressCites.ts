export interface PressCite {
  id: string;
  source: string;
  title: string;
  date: string;
  badge: string;
  url: string;
  quote: string;
  description: string;
  highlights: string[];
}

export const PRESS_CITES: PressCite[] = [
  {
    id: 'cite-the-star',
    source: 'The Star (StarEdu National Daily)',
    title: '"To the Land of the Alps, we go!"',
    date: '18 August 2024',
    badge: 'National Front Page',
    url: 'https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go',
    quote:
      'Team Sweetzerland emerged global champions of the 13th Hilti IT Competition... pitching Hireti, a platform tailored to enhance talent acquisition and bridge skill gaps.',
    description:
      'Front-page feature in Malaysia’s premier national English daily newspaper. Chronicles Zachary Ang’s strategic leadership guiding Team Sweetzerland through multi-stage competitive rounds to triumph over 53 international university teams from across Europe, North America, and APAC.',
    highlights: [
      '1st Place out of 53 teams worldwide (Unanimous jury verdict)',
      'Platform: Hireti — Sustainable AI Workforce & Green Skills Gap Engine',
      'All-expenses-paid executive tour to Hilti Corporation HQ in Schaan, Liechtenstein',
      'Alpine summit excursion scaling Mount Pilatus (2,128m) in Lucerne, Switzerland (Nov 2024)',
    ],
  },
  {
    id: 'cite-fusion-acm',
    source: 'APU Media Release & ACM SIGCHI',
    title: '"APU Students Make a Mark on Sustainable Development at Fusion 2023, Winning Silver Award"',
    date: 'September 2023',
    badge: 'ACM SIGCHI Silver Award',
    url: 'https://apu.edu.my/news/apu-students-make-mark-sustainable-development-fusion-2023-winning-gold-and-silver-awards',
    quote:
      'The Silver award was awarded to Lim Wye Yee, Ang Zi Yang, and Angel Wong Yun Yee, who created Satuconnect: Your One-Stop Culture Exchange and Education Hub... infused with immersive AR and gamification.',
    description:
      'Published institutional coverage by Asia Pacific University documenting the 5th National Symposium on Human-Computer Interaction (FUSION 2023) organised by the Kuala Lumpur ACM SIGCHI Chapter (myHCI-UX). Zachary Ang and team won the Silver Award for Satuconnect, advancing UN Sustainable Development Goal 4 (Quality Education) through accessible augmented reality and cultural learning.',
    highlights: [
      'Silver Award at 5th National Symposium on Human-Computer Interaction (FUSION 2023)',
      'Organised by Kuala Lumpur ACM SIGCHI Chapter (myHCI-UX)',
      'Platform: Satuconnect — AR-Infused Cultural Education & Digital Inclusion Platform',
      'Addresses UN SDG 4 (Quality Education) & SDG 10 (Reduced Inequalities)',
    ],
  },
  {
    id: 'cite-great-ai',
    source: 'Great AI Hackathon National Review',
    title: '"Top 10 Finalist: Privacy-First Edge Work Logging Architecture (ChronoAI)"',
    date: 'January 2025',
    badge: 'Corporate AI Top 10',
    url: 'https://github.com/ZacharyAng0309',
    quote:
      'ChronoAI engineered an enterprise privacy-first automated work-logging system utilizing background OS metadata with zero invasive screen capture or keylogging.',
    description:
      'National AI hackathon corporate track finalist recognized for architecting ChronoAI. Evaluated by enterprise tech leadership on data sovereignty, edge ONNX inference latency (<15ms), and automatic reconciliation with Jira and Asana task trees.',
    highlights: [
      'Top 10 Finalist out of hundreds of corporate and enterprise engineering participants',
      'Zero-Knowledge Metadata Harvester: 0 bytes video/screen capture egress',
      'Local ONNX Quantized Model for automated sprint epic categorization',
      'Full compliance with GDPR and enterprise non-disclosure privacy mandates',
    ],
  },
  {
    id: 'cite-petronas-pies',
    source: 'Petronas CHESS Engineering Symposium',
    title: '"Petronas Integrated Exploratory System (PIES) — Upstream Decarbonization (4th Place)"',
    date: 'October 2023',
    badge: 'Engineering Symposium 4th',
    url: 'https://github.com/ZacharyAng0309',
    quote:
      'Formulated an AI-driven predictive optimization engine for upstream oil & gas operations, targeting emissions reduction and exploratory drilling efficiency.',
    description:
      'Selected as 4th Placement overall at the prestigious Petronas CHESS Symposium. Zachary Ang led the systems modeling team to fuse downhole drilling sensor telemetry, acoustic seismic feedback, and predictive machine learning models to reduce unscheduled gas flaring by an estimated 18%.',
    highlights: [
      '4th Placement overall competing against senior collegiate and postgraduate engineering teams',
      'Predictive Flaring Early Warning: ML models alerting drill engineers to pressure anomalies',
      'Direct presentation before Petronas Digital leadership and academic engineering panels',
      'Multimodal drillhead telemetry and IoT sensor data fusion',
    ],
  },
  {
    id: 'cite-apu-news',
    source: 'APU Official Media Release',
    title: '"Back-to-Back Wins for APU Students at Hilti IT Competition"',
    date: '20 June 2024',
    badge: 'Institutional Historic Record',
    url: 'https://apu.edu.my/news/back-back-wins-apu-students-hilti-it-competition',
    quote:
      'Marking a historic milestone, APU became the first tertiary institution worldwide to secure consecutive victories. Team Sweetzerland, led by Zachary Ang Zi Yang, triumphed over 53 international university teams.',
    description:
      'Asia Pacific University official institutional release celebrating the consecutive championship record. The feature quotes Team Lead Zachary Ang on cross-functional product execution and business benefit modeling presented before Hilti Corporate IT Leadership in Schaan, Liechtenstein.',
    highlights: [
      'First tertiary institution globally to achieve back-to-back championship titles',
      'Team Lead: Zachary Ang Zi Yang (BSc Business Information Systems & Diploma Software Engineering)',
      'Featured live presentations before Hilti CIO and European corporate IT directors',
      'Conferred Vice Chancellor’s Honors List recognition',
    ],
  },
];
