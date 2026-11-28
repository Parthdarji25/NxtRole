/** The shapes the API sends for resumes and the profile (docs/API_DOCUMENTATION.md). */

export type FactKind =
  | "experience_years"
  | "role"
  | "achievement"
  | "skill"
  | "project"
  | "education"
  | "certification"
  | "location"
  | "notice_period";

export type Fact = {
  fact_id: string;
  kind: FactKind;
  value: string;
  company: string | null;
  dates: string | null;
  /** The words of the resume that state it. Facts written by the owner have none. */
  quote: string | null;
  source: "resume" | "you";
};

export type Identity = {
  name: string;
  emails: string[];
  phones: string[];
  links: string[];
  addresses: string[];
  other: string[];
};

/** What code found in an uploaded resume. */
export type Detected = Omit<Identity, "name" | "other"> & { name: string | null };

export type FileWarning = "truncated" | "not_english";

export type ResumeFile = {
  id: string;
  name: string;
  content_type: string;
};

export type Version = {
  id: string;
  version_no: number;
  in_use: boolean;
  approved_at: string | null;
  facts: Fact[];
  source_file_id: string | null;
};

export type Summary = {
  experience_years: string | null;
  latest_role: string | null;
  skills: string[];
};

export type Suggestion = {
  proposal_id: string;
  facts: Fact[];
  source_file_id: string | null;
  dropped: number;
  created_at: string;
};

export type Reading = {
  job_id: string;
  file_id: string;
  state: "queued" | "running" | "done" | "failed";
  problem: string | null;
  code: string | null;
};

export type Profile = {
  version: number;
  approved: Version | null;
  summary: Summary | null;
  suggestion: Suggestion | null;
  reading: Reading | null;
};
