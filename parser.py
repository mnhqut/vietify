from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


grammar = Grammar(r"""
Word = ws "/"? Syllable* "/"? ws
ws = " "*

Syllable =
      Stress? Consonant Stress? SyllableEnding
    / Stress? Consonant
    / Stress? SyllableEnding

# SyllableEnding =
#     ((((DiphthongEnding / Diphthong) !(Diphthong / Vowel))
#     / (Vowel EndingConsonant) !(Diphthong / Vowel))
#     / Vowel)

SyllableEnding =
    ((((DiphthongEnding / FrenchNasalDiphthong / Diphthong)
        !(Diphthong / Vowel))
    / (Vowel EndingConsonant) !(Diphthong / Vowel))
    / Vowel)

Consonant =
      "b"
    / "tʃ"
    / "tɹ"
    / "t"
    /     "k" Stress? "w"
    / "k"
    / "z"
    / "ɹ"
    / "s"
    / "m"
    / "f"
    / "ɡ"
    / "n"
    / "ɫ"
    / "l"
    / "w"
    / "p"
    / "θ"
    / "v"
    / "h"
    / "ŋ"
    / "ʃ"
    / "ʒ"
    / "dʒ"
    / "d"
    / "ð"

    # french 
    / "ɲ"
    / "ʁ"

EndingConsonant =
      "b"
    / "t" !"ʃ"
    / "k" !(Stress? "w")
    / "m"
    / "ɡ"
    / "n"
    / "p"
    / "h"
    / "ŋ"

    # french 
    # / "ɲ"   # complicated to treat this as ending consonant
    / "ʁ"

DiphthongEnding =
      "eɪt"
    / "jəŋ"
    / "eɪn"

Diphthong =
      "oʊ"
    / "eɪ"
    / "aɪ"
    / "aʊ"
    / "ju"
    / "jə"
    / "jæ"
    / "jɑ"
    / "jʊ"
    / "jɛ"
    / "jɪ"
    / "jɔ"
    / "ji"
    / "joʊ"
    / "jaʊ"
    / "jeɪ"
    / "əj"
    / "ɔɪ"

    / "wa"

    #fr
    # / "jɑ̃"
    # / "jɛ̃"
    # / "jɔ̃"
    # / "jœ̃"
FrenchNasalDiphthong =
      "jɑ̃"
    / "jɛ̃"
    / "jɔ̃"
    / "jœ̃"

Vowel =
    #fr
      "ɑ̃"
    / "ɛ̃"
    / "ɔ̃"
    / "œ̃"
    / "ø"
    / "œ"
    / "y"
    ##
    / "a"
    / "ʊ"
    / "ə"
    / "ɔ"
    / "u"
    / "ɪ"
    / "o"
    / "ɛ"
    / "e"
    / "i"
    / "ɑ"
    / "ɝ"
    / "æ"
    / "j"

Stress =
      "ˈ"
    / "ˌ"
""")


def stress_value(stress):
    if stress == "ˈ":
        return 1
    if stress == "ˌ":
        return 2
    return None


def remove_stress(text):
    return text.replace("ˈ", "").replace("ˌ", "")


class Visitor(NodeVisitor):

    def visit_Word(self, node, children):
        _, _, syllables, _, _ = children
        return syllables if isinstance(syllables, list) else [syllables]

    def visit_Syllable(self, node, children):
        # Optional expressions that do not match are omitted from
        # ``children`` by parsimonious, so inspect the named grammar nodes
        # instead of relying on positional indexes.
        sequence = node.children[0].children
        stress = next(
            (c for c in node.text if c in "ˈˌ"),
            None,
        )
        consonant = next(
            (
                child.text
                for child in sequence
                if child.expr_name == "Consonant"
            ),
            None,
        )
        ending = next(
            (
                child.text
                for child in sequence
                if child.expr_name == "SyllableEnding"
            ),
            None,
        )

        if consonant is not None and stress is None:
            stress = next(
                (c for c in consonant if c in "ˈˌ"),
                None,
            )

        return {
            "stress": stress_value(stress),
            "parts": [
                remove_stress(consonant) if consonant else None,
                remove_stress(ending) if ending else None,
            ],
        }

    # def visit_SyllableEnding(self, node, children):
    #     return node.text
    def visit_VowelWithEnding(self, node, children):
        vowel, ending = children
        return {
            "vowel": vowel,
            "ending": ending,
        }
    def visit_SyllableEnding(self, node, children):
        return children[0]
    
    def visit_Consonant(self, node, children):
        text = node.text

        # "k" stress? "w" -> "kw", "kˈw", or "kˌw"
        if text.startswith("k") and text.endswith("w"):
            stress = next(
                (c for c in text if c in "ˈˌ"),
                "",
            )
            return stress + "kw"

        return text

    def visit_EndingConsonant(self, node, children):
        return node.text

    def visit_DiphthongEnding(self, node, children):
        return node.text

    def visit_Diphthong(self, node, children):
        return node.text

    def visit_Vowel(self, node, children):
        return node.text

    def visit_Stress(self, node, children):
        return node.text

    def visit_ws(self, node, children):
        return node.text

    def generic_visit(self, node, children):
        if children:
            return children[0] if len(children) == 1 else children
        return node.text


def parse(text):
    tree = grammar.parse(text)
    return Visitor().visit(tree)
