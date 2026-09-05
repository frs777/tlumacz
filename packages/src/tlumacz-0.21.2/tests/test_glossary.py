"""Tests for the glossary parser and prompt generation."""

from tlumacz.glossary import Glossary, MAX_PROMPT_ENTRIES


def test_plain_csv_with_header(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("source,target\nHello,Witaj\nWorld,Świat\n", encoding="utf-8")
    glossary = Glossary.from_csv(path)
    assert len(glossary) == 2
    assert glossary.entries == [("Hello", "Witaj"), ("World", "Świat")]


def test_pattern_substitution_header_and_hash_targets(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("Pattern,Substitution\nAarona,#Aaron\nBabcia,#Babcia\n", encoding="utf-8")
    glossary = Glossary.from_csv(path)
    assert len(glossary) == 2
    assert glossary.entries[0] == ("Aarona", "Aaron")


def test_malformed_rows_skipped(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("source,target\n\nOnlyOne\nA,B\n,EmptyTarget\n", encoding="utf-8")
    glossary = Glossary.from_csv(path)
    assert glossary.entries == [("A", "B")]


def test_deduplication_case_insensitive(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("source,target\nFoo,One\nfoo,Two\n", encoding="utf-8")
    glossary = Glossary.from_csv(path)
    assert len(glossary) == 1
    assert glossary.entries[0] == ("Foo", "One")


def test_max_entries_stops_early(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text(
        "".join(f"k{i},v{i}\n" for i in range(1000)), encoding="utf-8"
    )
    glossary = Glossary.from_csv(path, max_entries=10)
    assert len(glossary) == 10


def test_to_prompt_skips_identity_pairs():
    glossary = Glossary(entries=[("Term", "Term"), ("Cat", "Kot")])
    prompt = glossary.to_prompt()
    assert "Cat => Kot" in prompt
    assert "Term" not in prompt


def test_to_prompt_empty_when_only_identity():
    glossary = Glossary(entries=[("A", "a")])
    assert glossary.to_prompt() == ""


def test_to_prompt_respects_max_entries():
    glossary = Glossary(entries=[(f"k{i}", f"v{i}") for i in range(400)])
    prompt = glossary.to_prompt(max_entries=MAX_PROMPT_ENTRIES)
    assert prompt.count("=>") == MAX_PROMPT_ENTRIES


def test_add_and_save_roundtrip(tmp_path):
    glossary = Glossary()
    assert glossary.add("Hello", "Witaj") is True
    assert glossary.add("hello", "Inne") is False
    assert glossary.add("", "X") is False
    path = tmp_path / "out.csv"
    glossary.save(path)
    reloaded = Glossary.from_csv(path)
    assert reloaded.entries == glossary.entries
