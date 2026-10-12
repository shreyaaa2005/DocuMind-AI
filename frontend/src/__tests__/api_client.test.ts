import { describe, it, expect } from 'vitest';
import { formatApiError } from '../api/client';
import { AxiosError } from 'axios';

describe('formatApiError', () => {
  it('formats custom string detail from FastAPI response', () => {
    const error = new AxiosError(
      'Request failed',
      '400',
      undefined,
      undefined,
      {
        status: 400,
        statusText: 'Bad Request',
        headers: {},
        config: {} as any,
        data: { detail: 'Only PDF files are supported' },
      }
    );
    expect(formatApiError(error)).toBe('Only PDF files are supported');
  });

  it('formats validation array detail from FastAPI response', () => {
    const error = new AxiosError(
      'Validation failed',
      '422',
      undefined,
      undefined,
      {
        status: 422,
        statusText: 'Unprocessable Entity',
        headers: {},
        config: {} as any,
        data: {
          detail: [
            { loc: ['body', 'question'], msg: 'Field required', type: 'missing' },
          ],
        },
      }
    );
    expect(formatApiError(error)).toBe('Field required');
  });

  it('formats HTTP 401 error', () => {
    const error = new AxiosError('Unauthorized', '401', undefined, undefined, {
      status: 401,
      statusText: 'Unauthorized',
      headers: {},
      config: {} as any,
      data: {},
    });
    expect(formatApiError(error)).toContain('Session expired or unauthenticated');
  });

  it('formats HTTP 413 file size error', () => {
    const error = new AxiosError('Payload Too Large', '413', undefined, undefined, {
      status: 413,
      statusText: 'Payload Too Large',
      headers: {},
      config: {} as any,
      data: {},
    });
    expect(formatApiError(error)).toContain('50MB limit');
  });

  it('formats network connectivity error', () => {
    const error = new AxiosError('Network Error');
    error.code = 'ERR_NETWORK';
    expect(formatApiError(error)).toContain('Could not connect to DocuMind backend server');
  });
});
