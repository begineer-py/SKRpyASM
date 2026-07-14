import axios from 'axios';
import { GLOBAL_CONFIG } from '../config';
import { extractApiError } from '../utils/errors';

export { extractApiError } from '../utils/errors';

interface AxiosErrorShape {
  isAxiosError?: boolean;
  response?: {
    data?: unknown;
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
 * Create an axios instance with standardized config and error normalization.
 *
 * - baseURL derived from GLOBAL_CONFIG.DJANGO_API_BASE + basePath
 * - Content-Type: application/json header
 * - Response interceptor normalizes error.message from API response data
 */
export function createApiClient(basePath: string) {
  const client = axios.create({
    baseURL: `${GLOBAL_CONFIG.DJANGO_API_BASE}/${basePath}`,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.response.use(
    (response) => response,
    (error: unknown): Promise<never> => {
      if (isAxiosErrorShape(error) && error.response) {
        const normalized = extractApiError(error);
        if (normalized !== error.message) {
          error.message = normalized;
        }
      }
      return Promise.reject(error);
    },
  );

  return client;
}

/**
 * Convenience factory for /api/core/ endpoints.
 * Optional subPath appends to core/ (e.g. "vulnerabilities" → /api/core/vulnerabilities).
 */
export function createCoreClient(subPath = '') {
  const path = subPath ? `core/${subPath}` : 'core';
  return createApiClient(path);
}
