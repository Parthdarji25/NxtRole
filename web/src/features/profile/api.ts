/** The calls about resumes and the profile, and the names their answers are kept under. */
import { api } from "@/lib/api";
import { send, SLOW_TIMEOUT_MILLISECONDS } from "@/lib/http";

import { contentTypeOf } from "./resumeFile";
import type { Detected, FileWarning, Identity, Profile, Reading, ResumeFile } from "./types";

export const PROFILE = ["profile"];
export const PRIVACY = ["privacy"];

export type StoredFile = ResumeFile & { hidden_identity: Identity | null };

export type CheckedFile = {
  file: StoredFile;
  detected: Detected;
  warnings: FileWarning[];
  duplicate: boolean;
};

export type PrivacyInfo = {
  zero_data_retention_confirmed_on: string | null;
  status: "normal" | "using_backup" | "limits_used" | "not_set_up" | "privacy_not_confirmed";
};

export const getProfile = () => api<Profile>("/api/profile");
export const getPrivacy = () => api<PrivacyInfo>("/api/settings/privacy");
export const getFile = (id: string) => api<StoredFile>(`/api/files/${id}`);

/**
 * Uploads a resume in three steps (D-029): ask for a one-file address, send the file there,
 * then have the API check it and read its text.
 */
export async function uploadResume(file: File, onSent: () => void): Promise<CheckedFile> {
  const type = contentTypeOf(file.name) ?? file.type;
  const upload = await api<{ file_id: string; upload_url: string }>("/api/files/uploads", {
    method: "POST",
    body: { filename: file.name.slice(0, 300), content_type: type, size: file.size },
  });
  // The address carries its own pass, so the sign-in is not sent with it.
  await send(upload.upload_url, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": type },
    timeout: SLOW_TIMEOUT_MILLISECONDS,
  });
  onSent();
  return api<CheckedFile>(`/api/files/${upload.file_id}/complete`, {
    method: "POST",
    timeout: SLOW_TIMEOUT_MILLISECONDS,
  });
}

export const startReading = (fileId: string, hide: Identity) =>
  api<Reading>("/api/profile/parse", { method: "POST", body: { file_id: fileId, hide } });

export const retryReading = (jobId: string) =>
  api<Reading>(`/api/profile/parse/${jobId}/retry`, { method: "POST" });
