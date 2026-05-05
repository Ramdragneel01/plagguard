import { wordCount, charCount, sentenceCount } from '../utils/textStats';

interface Props {
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
    disabled?: boolean;
}

export function TextInput({ value, onChange, placeholder, disabled }: Props) {
    const words = wordCount(value);
    const chars = charCount(value);
    const sentences = sentenceCount(value);

    return (
        <div className="relative">
            <textarea
                className="input-area min-h-[240px] text-sm leading-relaxed"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder || 'Paste your text here…'}
                disabled={disabled}
                maxLength={50000}
            />
            <div className="flex gap-4 mt-2 text-xs text-slate-500">
                <span>{words} words</span>
                <span>{chars.toLocaleString()} chars</span>
                <span>{sentences} sentences</span>
            </div>
        </div>
    );
}
