import argparse
import re
import sys
from pathlib import Path
from typing import Literal

from phonemizer import phonemize

# from .converter import ipa_to_vie
from typing import cast

if __package__:
    from .converter import ipa_to_vie
else:
    # Allow ``python main.py`` when this file is run from the package folder.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from vietify.converter import ipa_to_vie


PHONEMIZER_LANGUAGES = {
    "en": "en-us",
    "fr": "fr-fr",
    "de": "de",
}


def normalize_phonemized_ipa(ipa: str) -> str:
    return (
        ipa.replace("ː", "")
        .replace("̃", "")
        .replace("ɚ", "əɹ")
        # .replace("ɝ", "əɹ")
        .replace("ɜ", "ə")
        .replace("ɐ", "ə")
        .replace("ᵻ", "ɪ")
        .replace("ɾ", "r")
        # .replace("ʁ", "r")
        # .replace("ɲ", "n")
        .replace("ɥ", "w")
        # .replace("r", "ɹ")
        # .replace("l", "ɫ")
        .replace("ʌ", "ɑ")
    )


def text_to_vietify(
    text: str,
    language: str,
    mode: Literal["weak", "strong"] = "strong",
) -> str:
    if language == "ipa":
        ipa = text
    else:
        ipa = cast(
            str,
            phonemize(
                text,
                language=PHONEMIZER_LANGUAGES[language],
                backend="espeak",
                strip=True,
                preserve_punctuation=True,
            ),
        )
    ipa = normalize_phonemized_ipa(ipa)
    converted_words = []

    for word in ipa.split():
        match = re.match(r"^([^\w]*)(.*?)([^\w]*)$", word, re.UNICODE)
        if not match or not match.group(2):
            converted_words.append(word)
            continue

        leading, pronunciation, trailing = match.groups()
        results = ipa_to_vie(pronunciation, mode=mode)
        if not results:
            raise ValueError(f"could not parse IPA text: {pronunciation!r}")

        converted_words.append(
            leading
            + "-".join(result["vie"] for result in results)
            + trailing
        )

    return " ".join(converted_words)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert text or IPA pronunciation to Vietnamese spelling."
        ),
    )
    parser.add_argument(
        "text",
        nargs="+",
        help="Text to convert, or IPA text when --language=ipa.",
    )
    parser.add_argument(
        "-l",
        "--language",
        choices=("en", "fr", "de", "ipa"),
        default="en",
        help=(
            "Input language: en (English), fr (French), de (German), "
            "or ipa (already-transcribed IPA). Default: en."
        ),
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=("weak", "strong"),
        default="weak",
        help="Conversion rule mode: weak or strong. Default: strong.",
    )
    args = parser.parse_args()

    try:
        print(
            text_to_vietify(
                " ".join(args.text),
                args.language,
                args.mode,
            )
        )
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
