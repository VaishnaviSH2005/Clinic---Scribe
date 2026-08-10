import { API_BASE_URL, API_VERSION_PREFIX } from "@/constants/api";
import type { ApiListResponse, ApiResponse, Pagination } from "@/types/api";

export class ApiClientError extends Error {
  errorCode: string;
  status: number;

  constructor(message: string, errorCode: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.errorCode = errorCode;
    this.status = status;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

const NO_RETRY_PATHS = new Set(["/auth/refresh", "/auth/login"]);

/**
 * Silently refreshes the session on a 401 (PRD Ch19 — "Automatic Session
 * Refresh... transparent to the user"). Never called recursively; a failed
 * refresh simply lets the original 401 propagate so the caller can redirect
 * to /login.
 */
async function tryRefresh(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}${API_VERSION_PREFIX}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function rawRequest(path: string, options: RequestOptions): Promise<Response> {
  const { body, headers, ...rest } = options;
  return fetch(`${API_BASE_URL}${API_VERSION_PREFIX}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

/** No Content-Type header — the browser sets the multipart boundary itself. */
async function rawFormRequest(path: string, formData: FormData): Promise<Response> {
  return fetch(`${API_BASE_URL}${API_VERSION_PREFIX}${path}`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
}

async function requestForm<T>(path: string, formData: FormData, _retried = false): Promise<T> {
  const response = await rawFormRequest(path, formData);

  if (response.status === 401 && !_retried) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return requestForm<T>(path, formData, true);
    }
  }

  const payload = (await response.json().catch(() => null)) as ApiResponse<T> | null;

  if (!response.ok || !payload || payload.success === false) {
    throw new ApiClientError(
      payload?.success === false ? payload.message : "An unexpected error occurred.",
      payload?.success === false ? payload.errorCode : "UNKNOWN_ERROR",
      response.status,
    );
  }

  return payload.data;
}

/**
 * Thin fetch wrapper. Business features must call this only through a
 * feature-level `*.service.ts` file (PRD Ch4.4 services/ rules) — never
 * directly from components. Auth cookies are sent automatically via
 * `credentials: "include"`; no tokens are ever read/stored on the client.
 */
async function request<T>(
  path: string,
  options: RequestOptions = {},
  _retried = false,
): Promise<T> {
  const response = await rawRequest(path, options);

  if (response.status === 401 && !_retried && !NO_RETRY_PATHS.has(path)) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request<T>(path, options, true);
    }
  }

  const payload = (await response.json().catch(() => null)) as ApiResponse<T> | null;

  if (!response.ok || !payload || payload.success === false) {
    throw new ApiClientError(
      payload?.success === false ? payload.message : "An unexpected error occurred.",
      payload?.success === false ? payload.errorCode : "UNKNOWN_ERROR",
      response.status,
    );
  }

  return payload.data;
}

async function requestList<T>(
  path: string,
  options: RequestOptions = {},
  _retried = false,
): Promise<{ data: T[]; pagination: Pagination }> {
  const response = await rawRequest(path, options);

  if (response.status === 401 && !_retried && !NO_RETRY_PATHS.has(path)) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return requestList<T>(path, options, true);
    }
  }

  const payload = (await response.json().catch(() => null)) as ApiListResponse<T> | null;

  if (!response.ok || !payload || payload.success === false) {
    throw new ApiClientError(
      payload?.success === false ? payload.message : "An unexpected error occurred.",
      payload?.success === false ? payload.errorCode : "UNKNOWN_ERROR",
      response.status,
    );
  }

  return { data: payload.data, pagination: payload.pagination };
}

export const apiClient = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  getList: <T>(path: string, options?: RequestOptions) =>
    requestList<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
  postForm: <T>(path: string, formData: FormData) => requestForm<T>(path, formData),
};
