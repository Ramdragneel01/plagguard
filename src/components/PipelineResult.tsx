import { ArrowDownUp, TrendingDown, Sparkles } from 'lucide-react';
import type { PipelineResponse } from '../types';
import { PlagiarismReport } from './PlagiarismReport';
import { pctLabel } from '../utils/textStats';
import { useState, useCallback } from 'react';

interface Props {
    result: PipelineResponse;
    originalText: string;
}

export function PipelineResult({ result, originalText }: Props) {
    const [view, setView] = useState<'before' | 'after'>('after');

    const copyText = useCallback(async () => {
        await navigator.clipboard.writeText(result.humanized_text);
    }, [result.humanized_text]);

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Improvement hero */}
            <div className="card border border-brand-500/20 bg-brand-500/5">
                <div className="flex flex-col md:flex-row items-center gap-6">
                    <div className="flex items-center gap-4">
                        <div className="text-center">
                            <p className="text-xs text-slate-500 uppercase">Before</p>
                            <p className="text-3xl font-bold text-red-400">
                                {pctLabel(result.original_detection.overall_similarity)}
                            </p>
                        </div>
                        <ArrowDownUp className="w-6 h-6 text-slate-500" />
                        <div className="text-center">
                            <p className="text-xs text-slate-500 uppercase">After</p>
                            <p className="text-3xl font-bold text-green-400">
                                {pctLabel(result.post_humanize_detection.overall_similarity)}
                            </p>
                        </div>
                    </div>
                    <div className="flex-1 text-center md:text-left">
                        <p className="flex items-center gap-2 text-lg font-semibold text-brand-300">
                            <TrendingDown className="w-5 h-5" />
                            {result.improvement_percent.toFixed(1)}% Overall Improvement
                        </p>
                        <p className="text-sm text-slate-400">
                            AI probability:{' '}
                            {pctLabel(result.original_detection.ai_detection.ai_probability)}{' '}
                            → {pctLabel(result.post_humanize_detection.ai_detection.ai_probability)}
                        </p>
                    </div>
                    <button onClick={copyText} className="btn-primary flex items-center gap-2">
                        <Sparkles className="w-4 h-4" /> Copy Clean Text
                    </button>
                </div>
            </div>

            {/* Tab toggle */}
            <div className="flex gap-2">
                <button
                    onClick={() => setView('before')}
                    className={`btn-secondary text-sm ${view === 'before' ? 'bg-slate-700 border-brand-500' : ''}`}
                >
                    Original Analysis
                </button>
                <button
                    onClick={() => setView('after')}
                    className={`btn-secondary text-sm ${view === 'after' ? 'bg-slate-700 border-brand-500' : ''}`}
                >
                    After Humanization
                </button>
            </div>

            {/* Humanized text preview */}
            {view === 'after' && (
                <div className="card">
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                        Humanized Output
                    </h3>
                    <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                        {result.humanized_text}
                    </p>
                </div>
            )}

            {/* Detection report */}
            <PlagiarismReport
                result={view === 'before' ? result.original_detection : result.post_humanize_detection}
                originalText={view === 'before' ? originalText : result.humanized_text}
            />
        </div>
    );
}
