import { useCallback, useState } from 'react';
import type { DetectResponse } from '../types';
import { detectPlagiarism } from '../services/api';

export function usePlagiarismCheck() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<DetectResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const check = useCallback(async (text: string, checkWeb = false) => {
        setLoading(true);
        setError(null);
        try {
            const res = await detectPlagiarism(text, checkWeb);
            setResult(res);
        } catch (err: any) {
            setError(err.message || 'Detection failed');
            setResult(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const reset = useCallback(() => {
        setResult(null);
        setError(null);
    }, []);

    return { loading, result, error, check, reset };
}
