from .vietifyRuleStrong import ENDING_VOWEL_MAPPING


def main():
    result = [
        s
        for s in ENDING_VOWEL_MAPPING
        if len(s) >= 3
        and s[-1] in "btkmɡɛnephŋ"
    ]

    print(result)


if __name__ == "__main__":
    main()