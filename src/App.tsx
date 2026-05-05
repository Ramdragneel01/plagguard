import { useState } from 'react';
import {
    Search,
    Wand2,
    Workflow,
    Loader2,
    RotateCcw,
    Globe,
} from 'lucide-react';

import { Header } from './components/Header';
import { TextInput } from './components/TextInput';
import { PlagiarismReport } from './components/PlagiarismReport';
import { HumanizePanel } from './components/HumanizePanel';
import { PipelineResult } from './components/PipelineResult';

import { usePlagiarismCheck } from './hooks/usePlagiarismCheck';
import { useHumanize } from './hooks/useHumanize';
import { usePipeline } from './hooks/usePipeline';

import type { HumanizeLevel, TabKey } from './types';

const TABS: { key: TabKey; label: string; icon: typeof Search; desc: string }[] = [
    { key: 'detect', label: 'Detect', icon: Search, desc: 'Scan for plagiarism & AI' },
    { key: 'humanize', label: 'Humanize', icon: Wand2, desc: 'Make text sound human' },
    { key: 'pipeline', label: 'Full Pipeline', icon: Workflow, desc: 'Detect → Fix → Verify' },
];

export default function App() {
    const [text, setText] = useState('');
    const [tab, setTab] = useState<TabKey>('detect');
    const [level, setLevel] = useState<HumanizeLevel>('moderate');
    const [checkWeb, setCheckWeb] = useState(false);

    const detect = usePlagiarismCheck();
    const humanize = useHumanize();
    const pipeline = usePipeline();

    const isLoading = detect.loading || humanize.loading || pipeline.loading;
    const hasResult = !!(detect.result || humanize.result || pipeline.result);
    const error = detect.error || humanize.error || pipeline.error;

    const handleSubmit = () => {
        if (!text.trim() || text.length < 20) return;
        switch (tab) {
            case 'detect':
                detect.check(text, checkWeb);
                break;
            case 'humanize':
                humanize.humanize(text, level);
                break;
            case 'pipeline':
                pipeline.run(text, level, checkWeb);
                break;
        }
    };

    const handleReset = () => {
        setText('');
        detect.reset();
        humanize.reset();
        pipeline.reset();
    };

    return (
        <div className="min-h-screen flex flex-col">
            <Header />

            <main className="flex-1 max-w-6xl mx-auto w-full px-4 py-8 space-y-8">
                {/* Tab selector */}
                <div className="grid grid-cols-3 gap-3">
                    {TABS.map((t) => {
                        const Icon = t.icon;
                        const active = tab === t.key;
                        return (
                            <button
                                key={t.key}
                                onClick={() => {
                                    setTab(t.key);
                                    detect.reset();
                                    humanize.reset();
                                    pipeline.reset();
                                }}
                                className={`card flex items-center gap-3 transition-all duration-200 cursor-pointer
                  ${active ? 'border-brand-500 bg-brand-500/10 ring-1 ring-brand-500/30' : 'hover:border-slate-600'}`}
                            >
                                <Icon className={`w-5 h-5 ${active ? 'text-brand-400' : 'text-slate-500'}`} />
                                <div className="text-left">
                                    <p className={`font-semibold text-sm ${active ? 'text-brand-300' : 'text-slate-300'}`}>
                                        {t.label}
                                    </p>
                                    <p className="text-xs text-slate-500">{t.desc}</p>
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Input area */}
                <div className="card">
                    <TextInput
                        value={text}
                        onChange={setText}
                        placeholder={
                            tab === 'detect'
                                ? 'Paste text to check for plagiarism and AI-generated content…'
                                : tab === 'humanize'
                                    ? 'Paste AI-generated text to humanize…'
                                    : 'Paste text to detect, humanize, and re-verify…'
                        }
                        disabled={isLoading}
                    />

                    {/* Controls */}
                    <div className="flex flex-wrap items-center gap-4 mt-4">
                        {(tab === 'humanize' || tab === 'pipeline') && (
                            <div className="flex items-center gap-2">
                                <label className="text-xs text-slate-500">Level:</label>
                                <select
                                    value={level}
                                    onChange={(e) => setLevel(e.target.value as HumanizeLevel)}
                                    className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-sm
                             text-slate-200 focus:outline-none focus:ring-1 focus:ring-brand-500"
                                >
                                    <option value="light">Light</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="heavy">Heavy</option>
                                </select>
                            </div>
                        )}

                        {(tab === 'detect' || tab === 'pipeline') && (
                            <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={checkWeb}
                                    onChange={(e) => setCheckWeb(e.target.checked)}
                                    className="rounded bg-slate-800 border-slate-600 text-brand-500
                             focus:ring-brand-500 focus:ring-offset-0"
                                />
                                <Globe className="w-4 h-4" />
                                Check web sources
                            </label>
                        )}

                        <div className="flex-1" />

                        {hasResult && (
                            <button onClick={handleReset} className="btn-secondary flex items-center gap-2">
                                <RotateCcw className="w-4 h-4" /> Reset
                            </button>
                        )}

                        <button
                            onClick={handleSubmit}
                            disabled={isLoading || text.trim().length < 20}
                            className="btn-primary flex items-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" /> Analysing…
                                </>
                            ) : (
                                <>
                                    {tab === 'detect' && <Search className="w-4 h-4" />}
                                    {tab === 'humanize' && <Wand2 className="w-4 h-4" />}
                                    {tab === 'pipeline' && <Workflow className="w-4 h-4" />}
                                    {tab === 'detect' ? 'Scan Text' : tab === 'humanize' ? 'Humanize' : 'Run Pipeline'}
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="card border border-red-500/30 bg-red-500/5 text-red-300 text-sm">
                        ⚠️ {error}
                    </div>
                )}

                {/* Results */}
                {detect.result && <PlagiarismReport result={detect.result} originalText={text} />}
                {humanize.result && <HumanizePanel result={humanize.result} />}
                {pipeline.result && <PipelineResult result={pipeline.result} originalText={text} />}
            </main>

            <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-600">
                PlagGuard v1.0.0 — Plagiarism Detection · AI Detection · Text Humanization
            </footer>
        </div>
    );
}
