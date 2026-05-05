import { useCallback, useState } from 'react';
import type { HumanizeLevel, PipelineResponse } from '../types';
import { runPipeline } from '../services/api';

export function usePipeline() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<PipelineResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const run = useCallback(
        async (text: string, level: HumanizeLevel = 'moderate', checkWeb = false) => {
            setLoading(true);
            setError(null);
            try {
                const res = await runPipeline(text, level, checkWeb);
                setResult(res);
            } catch (err: any) {
                setError(err.message || 'Pipeline failed');
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

    return { loading, result, error, run, reset };
}
