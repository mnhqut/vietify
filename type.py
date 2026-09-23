from typing import TypedDict


class Syllable(TypedDict):
    stress: int | None
    parts: list[str | None]


class VieVowelEpenthesisOptions(TypedDict, total=False):
    skipAll: bool
    skipLast: bool
    replacement: str


class IpaToVieOptions(TypedDict, total=False):
    uppercaseStress: bool
    vowelEpenthesis: VieVowelEpenthesisOptions


class SyllableToVieProps(TypedDict, total=False):
    syllable: Syllable
    options: IpaToVieOptions
    isLastSyllable: bool