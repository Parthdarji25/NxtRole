import { z } from "zod";

// Limits only guard against nonsense. Whether a password is right is decided by the API (Phase 4).
export const loginSchema = z.object({
  email: z
    .string()
    .trim()
    .max(254, "Enter a valid email address.")
    .pipe(z.email("Enter a valid email address.")),
  password: z.string().min(1, "Enter your password.").max(200, "That password is too long."),
});

export type LoginValues = z.infer<typeof loginSchema>;
