import re
import unicodedata

from .constant import (
    COMBINE_ACUTE,
    COMBINE_DOT,
    COMBINE_GRAVE,
    ENDING_VOWEL_MAPPING,
    LETTER_MAPPING,
    NULL_MAPPING,
)
from .parser import parse


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


def syllable_to_vie(
    syllable: dict,
    options: dict | None = None,
    is_last_syllable: bool = False,
) -> str:
    options = options or {}

    head = syllable["parts"][0] or ""
    tail = syllable["parts"][1] or ""

    is_null_vowel = tail not in ENDING_VOWEL_MAPPING

    vie_syllable = (
        LETTER_MAPPING.get(head, "")
        + ENDING_VOWEL_MAPPING.get(tail, NULL_MAPPING)
    )

    # Equivalent to JS:
    #
    # .replace(/wi|wa|wâ|we|wơ|ge|gi(?!a)|gê|qui/g, callback)
    #
    replacements = {
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

    pattern = re.compile(r"wi|wa|wâ|we|wơ|ge|gi(?!a)|gê|qui")

    vie_syllable = pattern.sub(
        lambda match: replacements[match.group(0)],
        vie_syllable,
    )

    if is_null_vowel:
        vowel_epenthesis = options.get("vowelEpenthesis", {})

        if (
            vowel_epenthesis.get("skipAll")
            or (
                vowel_epenthesis.get("skipLast")
                and is_last_syllable
            )
        ):
            return ""

        # JS: /._/g
        #
        # Replace every two-character sequence where second char = "_".
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

        vie_syllable = re.sub(
            r"._",
            replace_epenthesis,
            vie_syllable,
        )

    else:
        # JS:
        # /ki$|li$|mi$|si$|ti$|hi$/g
        ending_replacements = {
            "ki": "ky",
            "li": "ly",
            "mi": "my",
            "si": "sy",
            "ti": "ty",
            "hi": "hy",
        }

        vie_syllable = re.sub(
            r"ki$|li$|mi$|si$|ti$|hi$",
            lambda match: ending_replacements[match.group(0)],
            vie_syllable,
        )

        # JS:
        # /^k.|^c./g
        #
        # This matches first two characters.
        vie_syllable = re.sub(
            r"^[kc].",
            lambda match: vie_consonant_rule(
                match.group(0)[0],
                match.group(0)[1],
            ),
            vie_syllable,
        )

    syl_with_tonal = add_tonal_mark(
        vie_syllable,
        syllable.get("stress"),
    )

    if options.get("uppercaseStress") and syllable.get("stress"):
        return syl_with_tonal.upper()

    return syl_with_tonal


def ipa_to_vie(
    ipa: str,
    options: dict | None = None,
) -> list[dict]:
    options = options or {}
    results = []

    for item in ipa.split(", "):
        cleaned = (
            item
            .replace("ɝˈ", "əˈɹ")
            .replace("ɝ", "əɹ")
        )

        try:
            ast = parse(cleaned)

            # JS:
            #
            # ast.reduce((s, p) => s + (p.stress ? 1 : 0), 0)
            #
            # ==
            #
            # ast.reduce((s, p) => s + (p.parts[1] ? 1 : 0), 0)
            stress_count = sum(
                1 for syllable in ast
                if syllable.get("stress")
            )

            vowel_count = sum(
                1 for syllable in ast
                if syllable["parts"][1]
            )

            if stress_count == vowel_count:
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

            last_syllable_idx = len(ast) - 1
            vie_parts = []

            for idx, syllable in enumerate(ast):
                # JS:
                #
                # if (
                #   syllable.stress &&
                #   !syllable.parts[1] &&
                #   !!ast[idx + 1]
                # )
                #
                if (
                    syllable.get("stress")
                    and not syllable["parts"][1]
                    and idx + 1 < len(ast)
                ):
                    ast[idx + 1]["stress"] = syllable["stress"]
                    syllable["stress"] = None

                vie_syl = syllable_to_vie(
                    syllable=syllable,
                    options=options,
                    is_last_syllable=(
                        idx == last_syllable_idx
                    ),
                )

                if idx != 0 and vie_syl:
                    vie_parts.append("-")

                vie_parts.append(vie_syl)

            results.append({
                "ipa": item,
                "ast": ast,
                "vie": "".join(vie_parts),
            })

        except Exception as e:
            print(
                e,
                "-------------",
                [ipa, item, cleaned],
            )

    return results
