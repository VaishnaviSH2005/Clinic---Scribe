import { apiClient } from "@/lib/api-client";
import type {
  AuthUser,
  ChangePasswordPayload,
  ForgotPasswordPayload,
  LoginPayload,
  Profile,
  ProfileUpdatePayload,
  ResetPasswordPayload,
  SessionInfo,
} from "@/types/auth";

export const authService = {
  login: (payload: LoginPayload) => apiClient.post<AuthUser>("/auth/login", payload),
  logout: () => apiClient.post<null>("/auth/logout"),
  me: () => apiClient.get<AuthUser>("/auth/me"),
  getProfile: () => apiClient.get<Profile>("/auth/profile"),
  updateProfile: (payload: ProfileUpdatePayload) =>
    apiClient.patch<Profile>("/auth/profile", payload),
  forgotPassword: (payload: ForgotPasswordPayload) =>
    apiClient.post<null>("/auth/forgot-password", payload),
  resetPassword: (payload: ResetPasswordPayload) =>
    apiClient.post<null>("/auth/reset-password", payload),
  changePassword: (payload: ChangePasswordPayload) =>
    apiClient.post<null>("/auth/change-password", payload),
  listSessions: () => apiClient.get<SessionInfo[]>("/auth/sessions"),
  revokeSession: (sessionId: string) => apiClient.delete<null>(`/auth/sessions/${sessionId}`),
};
