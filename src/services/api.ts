import type {
    DetectResponse,
    HumanizeLevel,
    HumanizeResponse,
    PipelineResponse,
} from '../types';

const BASE = '/api/v1';

async function post<T>(url: string, body: unknown): Promise<T> {
    const res = await fetch(`${BASE}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

export async function detectPlagiarism(
    text: string,
    checkWeb = false,
): Promise<DetectResponse> {
    return post<DetectResponse>('/detect', { text, check_web: checkWeb });
}

export async function humanizeText(
    text: string,
    level: HumanizeLevel = 'moderate',
    preserveKeywords: string[] = [],
): Promise<HumanizeResponse> {
    return post<HumanizeResponse>('/humanize', {
        text,
        level,
        preserve_keywords: preserveKeywords,
    });
}

export async function runPipeline(
    text: string,
    level: HumanizeLevel = 'moderate',
    checkWeb = false,
): Promise<PipelineResponse> {
    return post<PipelineResponse>('/pipeline', {
        text,
        humanize_level: level,
        check_web: checkWeb,
    });
}

export async function getReportHtml(reportId: string): Promise<string> {
    const res = await fetch(`${BASE}/reports/${reportId}/html`);
    if (!res.ok) throw new Error('Report not found');
    return res.text();
}
