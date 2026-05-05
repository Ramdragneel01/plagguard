"""Text humanization service.

Rewrites text to sound more natural/human while preserving meaning.
Uses LLM APIs (OpenAI or Anthropic) with carefully crafted prompts
for different humanization levels.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Humanization prompts per level ─────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are an expert editor. Your job is to rewrite text so it reads as if "
    "written by a thoughtful human — with natural rhythm, varied sentence "
    "structure, occasional colloquialisms, and genuine voice. "
    "NEVER mention that you are rewriting or humanising. "
    "Preserve the original meaning, facts, and technical accuracy."
)

_LEVEL_INSTRUCTIONS = {
    "light": (
        "Make minimal changes: vary a few sentence openings, replace one or two "
        "formal connectors with simpler alternatives, and add a single natural "
        "aside or short sentence. Keep 90%+ of the original wording intact."
    ),
    "moderate": (
        "Rewrite with a natural human voice: vary sentence lengths significantly, "
        "replace formal connectors (however, moreover, furthermore) with casual "
        "alternatives, add 1-2 personal-sounding observations, occasionally use "
        "contractions, and break up any overly long sentences. Keep the same "
        "structure but change ~40% of the wording."
    ),
    "heavy": (
        "Substantially rewrite from scratch in your own words. Use a conversational "
        "tone, short punchy sentences mixed with longer flowing ones, contractions, "
        "rhetorical questions, and real-world analogies. Make it feel like a blog "
        "post by an experienced practitioner. Preserve all facts and key terms "
        "but change 70%+ of the wording and structure."
    ),
}


def _build_prompt(text: str, level: str, preserve_keywords: list[str]) -> str:
    instruction = _LEVEL_INSTRUCTIONS.get(level, _LEVEL_INSTRUCTIONS["moderate"])
    keywords_note = ""
    if preserve_keywords:
        keywords_note = (
            f"\n\nIMPORTANT: Keep these exact terms/phrases unchanged: "
            f"{', '.join(preserve_keywords)}"
        )
    return (
        f"{instruction}{keywords_note}\n\n"
        f"--- ORIGINAL TEXT ---\n{text}\n--- END ---\n\n"
        "Respond ONLY with the rewritten text. No explanations."
    )


async def _call_openai(system: str, user: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.85,
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


async def _call_anthropic(system: str, user: str) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=settings.llm_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


async def humanize_text(
    text: str,
    level: str = "moderate",
    preserve_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Humanize the given text using the configured LLM provider.

    Returns:
        {
            "humanized_text": str,
            "changes_made": int,  (estimated word-level diffs)
            "level": str,
        }
    """
    if preserve_keywords is None:
        preserve_keywords = []

    prompt = _build_prompt(text, level, preserve_keywords)

    if settings.llm_provider == "anthropic":
        humanized = await _call_anthropic(_SYSTEM_PROMPT, prompt)
    else:
        humanized = await _call_openai(_SYSTEM_PROMPT, prompt)

    # Estimate changes
    original_words = set(re.findall(r"\b\w+\b", text.lower()))
    new_words = set(re.findall(r"\b\w+\b", humanized.lower()))
    changes = len(original_words.symmetric_difference(new_words))

    return {
        "humanized_text": humanized.strip(),
        "changes_made": changes,
        "level": level,
    }


