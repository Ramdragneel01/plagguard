import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  detectPlagiarism,
  getReportHtml,
  humanizeText,
  runPipeline,
} from './api';

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('api service', () => {
  it('sends detect request with expected payload shape', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ report_id: 'r1' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await detectPlagiarism('This is a valid sentence with enough characters.', true);

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/detect',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body).toEqual({
      text: 'This is a valid sentence with enough characters.',
      check_web: true,
    });
  });

  it('sends humanize request with preserve keywords', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ humanized_text: 'ok' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await humanizeText('Input text long enough for processing.', 'heavy', ['LLM', 'API']);

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.level).toBe('heavy');
    expect(body.preserve_keywords).toEqual(['LLM', 'API']);
  });

  it('throws backend detail on failed pipeline request', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'request_validation_failed' }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      runPipeline('Input text long enough for processing.', 'moderate', false),
    ).rejects.toThrow('request_validation_failed');
  });

  it('throws report-not-found style error for html fetch', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      text: async () => '',
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(getReportHtml('missing')).rejects.toThrow('Report not found');
  });
});
