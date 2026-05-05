import {
    AlertTriangle,
    CheckCircle,
    FileText,
    Bot,
    BarChart3,
} from 'lucide-react';
import type { DetectResponse } from '../types';
import { ProgressBar } from './ProgressBar';
import { SimilarityHighlight } from './SimilarityHighlight';
import { riskColor, riskBg, pctLabel } from '../utils/textStats';

interface Props {
    result: DetectResponse;
    originalText: string;
}

export function PlagiarismReport({ result, originalText }: Props) {
    const ai = result.ai_detection;
    const stats = result.text_stats;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Score cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className={`card border ${riskBg(result.risk_level)}`}>
                    <div className="flex items-center gap-2 mb-2">
                        {result.risk_level === 'low' ? (
                            <CheckCircle className="w-5 h-5 text-green-400" />
                        ) : (
                            <AlertTriangle className="w-5 h-5 text-red-400" />
                        )}
                        <span className="text-xs text-slate-400 uppercase tracking-wider">
                            Risk Level
                        </span>
                    </div>
                    <p className={`text-2xl font-bold ${riskColor(result.risk_level)}`}>
                        {result.risk_level.toUpperCase()}
                    </p>
                </div>

                <div className="card">
                    <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-5 h-5 text-brand-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">
                            Similarity
                        </span>
                    </div>
                    <p className="text-2xl font-bold">
                        {pctLabel(result.overall_similarity)}
                    </p>
                </div>

                <div className="card">
                    <div className="flex items-center gap-2 mb-2">
                        <Bot className="w-5 h-5 text-purple-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">
                            AI Probability
                        </span>
                    </div>
                    <p className="text-2xl font-bold">{pctLabel(ai.ai_probability)}</p>
                    <p className="text-xs mt-1 text-slate-500">
                        {ai.is_ai_generated ? '🤖 Likely AI' : '✍️ Likely Human'}
                    </p>
                </div>

                <div className="card">
                    <div className="flex items-center gap-2 mb-2">
                        <BarChart3 className="w-5 h-5 text-cyan-400" />
                        <span className="text-xs text-slate-400 uppercase tracking-wider">
                            Flagged
                        </span>
                    </div>
                    <p className="text-2xl font-bold">
                        {result.flagged_sentences.length}
                    </p>
                    <p className="text-xs mt-1 text-slate-500">sentences</p>
                </div>
            </div>

            {/* Progress bars */}
            <div className="card space-y-4">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                    Analysis Breakdown
                </h3>
                <ProgressBar value={result.overall_similarity} label="Plagiarism Score" />
                <ProgressBar
                    value={ai.ai_probability}
                    label="AI Detection Score"
                    color={ai.ai_probability >= 0.55 ? 'bg-purple-500' : 'bg-green-500'}
                />
                <div className="grid grid-cols-2 gap-4 text-sm text-slate-400">
                    <div>
                        Perplexity: <span className="text-slate-200 font-medium">{ai.perplexity_score}</span>
                    </div>
                    <div>
                        Burstiness: <span className="text-slate-200 font-medium">{ai.burstiness_score}</span>
                    </div>
                </div>
            </div>

            {/* Text with highlights */}
            <div className="card">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                    Highlighted Text
                </h3>
                <SimilarityHighlight text={originalText} matches={result.flagged_sentences} />
            </div>

            {/* Flagged sentences table */}
            {result.flagged_sentences.length > 0 && (
                <div className="card overflow-x-auto">
                    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                        Flagged Sentences
                    </h3>
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-slate-700 text-left text-xs text-slate-500 uppercase">
                                <th className="py-2 pr-4">#</th>
                                <th className="py-2 pr-4">Sentence</th>
                                <th className="py-2 pr-4">Score</th>
                                <th className="py-2">Source</th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.flagged_sentences.map((m, i) => (
                                <tr key={i} className="border-b border-slate-800/50">
                                    <td className="py-2 pr-4 text-slate-500">{i + 1}</td>
                                    <td className="py-2 pr-4 max-w-[300px] truncate">
                                        {m.sentence}
                                    </td>
                                    <td className="py-2 pr-4 font-medium text-red-400">
                                        {pctLabel(m.similarity_score)}
                                    </td>
                                    <td className="py-2 text-xs text-slate-500 max-w-[200px] truncate">
                                        {m.matched_source || '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Text stats */}
            <div className="card">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                    Text Statistics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
                    <div>
                        <p className="text-2xl font-bold text-brand-400">{stats.word_count}</p>
                        <p className="text-xs text-slate-500">Words</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-brand-400">{stats.sentence_count}</p>
                        <p className="text-xs text-slate-500">Sentences</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-brand-400">{stats.avg_sentence_length}</p>
                        <p className="text-xs text-slate-500">Avg Length</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-brand-400">{pctLabel(stats.unique_word_ratio)}</p>
                        <p className="text-xs text-slate-500">Unique Words</p>
                    </div>
                    <div>
                        <p className="text-2xl font-bold text-brand-400">{stats.readability_score}</p>
                        <p className="text-xs text-slate-500">Readability</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
