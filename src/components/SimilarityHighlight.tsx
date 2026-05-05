import type { SentenceMatch } from '../types';

interface Props {
    text: string;
    matches: SentenceMatch[];
}

export function SimilarityHighlight({ text, matches }: Props) {
    if (matches.length === 0) {
        return <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">{text}</p>;
    }

    // Build highlighted version
    const sorted = [...matches].sort((a, b) => a.start_idx - b.start_idx);
    const parts: { text: string; flagged: boolean; score?: number }[] = [];
    let cursor = 0;

    for (const m of sorted) {
        if (m.start_idx > cursor) {
            parts.push({ text: text.slice(cursor, m.start_idx), flagged: false });
        }
        parts.push({
            text: text.slice(m.start_idx, m.end_idx),
            flagged: true,
            score: m.similarity_score,
        });
        cursor = m.end_idx;
    }
    if (cursor < text.length) {
        parts.push({ text: text.slice(cursor), flagged: false });
    }

    return (
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {parts.map((p, i) =>
                p.flagged ? (
                    <span
                        key={i}
                        className="bg-red-500/20 border-b-2 border-red-400 px-0.5 rounded-sm cursor-help"
                        title={`Similarity: ${((p.score || 0) * 100).toFixed(1)}%`}
                    >
                        {p.text}
                    </span>
                ) : (
                    <span key={i}>{p.text}</span>
                ),
            )}
        </p>
    );
}
