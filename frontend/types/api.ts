// Standard response envelope per PRD Ch16.2. Every API response must conform to this shape.
export interface ApiSuccess<T> {
  success: true;
  data: T;
  message?: string;
}

export interface ApiError {
  success: false;
  message: string;
  errorCode: string;
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
}

export interface ApiListSuccess<T> {
  success: true;
  data: T[];
  pagination: Pagination;
}

export type ApiListResponse<T> = ApiListSuccess<T> | ApiError;
