import logging
import re
import unicodedata
from typing import Literal, Protocol

from . import vietifyRuleStrong, vietifyRuleWeak
from .vietifyRuleStrong import (
    COMBINE_ACUTE,
    COMBINE_DOT,
    COMBINE_GRAVE,
)
from .parser import parse

logger = logging.getLogger(__name__)

RuleMode = Literal["weak", "strong"]


class ConversionRules(Protocol):
    """Rule table required by syllable-to-Vie conversion."""

    SYLLABLE_ENDING_MAPPING: dict[str, str]
    LETTER_MAPPING: dict[str, str]
    NULL_MAPPING: Literal["_"]


_RULES: dict[RuleMode, ConversionRules] = {
    "weak": vietifyRuleWeak,
    "strong": vietifyRuleStrong,
}


def _rules_for_mode(mode: RuleMode) -> ConversionRules:
    """Return rule table for mode, raising ValueError for unsupported modes."""
    try:
        return _RULES[mode]
    except KeyError:
        raise ValueError(
            f"mode must be 'weak' or 'strong', got {mode!r}"
        ) from None


def normalize_nfc(value: str) -> str:
    """Normalize Unicode to NFC so composed Vietnamese characters compare consistently."""
    return unicodedata.normalize("NFC", value)


def normalize_nfd(value: str) -> str:
    """Normalize Unicode to NFD for inspecting a base character."""
    return unicodedata.normalize("NFD", value)


def add_tonal_mark_to_vowel(vie: str, tonal_mark: str) -> str:
    """Attach tonal mark to preferred Vietnamese vowel, falling back by priority."""
    # Prefer ê, â, ă, ô, ơ, ư
    match = re.search(r"[êâăôơư]", vie, re.IGNORECASE)

    if match:
        start, end = match.span()
        vowel = vie[start:end]
        return (
            vie[:start]
            + normalize_nfc(vowel + tonal_mark)
            + vie[end:]
        )

    # Then e, a, o, u, i
    match = re.search(r"[eao ui]".replace(" ", ""), vie, re.IGNORECASE)

    if match:
        start, end = match.span()
        vowel = vie[start:end]
        return (
            vie[:start]
            + normalize_nfc(vowel + tonal_mark)
            + vie[end:]
        )

    # Finally y
    match = re.search(r"y", vie, re.IGNORECASE)

    if match:
        start, end = match.span()
        vowel = vie[start:end]
        return (
            vie[:start]
            + normalize_nfc(vowel + tonal_mark)
            + vie[end:]
        )

    return vie


def add_tonal_mark(vie: str, is_stress: int | None = None) -> str:
    """Apply Vietnamese tone mark based on syllable ending and stress."""
    if re.search(r"(ch|t|p|c)$", vie):
        return add_tonal_mark_to_vowel(
            vie,
            COMBINE_ACUTE if is_stress else COMBINE_DOT,
        )

    if not is_stress:
        return add_tonal_mark_to_vowel(vie, COMBINE_GRAVE)

    return vie



def vie_consonant_rule(consonant: str, vowel: str) -> str:
    """Resolve c/k alternation required by following vowel."""

    # k/c + u + vowel -> qu + vowel
    if (
        vowel
        and consonant in {"k", "c"}
        and normalize_nfd(vowel[0])[0] == "u"
        and len(vowel) > 1
        and normalize_nfd(vowel[1])[0] in {
            "a", "e", "ê", "i", "o", "u", "œ", "ø", "ä", "ö", "ü", 
        }
    ):
        return "qu" + vowel[1:]

    if (
        vowel
        and consonant == "k"
        and normalize_nfd(vowel[0])[0] in {"a", "o", "u", "ä", "ü",}
    ):
        return "c" + vowel

    if (
        vowel
        and consonant == "c"
        and normalize_nfd(vowel[0])[0] in {"e", "ê", "i", "œ", "ø"}
    ):
        return "k" + vowel

    return consonant + vowel

_VIE_SYLLABLE_REPLACEMENTS = {
    "wi": "uy",
    "wa": "oa",
    "wâ": "uâ",
    "we": "oe",
    "wơ": "uơ",
    "ge": "ghe",
    "gi": "ghi",
    "gê": "ghê",
    "qui": "quy",
}

_VIE_SYLLABLE_PATTERN = re.compile(
    r"wi|wa|wâ|we|wơ|ge|gi(?!a)|gê|qui"
    # r"wi|wa|wâ|we|wơ|ge|gê|qui"
)

_ENDING_REPLACEMENTS = {
    "ki": "ky",
    "li": "ly",
    "mi": "my",
    "si": "sy",
    "ti": "ty",
    "hi": "hy",
}

