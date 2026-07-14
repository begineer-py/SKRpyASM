function isRecord(value: unknown): value is Record<PropertyKey, unknown> {
  return typeof value === 'object' && value !== null;
}

function extractMessageFromData(data: unknown): string | undefined {
  if (!isRecord(data)) return undefined;
  if (typeof data.detail === 'string') return data.detail;
  if (typeof data.message === 'string') return data.message;
  return undefined;
}

interface AxiosErrorShape {
  isAxiosError?: boolean;
  response?: {
    data?: unknown;
    status?: number;
  };
  message?: string;
}

function getAxiosFlag(error: object): boolean | undefined {
  if ('isAxiosError' in error) {
    const value = error['isAxiosError'];
    return typeof value === 'boolean' ? value : undefined;
  }
  return undefined;
}

function isAxiosErrorShape(error: unknown): error is AxiosErrorShape {
  if (typeof error !== 'object' || error === null) return false;
  return getAxiosFlag(error) === true;
}

/**
 * Extract a human-readable error message from an unknown error value.
 *
 * Handles:
 *  - AxiosError with response.data.detail (Django Ninja ErrorSchema)
 *  - AxiosError with response.data.message (legacy pattern)
 *  - AxiosError with response.data (stringify non-standard payloads)
 *  - AxiosError without response (network / timeout errors)
 *  - Generic Error instances
 *  - Unknown values (returns fallback)
 */
export function extractApiError(error: unknown, fallback = '請求失敗'): string {
  if (isAxiosErrorShape(error)) {
    const responseMessage = extractMessageFromData(error.response?.data);
    if (responseMessage) return responseMessage;

    const data = error.response?.data;
    if (data !== undefined && data !== null) {
      if (typeof data === 'string') return data;
      try {
        return JSON.stringify(data);
      } catch {
        return fallback;
      }
    }

    if (error.message) return error.message;
    return fallback;
  }

  if (error instanceof Error) return error.message;
  return fallback;
}

/**
 * Typed API error carrying HTTP status and response payload.
 * Use with extractApiError for message extraction.
 */
export class ApiError extends Error {
  readonly status?: number;
  readonly data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}
