export function wordCount(text: string): number {
    return text.trim().split(/\s+/).filter(Boolean).length;
}

export function charCount(text: string): number {
    return text.length;
}

export function sentenceCount(text: string): number {
    return text.split(/[.!?]+/).filter((s) => s.trim().length > 3).length;
}

export function riskColor(risk: string): string {
    const map: Record<string, string> = {
        low: 'text-green-400',
        medium: 'text-yellow-400',
        high: 'text-orange-400',
        critical: 'text-red-400',
    };
    return map[risk] || 'text-slate-400';
}

export function riskBg(risk: string): string {
    const map: Record<string, string> = {
        low: 'bg-green-500/10 border-green-500/30',
        medium: 'bg-yellow-500/10 border-yellow-500/30',
        high: 'bg-orange-500/10 border-orange-500/30',
        critical: 'bg-red-500/10 border-red-500/30',
    };
    return map[risk] || 'bg-slate-500/10 border-slate-500/30';
}

export function pctLabel(value: number): string {
    return `${(value * 100).toFixed(1)}%`;
}