_ENDING_PATTERN = re.compile(
    r"ki$|li$|mi$|si$|ti$|hi$"
)


def _replace_vie_syllable_patterns(vie: str) -> str:
    """Apply spelling substitutions that operate on complete Vie syllables."""
    return _VIE_SYLLABLE_PATTERN.sub(
        lambda match: _VIE_SYLLABLE_REPLACEMENTS[match.group(0)],
        vie,
    )


def _apply_vowel_epenthesis(
    vie: str,
    options: dict,
) -> str:
    """Insert configured vowel into syllables whose vowel is missing."""
    vowel_epenthesis = options.get("vowelEpenthesis", {})

    def replace_epenthesis(match: re.Match) -> str:
        consonant = match.group(0)[0]
        replacement = vowel_epenthesis.get(
            "replacement",
            "ơ",
        )
        return vie_consonant_rule(
            consonant,
            replacement,
        )

    return re.sub(
        r"._",
        replace_epenthesis,
        vie,
    )


def _apply_ending_replacements(vie: str) -> str:
    """Apply final -i -> -y spelling substitutions."""
    return _ENDING_PATTERN.sub(
        lambda match: _ENDING_REPLACEMENTS[match.group(0)],
        vie,
    )

def _apply_initial_consonant_rule(vie: str) -> str:
    """Apply c/k spelling rule to initial consonant."""

    if len(vie) < 2 or vie[0] not in {"k", "c"}:
        return vie

    return vie_consonant_rule(vie[0], vie[1:])

def _apply_final_k_rule(vie: str) -> str:
    """Apply Vietnamese c/ch spelling rule to final /k/."""

    if not vie.endswith("c"):
        return vie

    if len(vie) < 2:
        return vie

    preceding = normalize_nfd(vie[-2])[0]

    if preceding in {"e", "ê", "i"}:
        return vie[:-1] + "ch"

    return vie

def _should_skip_vowel_epenthesis(
    options: dict,
    is_last_syllable: bool,
) -> bool:
    """Return whether vowel epenthesis should be skipped for current syllable."""
    vowel_epenthesis = options.get("vowelEpenthesis", {})

    return (
        vowel_epenthesis.get("skipAll")
        or (
            vowel_epenthesis.get("skipLast")
            and is_last_syllable
        )
    )


def _build_vie_syllable(
    syllable: dict,
    rules: ConversionRules,
) -> tuple[str, bool]:
    """Map parser AST syllable components into an intermediate Vie syllable.

    Returns:
        (syllable, is_null_vowel)
    """
    head = syllable.get("initial") or ""
    nucleus = syllable.get("nucleus") or ""
    ending = syllable.get("ending") or ""

    tail = nucleus + ending

    is_null_vowel = tail not in rules.SYLLABLE_ENDING_MAPPING

    vie = (
        rules.LETTER_MAPPING.get(head, "")
        + rules.SYLLABLE_ENDING_MAPPING.get(
            tail,
            rules.NULL_MAPPING,
        )
    )

    return _replace_vie_syllable_patterns(vie), is_null_vowel


def syllable_to_vie(
    syllable: dict,
    options: dict | None = None,
    is_last_syllable: bool = False,
    *,
    mode: RuleMode,
) -> str:
    """Convert one parser AST syllable into Vie spelling.

    Strong mode preserves additional information such as stress and can
    insert epenthetic vowels. Weak mode removes null-vowel placeholders.
    """
    options = options or {}
    rules = _rules_for_mode(mode)

    vie_syllable, is_null_vowel = _build_vie_syllable(
        syllable,
        rules,
    )

    if is_null_vowel:
        if mode == "strong":
            if _should_skip_vowel_epenthesis(
                options,
                is_last_syllable,
            ):
                return ""

            vie_syllable = _apply_vowel_epenthesis(
                vie_syllable,
                options,
            )
        else:
            vie_syllable = vie_syllable.replace(
                rules.NULL_MAPPING,
                "",
            )
    else:
        vie_syllable = _apply_ending_replacements(
            vie_syllable,
        )
        vie_syllable = _apply_initial_consonant_rule(
            vie_syllable,
        )

        vie_syllable = _apply_final_k_rule(
            vie_syllable,
        )

    if mode == "strong":
        vie_syllable = add_tonal_mark(
            vie_syllable,
            syllable.get("stress"),
        )

        if options.get("uppercaseStress") and syllable.get("stress"):
            return vie_syllable.upper()

    return vie_syllable


def _clean_ipa_item(item: str) -> str:
    """Normalize IPA variants that parser does not consume directly."""
    return (
        item
        .replace("ɝˈ", "əˈɹ")
        .replace("ɝ", "əɹ")
    )


