import { ArrowRight, Sparkles, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import type { HumanizeResponse } from '../types';
import { ProgressBar } from './ProgressBar';
import { pctLabel } from '../utils/textStats';

interface Props {
    result: HumanizeResponse;
}

export function HumanizePanel({ result }: Props) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        await navigator.clipboard.writeText(result.humanized_text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const before = result.ai_detection_before;
    const after = result.ai_detection_after;
    const improvement =
        before.ai_probability > 0
            ? ((before.ai_probability - after.ai_probability) / before.ai_probability) * 100
            : 0;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Improvement banner */}
            <div className="card border border-green-500/20 bg-green-500/5">
                <div className="flex items-center gap-3">
                    <Sparkles className="w-6 h-6 text-green-400" />
                    <div>
                        <p className="font-semibold text-green-300">
                            {improvement > 0
                                ? `AI score reduced by ${improvement.toFixed(1)}%`
                                : 'Text humanized successfully'}
                        </p>
                        <p className="text-sm text-slate-400">
                            {result.changes_made} word-level changes · Level:{' '}
                            <span className="capitalize text-slate-300">{result.level}</span>
                        </p>
                    </div>
                </div>
            </div>

            {/* AI detection comparison */}
            <div className="grid md:grid-cols-2 gap-4">
                <div className="card">
                    <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
                        Before Humanization
                    </h3>
                    <ProgressBar
                        value={before.ai_probability}
                        label="AI Probability"
                        color={before.ai_probability >= 0.55 ? 'bg-red-500' : 'bg-green-500'}
                    />
                    <p className="text-sm mt-2 text-slate-400">
                        {before.is_ai_generated ? '🤖 Detected as AI' : '✍️ Detected as Human'}
                    </p>
                </div>
                <div className="card">
                    <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
                        After Humanization
                    </h3>
                    <ProgressBar
                        value={after.ai_probability}
                        label="AI Probability"
                        color={after.ai_probability >= 0.55 ? 'bg-red-500' : 'bg-green-500'}
                    />
                    <p className="text-sm mt-2 text-slate-400">
                        {after.is_ai_generated ? '🤖 Still flagged as AI' : '✍️ Now reads as Human'}
                    </p>
                </div>
            </div>

            {/* Side-by-side comparison */}
            <div className="grid md:grid-cols-2 gap-4">
                <div className="card">
                    <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
                        Original
                    </h3>
                    <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">
                        {result.original_text}
                    </p>
                </div>
                <div className="card relative">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-xs uppercase tracking-wider text-slate-500">
                            Humanized
                        </h3>
                        <button
                            onClick={handleCopy}
                            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
                        >
                            {copied ? (
                                <>
                                    <Check className="w-3.5 h-3.5 text-green-400" /> Copied
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3.5 h-3.5" /> Copy
                                </>
                            )}
                        </button>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                        {result.humanized_text}
                    </p>
                </div>
            </div>
        </div>
    );
}
