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

RuleMode = Literal["weak", "strong"]


class ConversionRules(Protocol):
    ENDING_VOWEL_MAPPING: dict[str, str]
    LETTER_MAPPING: dict[str, str]
    NULL_MAPPING: Literal["_"]


_RULES: dict[RuleMode, ConversionRules] = {
    "weak": vietifyRuleWeak,
    "strong": vietifyRuleStrong,
}


def _rules_for_mode(mode: RuleMode) -> ConversionRules:
    try:
        return _RULES[mode]
    except KeyError:
        raise ValueError(
            f"mode must be 'weak' or 'strong', got {mode!r}"
        ) from None


def normalize_nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def normalize_nfd(value: str) -> str:
    return unicodedata.normalize("NFD", value)


def add_tonal_mark_to_vowel(vie: str, tonal_mark: str) -> str:
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
    if re.search(r"(ch|t|p|c)$", vie):
        return add_tonal_mark_to_vowel(
            vie,
            COMBINE_ACUTE if is_stress else COMBINE_DOT,
        )

    if not is_stress:
        return add_tonal_mark_to_vowel(vie, COMBINE_GRAVE)

    return vie


def vie_consonant_rule(consonant: str, vowel: str) -> str:
    if (
        vowel
        and consonant == "k"
        and normalize_nfd(vowel[0])[0] in {"a", "o", "u"}
    ):
        return "c" + vowel

    if (
        vowel
        and consonant == "c"
        and normalize_nfd(vowel[0])[0] in {"e", "i"}
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
    return _VIE_SYLLABLE_PATTERN.sub(
        lambda match: _VIE_SYLLABLE_REPLACEMENTS[match.group(0)],
        vie,
    )


def _apply_vowel_epenthesis(
    vie: str,
    options: dict,
) -> str:
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
    return _ENDING_PATTERN.sub(
        lambda match: _ENDING_REPLACEMENTS[match.group(0)],
        vie,
    )


def _apply_initial_consonant_rule(vie: str) -> str:
    return re.sub(
        r"^[kc].",
        lambda match: vie_consonant_rule(
            match.group(0)[0],
            match.group(0)[1],
        ),
        vie,
    )


def _should_skip_vowel_epenthesis(
    options: dict,
    is_last_syllable: bool,
) -> bool:
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
    head = syllable["parts"][0] or ""
    tail = syllable["parts"][1] or ""
    is_null_vowel = tail not in rules.ENDING_VOWEL_MAPPING

    vie = (
        rules.LETTER_MAPPING.get(head, "")
        + rules.ENDING_VOWEL_MAPPING.get(
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

    if mode == "strong":
        vie_syllable = add_tonal_mark(
            vie_syllable,
            syllable.get("stress"),
        )

        if options.get("uppercaseStress") and syllable.get("stress"):
            return vie_syllable.upper()

    return vie_syllable


def _clean_ipa_item(item: str) -> str:
    return (
        item
        .replace("ɝˈ", "əˈɹ")
        .replace("ɝ", "əɹ")
    )


def _normalize_stress(ast: list[dict]) -> None:
    stress_count = sum(
        1 for syllable in ast
        if syllable.get("stress")
    )

    vowel_count = sum(
        1 for syllable in ast
        if syllable["parts"][1]
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


def _move_stress_from_empty_syllables(ast: list[dict]) -> None:
    for idx, syllable in enumerate(ast):
        if (
            syllable.get("stress")
            and not syllable["parts"][1]
            and idx + 1 < len(ast)
        ):
            ast[idx + 1]["stress"] = syllable["stress"]
            syllable["stress"] = None


def _convert_ast_to_vie(
    ast: list[dict],
    options: dict,
    mode: RuleMode,
) -> str:
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
    cleaned = _clean_ipa_item(item)
    ast = parse(cleaned)

    _normalize_stress(ast)
    _move_stress_from_empty_syllables(ast)

    return {
        "ipa": item,
        "ast": ast,
        "vie": _convert_ast_to_vie(
            ast,
            options,
            mode,
        ),
    }


def ipa_to_vie(
    ipa: str,
    options: dict | None = None,
    *,
    mode: RuleMode,
) -> list[dict]:
    options = options or {}
    _rules_for_mode(mode)

    results = []

    for item in ipa.split(", "):
        try:
            results.append(
                _convert_ipa_item(
                    item,
                    options,
                    mode,
                )
            )
        except Exception as e:
            print(
                e,
                "-------------",
                [ipa, item, _clean_ipa_item(item)],
            )

    return results