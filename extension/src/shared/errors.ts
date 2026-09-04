export const THEME_ERROR_CODES = [
  "THEME_NOT_FOUND",
  "THEME_INVALID",
  "THEME_UNSUPPORTED_COLOR",
  "CALLER_FORBIDDEN",
  "PROTOCOL_MISMATCH",
] as const;

export type ThemeErrorCode = (typeof THEME_ERROR_CODES)[number];

export const CONNECTION_ERROR_CODES = [
  "HOST_NOT_FOUND",
  "HOST_DISCONNECTED",
  "HOST_PROTOCOL_ERROR",
  "HOST_MESSAGE_INVALID",
] as const;

export type ConnectionErrorCode = (typeof CONNECTION_ERROR_CODES)[number];
