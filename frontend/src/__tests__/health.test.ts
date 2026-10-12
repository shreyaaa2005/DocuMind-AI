import { describe, it, expect, vi } from 'vitest';
import { getBackendRootUrl, apiClient, BACKEND_ROOT_URL } from '../api/client';
import { checkBackendHealth } from '../api/qa';

describe('Backend health-check URL and root resolution', () => {
  it('correctly derives root server URL from API base URL', () => {
    expect(getBackendRootUrl('http://localhost:8000/api/v1')).toBe('http://localhost:8000');
    expect(getBackendRootUrl('http://localhost:8000/api/v1/')).toBe('http://localhost:8000');
    expect(getBackendRootUrl('http://127.0.0.1:8000/api/v1')).toBe('http://127.0.0.1:8000');
    expect(getBackendRootUrl('https://api.documind.ai/api/v1')).toBe('https://api.documind.ai');
    expect(getBackendRootUrl('/api/v1')).toBe('');
  });

  it('ensures checkBackendHealth requests /health using BACKEND_ROOT_URL', async () => {
    const getSpy = vi.spyOn(apiClient, 'get').mockResolvedValueOnce({
      data: { status: 'healthy' },
    } as any);

    const result = await checkBackendHealth();

    expect(result).toEqual({ status: 'healthy' });
    expect(getSpy).toHaveBeenCalledTimes(1);

    const [url, config] = getSpy.mock.calls[0];
    expect(url).toBe('/health');
    expect(config?.baseURL).toBe(BACKEND_ROOT_URL);

    // Verify it does not request /api/v1/health or duplicate path
    expect(url).not.toBe('/api/v1/health');
    expect(url).not.toContain('api/v1');

    getSpy.mockRestore();
  });
});
