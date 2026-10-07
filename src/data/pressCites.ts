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
    source: 'The Star (StarEdu)',
    title: '"To the Land of the Alps, we go!"',
    date: '18 August 2024',
    badge: 'National Front Page',
    url: 'https://www.thestar.com.my/news/education/2024/08/18/to-the-land-of-the-alps-we-go',
    quote:
      'Team Sweetzerland emerged global champions of the 13th Hilti IT Competition... pitching Hireti, a platform tailored to enhance talent acquisition and bridge skill gaps.',
    description:
      'Published on the front page of StarEdu in The Star, Malaysia’s premier English daily newspaper. The feature chronicles Zachary Ang’s strategic leadership guiding Team Sweetzerland through multi-stage competitive rounds to triumph over 53 international university teams from across Europe, North America, and APAC.',
    highlights: [
      '1st Place out of 53 teams worldwide (Unanimous jury verdict)',
      'Platform: Hireti — Sustainable AI Workforce & Green Skills Gap Engine',
      'All-expenses-paid executive tour to Hilti Corporation HQ in Schaan, Liechtenstein',
      'Alpine summit excursion scaling Mount Pilatus (2,128m) in Lucerne, Switzerland (Nov 2024)',
    ],
  },
  {
    id: 'cite-apu-news',
    source: 'APU Official Media Release',
    title: '"Back-to-Back Wins for APU Students at Hilti IT Competition"',
    date: '20 June 2024',
    badge: 'University Media Release',
    url: 'https://apu.edu.my/news/back-back-wins-apu-students-hilti-it-competition',
    quote:
      'Marking a historic milestone, APU became the first tertiary institution worldwide to secure consecutive victories. Team Sweetzerland, led by Zachary Ang Zi Yang, triumphed over 53 international university teams.',
    description:
      'Asia Pacific University official institutional release celebrating Team Sweetzerland’s victory. The article highlights Zachary Ang’s role in balancing technical software engineering with rigorous product discovery, pitching Hireti directly before Hilti’s Global Corporate IT Leadership Council in Schaan, Liechtenstein.',
    highlights: [
      'First tertiary institution globally to achieve back-to-back championship titles',
      'Team Lead: Zachary Ang Zi Yang (BSc Business Information Systems & Diploma Software Engineering)',
      'Featured live presentations before Hilti CIO and European corporate IT directors',
    ],
  },
  {
    id: 'cite-hilti-itc',
    source: 'Hilti Corporation (Corporate Portal)',
    title: 'Hilti IT Competition 2024 Global Championship',
    date: 'June 2024',
    badge: 'Corporate Championship Portal',
    url: 'https://itcompetition.hilti.group/',
    quote:
      'The 13th Hilti IT Competition attracted 53 international university submissions competing to build cutting-edge IT solutions for global industry challenges.',
    description:
      'Official Hilti corporate IT competition platform documenting competition rules, executive jury standards, and global championship expedition awards.',
    highlights: [
      'Organized by Hilti Corporation (HQ in Schaan, Liechtenstein)',
      'Evaluated by Hilti CIO and European Corporate IT Leadership',
      'Grand Champion prize: Sponsored expedition to Hilti IT HQ in Switzerland and Liechtenstein',
    ],
  },
  {
    id: 'cite-hilti-hq',
    source: 'Hilti Corporation Executive Expedition',
    title: 'Hilti HQ Executive Presentation & Swiss Alps Summit Ascent',
    date: '12 – 19 November 2024',
    badge: 'Corporate Record',
    url: 'https://apu.edu.my/news/back-back-wins-apu-students-hilti-it-competition',
    quote:
      'Executive technical symposium at Hilti Global IT Headquarters in Schaan, Liechtenstein, followed by high-altitude summit excursion at Mount Pilatus (2,128m).',
    description:
      'The grand prize expedition awarded to Team Sweetzerland: a 7-day all-expenses-paid technical tour across Liechtenstein and Switzerland. The team met with corporate IT leadership, explored global cloud infrastructure, and scaled Mount Pilatus.',
    highlights: [
      'Private technical sessions with Hilti CIO and Enterprise Architecture council',
      'Mount Pilatus alpine ascent and Lucerne cultural exchange',
      'Trophy conferral ceremony in Schaan, Liechtenstein',
    ],
  },
];
