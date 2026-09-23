import argparse
import sys
from pathlib import Path

if __package__:
    from .converter import ipa_to_vie
else:
    # Allow ``python main.py`` when this file is run from the package folder.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from vietify.converter import ipa_to_vie


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert English IPA pronunciation to Vietnamese spelling.",
    )
    parser.add_argument(
        "ipa",
        nargs="+",
        help="IPA text to convert. Keep stress marks such as ˈ when available.",
    )
    args = parser.parse_args()

    input_text = " ".join(args.ipa)
    results = ipa_to_vie(input_text)

    if not results:
        parser.error("could not parse the supplied IPA text")

    for result in results:
        print(result["vie"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
