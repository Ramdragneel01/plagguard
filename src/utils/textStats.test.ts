import { describe, expect, it } from 'vitest';

import {
    charCount,
    pctLabel,
    riskBg,
    riskColor,
    sentenceCount,
    wordCount,
} from './textStats';

describe('textStats utilities', () => {
    it('counts words while ignoring repeated whitespace', () => {
        expect(wordCount('  hello   world  from   plagguard ')).toBe(4);
        expect(wordCount('')).toBe(0);
    });

    it('counts characters exactly', () => {
        expect(charCount('abc')).toBe(3);
        expect(charCount('')).toBe(0);
    });

    it('counts non-trivial sentences split by punctuation', () => {
        const sample = 'One short sentence. Another valid sentence! ok?';
        expect(sentenceCount(sample)).toBe(2);
    });

    it('maps risk levels to color classes with sane defaults', () => {
        expect(riskColor('critical')).toContain('text-red-400');
        expect(riskColor('unknown')).toContain('text-slate-400');
    });

    it('maps risk levels to background classes with sane defaults', () => {
        expect(riskBg('high')).toContain('bg-orange-500/10');
        expect(riskBg('other')).toContain('bg-slate-500/10');
    });

    it('formats decimal values as percentage labels', () => {
        expect(pctLabel(0.1234)).toBe('12.3%');
        expect(pctLabel(1)).toBe('100.0%');
    });
});
