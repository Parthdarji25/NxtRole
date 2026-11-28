/**
 * The accounts of the browser tests. They exist only in the throw-away test database, which
 * is built again for every run, and their password is new every time.
 */
export const EMAILS = {
  /** Used to look at screens. Nothing changes its data. */
  owner: "owner@example.com",
  /** Changed freely by the account tests. */
  editor: "editor@example.com",
  /** Signed out everywhere, given a new password and recovered. */
  careful: "careful@example.com",
  /** One each for the account screen's pictures, so that each shows one device. */
  "desktop-light": "desktop-light@example.com",
  "desktop-dark": "desktop-dark@example.com",
  "phone-light": "phone-light@example.com",
  "phone-dark": "phone-dark@example.com",
} as const;

export type Account = keyof typeof EMAILS;

export const password = (): string => process.env.E2E_PASSWORD!;
export const recoveryCode = (): string => process.env.E2E_RECOVERY_CODE!;
