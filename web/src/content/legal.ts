/**
 * Approved by the founder (D-049). These pages describe how NxtRole is designed to work
 * (docs/PRD.md, docs/SECURITY.md). Check them again before launch (Phase 14). Not legal advice.
 */
export type LegalSection = { heading: string; paragraphs?: string[]; points?: string[] };

export type LegalContent = {
  kicker: string;
  title: string;
  lead: string;
  sections: LegalSection[];
};

export const ABOUT: LegalContent = {
  kicker: "About",
  title: "About NxtRole",
  lead: "A personal job-search assistant for India, built as a personal project.",
  sections: [
    {
      heading: "What it is for",
      paragraphs: [
        "NxtRole is being built to show a short list of real, safe and well-matched jobs each morning, and to help you apply well and follow up.",
      ],
    },
    {
      heading: "How it behaves",
      points: [
        "It never applies, emails or messages anyone for you.",
        "It proposes changes; you approve them, and you can undo them.",
        "It uses official job feeds, your own job emails and jobs you add. It does not scrape sites that need a login.",
        "When it does not know something, it leaves it blank instead of guessing.",
      ],
    },
    {
      heading: "Where it stands",
      paragraphs: [
        "NxtRole is still being built. Some screens describe features that are not ready yet.",
      ],
    },
  ],
};

export const TERMS: LegalContent = {
  kicker: "Terms",
  title: "Terms of use",
  lead: "Plain terms for a personal, non-commercial project.",
  sections: [
    {
      heading: "Who can use it",
      paragraphs: [
        "NxtRole is run by its owner for the owner’s own job search. There is no public sign-up.",
      ],
    },
    {
      heading: "Check before you rely on it",
      points: [
        "Job details come from other websites and may be wrong or out of date. Check the company’s own page.",
        "Scam checks and trust labels are warnings, not guarantees. Never pay a fee or share identity documents to get a job.",
        "Match scores and drafts are made with AI and can be wrong. Read everything before you use it.",
        "Pay estimates are estimates, not tax or legal advice.",
      ],
    },
    {
      heading: "Your part",
      points: [
        "You send applications and messages yourself, and you are responsible for what you send.",
        "Follow the terms of the websites you use.",
      ],
    },
    {
      heading: "No promise of service",
      paragraphs: [
        "NxtRole runs on free services and is provided as it is. It may stop, change or be unavailable at any time, and it does not promise interviews or offers.",
      ],
    },
  ],
};

export const PRIVACY: LegalContent = {
  kicker: "Privacy",
  title: "Privacy notice",
  lead: "What NxtRole is designed to keep, who processes it, and how to remove it.",
  sections: [
    {
      heading: "Today",
      paragraphs: [
        "NxtRole is still being built. This notice describes how it is designed to work once its features are switched on.",
      ],
    },
    {
      heading: "What it keeps",
      points: [
        "Your account email and a one-way hash of your password.",
        "Your resume, the facts you approve from it, and your job preferences.",
        "Jobs you save or skip, applications, interview rounds, notes, offers and drafts.",
        "Contacts from your LinkedIn export if you import it: name, company, title, date and profile link. Email addresses are dropped.",
        "For job emails sent by your Gmail script: the sender’s domain, the subject, the time and what kind of email it was. The email text is not stored.",
      ],
    },
    {
      heading: "AI",
      points: [
        "Your name, phone number, email address and links are removed before any text is sent to an AI provider.",
        "Contacts and the text of your emails are never sent to AI.",
        "The AI provider is Groq. Its data settings are checked before AI features are switched on.",
      ],
    },
    {
      heading: "Other services involved",
      points: [
        "Vercel hosts the app. Supabase stores the database and files. Upstash keeps short-lived counters.",
        "GitHub runs the scheduled searches.",
        "Google: the Gmail script runs in your own account, and Calendar is used only if you connect it.",
        "Your browser’s push service delivers alerts.",
        "Error reporting and AI tracing are optional, off unless set up, and receive data with identity removed.",
      ],
    },
    {
      heading: "How long, and your control",
      points: [
        "Chats are deleted after 30 days. Other data stays until you delete it or its fixed period ends.",
        "You can export all your data, and delete your account and data, from Settings.",
        "NxtRole does not sell data and does not show advertising.",
      ],
    },
  ],
};
