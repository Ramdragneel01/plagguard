export interface SentenceMatch {
    sentence: string;
    similarity_score: number;
    matched_source: string | null;
    start_idx: number;
    end_idx: number;
}

export interface AIDetectionResult {
    is_ai_generated: boolean;
    ai_probability: number;
    perplexity_score: number;
    burstiness_score: number;
}

export interface TextStats {
    word_count: number;
    sentence_count: number;
    avg_sentence_length: number;
    unique_word_ratio: number;
    readability_score: number;
}

export interface DetectResponse {
    report_id: string;
    overall_similarity: number;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    flagged_sentences: SentenceMatch[];
    ai_detection: AIDetectionResult;
    text_stats: TextStats;
    created_at: string;
}

export interface HumanizeResponse {
    original_text: string;
    humanized_text: string;
    changes_made: number;
    level: 'light' | 'moderate' | 'heavy';
    ai_detection_before: AIDetectionResult;
    ai_detection_after: AIDetectionResult;
}

export interface PipelineResponse {
    report_id: string;
    original_detection: DetectResponse;
    humanized_text: string;
    post_humanize_detection: DetectResponse;
    improvement_percent: number;
    created_at: string;
}

export type HumanizeLevel = 'light' | 'moderate' | 'heavy';
export type TabKey = 'detect' | 'humanize' | 'pipeline';
