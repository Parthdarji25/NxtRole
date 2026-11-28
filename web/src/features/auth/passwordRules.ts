import { z } from "zod";

// The same lengths as the API, which also refuses common passwords.
export const MIN_PASSWORD = 12;
export const MAX_PASSWORD = 128;

export const newPassword = z
  .string()
  .min(MIN_PASSWORD, `Use at least ${MIN_PASSWORD} characters. A short sentence works well.`)
  .max(MAX_PASSWORD, `Use at most ${MAX_PASSWORD} characters.`);

export const NOT_THE_SAME = "The two passwords are not the same.";