def _normalize_stress(ast: list[dict]) -> None:
    """Remove secondary stress when every vowel already has stress."""
    stress_count = sum(
        1 for syllable in ast
        if syllable.get("stress")
    )

    vowel_count = sum(
        1 for syllable in ast
        if syllable.get("nucleus")
    )

    if stress_count != vowel_count:
        return

    secondary = next(
        (
            syllable
            for syllable in ast
            if syllable.get("stress") == 2
        ),
        None,
    )

    if secondary:
        secondary["stress"] = None


def _move_stress_from_empty_syllables(
    ast: list[dict],
) -> None:
    """Move stress from syllable without nucleus onto following syllable."""
    for idx, syllable in enumerate(ast):
        if (
            syllable.get("stress")
            and not syllable.get("nucleus")
            and idx + 1 < len(ast)
        ):
            ast[idx + 1]["stress"] = syllable["stress"]
            syllable["stress"] = None


def _convert_ast_to_vie(
    ast: list[dict],
    options: dict,
    mode: RuleMode,
) -> str:
    """Convert parsed IPA AST into hyphen-separated Vie syllables."""
    last_syllable_idx = len(ast) - 1
    vie_parts = []

    for idx, syllable in enumerate(ast):
        vie_syl = syllable_to_vie(
            syllable=syllable,
            options=options,
            is_last_syllable=(
                idx == last_syllable_idx
            ),
            mode=mode,
        )

        if idx != 0 and vie_syl:
            vie_parts.append("-")

        vie_parts.append(vie_syl)

    return "".join(vie_parts)


def _convert_ipa_item(
    item: str,
    options: dict,
    mode: RuleMode,
) -> dict:
    """Parse and convert one IPA item.

    Kept separate from `ipa_to_vie` so failures can be traced to one
    IPA item without losing surrounding input context.
    """
    cleaned = _clean_ipa_item(item)

    logger.debug(
        "IPA conversion start: item=%r cleaned=%r mode=%s options=%r",
        item,
        cleaned,
        mode,
        options,
    )

    ast = parse(cleaned)

    logger.debug(
        "IPA parsed: item=%r ast=%r",
        item,
        ast,
    )

    _normalize_stress(ast)
    _move_stress_from_empty_syllables(ast)

    vie = _convert_ast_to_vie(
        ast,
        options,
        mode,
    )

    logger.debug(
        "IPA conversion complete: item=%r vie=%r ast=%r",
        item,
        vie,
        ast,
    )

    return {
        "ipa": item,
        "ast": ast,
        "vie": vie,
    }

_LIAISON_CONSONANTS = {
    "z", "x",  # z liaison
    "t", "d",       # t liaison
    "n",            # n liaison
    "ph",            # v liaison
    # "p", "r", 
}
_VOWELS = set("aeêiouœøäöü")

def _apply_french_liaison(results: list[dict]) -> list[dict]:
    """Mark liaison between adjacent converted words."""

    for current, following in zip(results, results[1:]):
        current_vie = current["vie"]
        following_vie = following["vie"]

        if (
            current_vie
            and following_vie
            # and current_vie[-1].lower() in _LIAISON_CONSONANTS
            and any(current_vie.lower().endswith(c) for c in _LIAISON_CONSONANTS)
            and following_vie[0].lower() in _VOWELS
        ):
            current["vie"] = current_vie + " →"

    return results

def ipa_to_vie(
    ipa: str,
    options: dict | None = None,
    *,
    mode: RuleMode,
) -> list[dict]:
    """Convert comma-separated IPA items into Vie representations.

    Each result contains original IPA, parsed AST, and converted Vie text.
    Exceptions retain their original traceback while logging enough context
    to identify failing input and conversion mode.
    """
    options = options or {}
    _rules_for_mode(mode)

    results = []

    logger.debug(
        "IPA batch conversion start: ipa=%r mode=%s options=%r",
        ipa,
        mode,
        options,
    )

    for index, item in enumerate(ipa.split(", ")):
        try:
            results.append(
                _convert_ipa_item(
                    item,
                    options,
                    mode,
                )
            )
        except Exception:
            logger.exception(
                "IPA conversion failed: "
                "index=%d item=%r cleaned=%r mode=%s options=%r",
                index,
                item,
                _clean_ipa_item(item),
                mode,
                options,
            )
            raise

    if options.get("language") == "fr":
        results = _apply_french_liaison(results)


    logger.debug(
        "IPA batch conversion complete: count=%d mode=%s",
        len(results),
        mode,
    )

    return results