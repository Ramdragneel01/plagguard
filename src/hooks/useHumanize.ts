import { useCallback, useState } from 'react';
import type { HumanizeLevel, HumanizeResponse } from '../types';
import { humanizeText } from '../services/api';

export function useHumanize() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<HumanizeResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const humanize = useCallback(
        async (text: string, level: HumanizeLevel = 'moderate', keywords: string[] = []) => {
            setLoading(true);
            setError(null);
            try {
                const res = await humanizeText(text, level, keywords);
                setResult(res);
            } catch (err: any) {
                setError(err.message || 'Humanization failed');
                setResult(null);
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    const reset = useCallback(() => {
        setResult(null);
        setError(null);
    }, []);

    return { loading, result, error, humanize, reset };
}