def _fallback_humanize(text: str, level: str = "moderate") -> str:
    """Comprehensive rule-based humanization that targets all 10 AI detection signals.

    Signals targeted:
    - Connector density       → replace formal connectors with casual ones
    - AI signature vocabulary → swap overused AI words for plain alternatives
    - Contraction absence     → inject contractions
    - Personal pronoun scarcity → sprinkle "you", "we", "I"
    - Sentence-length uniformity / burstiness → split long sentences, merge short ones
    - Sentence-start patterns → vary openers, remove formulaic starters
    - Average word length     → replace long formal words with short plain ones
    - Hedging density         → remove/simplify hedging
    """
    result = text

    # ── 1. Replace AI-signature vocabulary with plain alternatives ─────
    ai_word_swaps = [
        # (pattern, replacement) — case-insensitive word-boundary replace
        (r"\bdelve(?:s|ing)?\b", "dig"),
        (r"\btapestry\b", "mix"),
        (r"\bmultifaceted\b", "complex"),
        (r"\bnuanced?\b", "subtle"),
        (r"\blandscape\b", "space"),
        (r"\bcrucial\b", "key"),
        (r"\bpivotal\b", "critical"),
        (r"\bparamount\b", "top"),
        (r"\bfoster(?:s|ing)?\b", "build"),
        (r"\bleverage(?:s|d)?\b", "use"),
        (r"\bleveraging\b", "using"),
        (r"\butilize(?:s|d|tion)?\b", "use"),
        (r"\butilizing\b", "using"),
        (r"\butilization\b", "use"),
        (r"\bfacilitate(?:s|d)?\b", "help"),
        (r"\bfacilitating\b", "helping"),
        (r"\bcomprehensive\b", "thorough"),
        (r"\bintricate\b", "complex"),
        (r"\bintricacies\b", "details"),
        (r"\bnavigate(?:s|d)?\b", "handle"),
        (r"\bnavigating\b", "handling"),
        (r"\bunderscore(?:s|d)?\b", "highlight"),
        (r"\bunderscoring\b", "highlighting"),
        (r"\bencompass(?:es|ed)?\b", "cover"),
        (r"\bencompassing\b", "covering"),
        (r"\bstreamline(?:s|d)?\b", "simplify"),
        (r"\bstreamlining\b", "simplifying"),
        (r"\benhance(?:s|d|ment)?\b", "improve"),
        (r"\benhancing\b", "improving"),
        (r"\brobust\b", "solid"),
        (r"\bseamless(?:ly)?\b", "smooth"),
        (r"\bscalable\b", "flexible"),
        (r"\bgroundbreaking\b", "new"),
        (r"\btransformative\b", "powerful"),
        (r"\bimperative\b", "important"),
        (r"\bindispensable\b", "essential"),
        (r"\bharness(?:es|ed)?\b", "use"),
        (r"\bharnessing\b", "using"),
        (r"\bbolster(?:s|ing|ed)?\b", "strengthen"),
        (r"\bempower(?:s|ing|ed|ment)?\b", "give"),
        (r"\bburgeoning\b", "growing"),
        (r"\bplethora\b", "range"),
        (r"\bmyriad\b", "many"),
        (r"\bsynergy\b", "teamwork"),
        (r"\bparadigm\b", "model"),
        (r"\bholistic\b", "overall"),
        (r"\bproactive(?:ly)?\b", "ahead of time"),
        (r"\bendeavor(?:s|ing|ed)?\b", "effort"),
        (r"\boptimize(?:s|d)?\b", "improve"),
        (r"\boptimizing\b", "improving"),
        (r"\boptimization\b", "tuning"),
        (r"\bmitigate(?:s|d)?\b", "reduce"),
        (r"\bmitigating\b", "reducing"),
        (r"\bmitigation\b", "reduction"),
        (r"\bresonate(?:s|d)?\b", "connect"),
        (r"\bresonating\b", "connecting"),
        (r"\bstakeholders?\b", "people involved"),
        (r"\becosystem\b", "environment"),
        (r"\bcutting-edge\b", "latest"),
        (r"\brevolutionize(?:s|d)?\b", "change"),
        (r"\brevolutionizing\b", "changing"),
        (r"\bspearhead(?:s|ed)?\b", "lead"),
        (r"\bspearheading\b", "leading"),
        (r"\binnovative\b", "new"),
        (r"\binnovation\b", "new idea"),
        (r"\bunprecedented\b", "never-before-seen"),
        (r"\bsophisticated\b", "advanced"),
        (r"\bsignificant(?:ly)?\b", "major"),
        (r"\bfundamental(?:ly)?\b", "basic"),
        (r"\bimplications?\b", "impact"),
        (r"\badvancement(?:s)?\b", "progress"),
        (r"\bincorporate(?:s|ing|d)?\b", "include"),
        (r"\bdemonstrate(?:s|ing|d)?\b", "show"),
        (r"\bhighlight(?:s|ing|ed)?\b", "point out"),
        (r"\brepresent(?:s|ing|ed)?\b", "show"),
    ]
    for pattern, replacement in ai_word_swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 1b. Shorten common long words to reduce average word length ────
    word_length_swaps = [
        (r"\btransforming\b", "changing"),
        (r"\bincreasingly\b", "more and more"),
        (r"\balgorithms?\b", "tools"),
        (r"\btechniques?\b", "methods"),
        (r"\bopportunities\b", "chances"),
        (r"\bchallenges\b", "issues"),
        (r"\btechnology\b", "tech"),
        (r"\btechnological(?:ly)?\b", "tech"),
        (r"\bprocessing\b", "handling"),
        (r"\bapplication(?:s)?\b", "apps"),
        (r"\bimplementation\b", "setup"),
        (r"\bperformance\b", "speed"),
        (r"\bunderstanding\b", "grasp"),
        (r"\bpossibilities\b", "options"),
        (r"\bimportance\b", "value"),
        (r"\bdevelopment\b", "growth"),
        (r"\bmanagement\b", "control"),
        (r"\bcommunication\b", "talk"),
        (r"\bpresentation(?:s)?\b", "talks"),
        (r"\binteraction(?:s)?\b", "use"),
        (r"\binitiative(?:s)?\b", "push"),
        (r"\bimportant\b", "key"),
        (r"\bapproach(?:es)?\b", "way"),
        (r"\bdiscovery\b", "find"),
        (r"\bresponsibility\b", "job"),
        (r"\bresponsibilities\b", "duties"),
        (r"\bprofessional(?:s)?\b", "pro"),
        (r"\bpractitioner(?:s)?\b", "pro"),
        (r"\bmethods?\b", "ways"),
        (r"\badvanced\b", "smart"),
        (r"\bmodern\b", "new"),
        (r"\bexisting\b", "current"),
        (r"\bvarious\b", "many"),
        (r"\bnumerous\b", "many"),
        (r"\badditional\b", "more"),
        (r"\bsimilar(?:ly)?\b", "like"),
        (r"\bcurrent(?:ly)?\b", "now"),
    ]
    for pattern, replacement in word_length_swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 2. Replace formal connectors ──────────────────────────────────
    connector_swaps = [
        (r"\bFurthermore,\s*", "Also, "),
        (r"\bMoreover,\s*", "On top of that, "),
        (r"\bAdditionally,\s*", "And "),
        (r"\bConsequently,\s*", "So "),
        (r"\bNevertheless,\s*", "Still, "),
        (r"\bNonetheless,\s*", "Even so, "),
        (r"\bSubsequently,\s*", "After that, "),
        (r"\bTherefore,\s*", "So "),
        (r"\bHence,\s*", "That's why "),
        (r"\bThus,\s*", "So "),
        (r"\bIn conclusion,\s*", "To wrap up, "),
        (r"\bIn summary,\s*", "In short, "),
        (r"\bIt is important to note that\b", "Worth noting —"),
        (r"\bIt should be noted that\b", "Keep in mind,"),
        (r"\bIt is worth mentioning that\b", "Also,"),
        (r"\bIt is essential to\b", "You need to"),
        (r"\bIn order to\b", "To"),
        (r"\bDue to the fact that\b", "Because"),
        (r"\bAt the present time\b", "Right now"),
        (r"\bIn the event that\b", "If"),
        (r"\bFor the purpose of\b", "To"),
        (r"\bWith regard to\b", "About"),
        (r"\bIn light of\b", "Given"),
        (r"\bOn the other hand,\s*", "Then again, "),
        (r"\bAs a result,\s*", "So "),
        (r"\bIn addition,\s*", "Plus, "),
        (r"\bBy contrast,\s*", "But "),
        (r"\bIn particular,\s*", "Specifically, "),
        (r"\bFor instance,\s*", "For example, "),
        (r"\bIn this regard,\s*", "Here, "),
        (r"\bWith this in mind,\s*", "So "),
        (r"\bThis is why\b", "That's why"),
        (r"\bThis means that\b", "This means"),
        (r"\bIn today's\b", "These days,"),
        (r"\bIn today\b", "These days"),
    ]
    for pattern, replacement in connector_swaps:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 3. Add contractions ────────────────────────────────────────────
    contractions = [
        (r"\bdo not\b", "don't"),
        (r"\bdoes not\b", "doesn't"),
        (r"\bdid not\b", "didn't"),
        (r"\bis not\b", "isn't"),
        (r"\bare not\b", "aren't"),
        (r"\bwas not\b", "wasn't"),
        (r"\bwere not\b", "weren't"),
        (r"\bwill not\b", "won't"),
        (r"\bwould not\b", "wouldn't"),
        (r"\bcould not\b", "couldn't"),
        (r"\bshould not\b", "shouldn't"),
        (r"\bcannot\b", "can't"),
        (r"\bit is\b", "it's"),
        (r"\bthat is\b", "that's"),
        (r"\bthere is\b", "there's"),
        (r"\bthey are\b", "they're"),
        (r"\bwe are\b", "we're"),
        (r"\byou are\b", "you're"),
        (r"\bhe is\b", "he's"),
        (r"\bshe is\b", "she's"),
        (r"\bwho is\b", "who's"),
        (r"\bwhat is\b", "what's"),
        (r"\bI am\b", "I'm"),
        (r"\bI have\b", "I've"),
        (r"\bI will\b", "I'll"),
        (r"\bI would\b", "I'd"),
        (r"\bthey have\b", "they've"),
        (r"\bwe have\b", "we've"),
        (r"\byou have\b", "you've"),
        (r"\bhave not\b", "haven't"),
        (r"\bhas not\b", "hasn't"),
        (r"\bhad not\b", "hadn't"),
    ]
    if level in ("moderate", "heavy"):
        for pattern, replacement in contractions:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 4. Vary sentence starters — break formulaic openers ───────────
    formulaic_opener_swaps = [
        (r"^The (\w)", r"This \1"),
        (r"\. The importance of\b", ". Why does this matter?"),
        (r"\. This demonstrates\b", ". That shows"),
        (r"\. This highlights\b", ". And that points to"),
        (r"\. This shows\b", ". That tells us"),
        (r"\. This means\b", ". Put simply,"),
        (r"\. These (\w)", r". Those \1"),
        (r"\. When it comes to\b", ". For"),
        (r"\. By leveraging\b", ". Using"),
        (r"\. By utilizing\b", ". Using"),
        (r"\. By incorporating\b", ". Using"),
    ]
    for pattern, replacement in formulaic_opener_swaps:
        result = re.sub(pattern, replacement, result, flags=re.MULTILINE)

    # ── 5. Remove/simplify hedging for heavy level ────────────────────
    if level == "heavy":
        hedging_swaps = [
            (r"\bit is generally (\w)", r"generally, \1"),
            (r"\bit is typically (\w)", r"typically, \1"),
            (r"\bit appears that\b", ""),
            (r"\bit seems that\b", ""),
            (r"\bseemingly\b", ""),
            (r"\bpresumably\b", ""),
            (r"\bin many cases\b", "often"),
            (r"\bin most cases\b", "usually"),
            (r"\bto a certain extent\b", "somewhat"),
            (r"\bto some extent\b", "somewhat"),
            (r"\bhas been shown to\b", "can"),
            (r"\bhave been shown to\b", "can"),
        ]
        for pattern, replacement in hedging_swaps:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 6. Vary sentence lengths + inject human touches ─────────────
    if level in ("moderate", "heavy"):
        sentences = re.split(r'(?<=[.!?])\s+', result.strip())
        new_sentences: list[str] = []

        # Alternating 1-word and 2-word-contraction interjections — max burstiness + good contraction rate
        interjections = [
            "Seriously.", "That's key.", "Right?", "It's true.",
            "True.", "That's real.", "Exactly.", "It's clear.",
            "Really.", "That's it.", "Wow.", "It's wild.",
        ]
        inject_idx = 0

        for i, sent in enumerate(sentences):
            words = sent.split()

            # Split sentences over 20 words at a natural conjunction
            if len(words) > 20:
                split_at = -1
                for j, w in enumerate(words[8:18], start=8):
                    if w.lower().rstrip(",") in ("and", "but", "which", "while", "so", "though", "as", "since", "because"):
                        split_at = j
                        break
                if split_at > 0:
                    first = " ".join(words[:split_at]).rstrip(",")
                    second = " ".join(words[split_at:])
                    # Remove leading conjunction from second part for natural flow
                    conj_match = re.match(r"^(and|but|which|while|so|though|as|since|because)\s+", second, re.IGNORECASE)
                    if conj_match:
                        second = second[conj_match.end():]
                    second = second[0].upper() + second[1:] if second else second
                    new_sentences.append(first + ".")
                    new_sentences.append(second)
                    continue

            new_sentences.append(sent)

            # Inject after every sentence in heavy mode — creates maximum burstiness variance
            if level == "heavy" and i < len(sentences) - 1:
                new_sentences.append(interjections[inject_idx % len(interjections)])
                inject_idx += 1

        result = " ".join(new_sentences)

    # ── 6b. Inject first/second person sentence starters for pronoun density ──
    if level == "heavy":
        # Use starters with first-person pronouns (I, we) to boost pronoun rate
        you_starters = [
            "I think",
            "We found that",
            "I can tell you —",
            "We know that",
            "I mean,",
            "We see that",
        ]
        slist = re.split(r'(?<=[.!?])\s+', result.strip())
        modified_p: list[str] = []
        inject_you_count = 0
        max_injections = 3  # inject I/we into up to 3 sentences
        for i, sent in enumerate(slist):
            wds = sent.split()
            if (
                inject_you_count < max_injections
                and len(wds) > 5
                and not re.match(
                    r"^(you|i |we |honest|here|that|what|it|serious|right|true|wow|yep|neat|done|really|exactly|think)",
                    sent, re.IGNORECASE
                )
            ):
                starter = you_starters[inject_you_count % len(you_starters)]
                # Strip any residual leading connectors so 'I think also, ...' becomes 'I think machine...'
                rest = sent[0].lower() + sent[1:] if sent else sent
                for _conn in ("also, ", "and ", "on top of that, ", "plus, ", "so ",
                              "but ", "yet ", "still, ", "moreover, ", "furthermore, ", "additionally, "):
                    if rest.startswith(_conn):
                        rest = rest[len(_conn):]
                        rest = rest[0].upper() + rest[1:] if rest else rest
                        break
                modified_p.append(f"{starter} {rest}")
                inject_you_count += 1
            else:
                modified_p.append(sent)
        result = " ".join(modified_p)

    # ── 7. Inject personal pronouns into impersonal sentences ─────────
    if level in ("moderate", "heavy"):
        # Replace impersonal constructions with personal ones
        personal_swaps = [
            (r"\bOne can\b", "You can"),
            (r"\bOne may\b", "You might"),
            (r"\bOne should\b", "You should"),
            (r"\bIt can be observed that\b", "You'll notice"),
            (r"\bIt can be seen that\b", "You can see"),
            (r"\bIt is clear that\b", "Clearly,"),
            (r"\bIt is evident that\b", "Obviously,"),
            (r"\bIt is widely recognized\b", "Most people agree"),
            (r"\bIt has become increasingly\b", "It's gotten more and more"),
            (r"\bThe fact remains that\b", "But look,"),
            (r"\borganizations\b", "teams"),
            (r"\bOrganizations\b", "Teams"),
        ]
        for pattern, replacement in personal_swaps:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # ── 7. Clean up double spaces and punctuation artifacts ───────────
    result = re.sub(r" {2,}", " ", result)
    result = re.sub(r"\s([,.])", r"\1", result)
    result = re.sub(r"\.\s*\.", ".", result)

    return result.strip()


async def humanize_text_with_fallback(
    text: str,
    level: str = "moderate",
    preserve_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """Try LLM-based humanization, fall back to rule-based if no API key."""
    has_key = bool(settings.openai_api_key or settings.anthropic_api_key)
    if has_key:
        try:
            return await humanize_text(text, level, preserve_keywords)
        except Exception as exc:
            logger.warning("LLM humanization failed, using fallback: %s", exc)

    humanized = _fallback_humanize(text, level)
    original_words = set(re.findall(r"\b\w+\b", text.lower()))
    new_words = set(re.findall(r"\b\w+\b", humanized.lower()))
    changes = len(original_words.symmetric_difference(new_words))

    return {
        "humanized_text": humanized.strip(),
        "changes_made": changes,
        "level": level,
    }
