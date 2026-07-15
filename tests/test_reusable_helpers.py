from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from reading_spelling_coach import (
    clean_definition,
    clean_internet_word,
    prepare_internet_search_topic,
    word_matches_difficulty,
    word_matches_search_topic,
)


def test_prepare_internet_search_topic_maps_current_known_topics():
    examples = {
        "network": "computer networking",
        "networks": "computer networking",
        "networking": "computer networking",
        "computer network": "computer networking",
        "computer networks": "computer networking",
        "security": "cybersecurity",
        "cyber": "cybersecurity",
        "cyber security": "cybersecurity",
        "computer": "computer science",
    }

    for topic, expected_search_term in examples.items():
        assert prepare_internet_search_topic(topic) == expected_search_term


def test_prepare_internet_search_topic_strips_spaces_and_is_case_insensitive_for_mapped_topics():
    assert prepare_internet_search_topic("  Network  ") == "computer networking"
    assert prepare_internet_search_topic("CYBER SECURITY") == "cybersecurity"


def test_prepare_internet_search_topic_returns_stripped_original_for_unmapped_topics():
    assert prepare_internet_search_topic("  Reading skills  ") == "Reading skills"
    assert prepare_internet_search_topic("") == ""
    assert prepare_internet_search_topic("   ") == ""


def test_clean_internet_word_accepts_current_valid_formats():
    assert clean_internet_word("Router") == "router"
    assert clean_internet_word("  Wi-Fi  ") == "wi-fi"
    assert clean_internet_word("ab") == "ab"
    assert clean_internet_word("a" * 25) == "a" * 25


def test_clean_internet_word_rejects_empty_short_long_and_invalid_characters():
    invalid_words = [
        "",
        "   ",
        "a",
        "a" * 26,
        "two words",
        "word!",
        "word2",
        "can't",
        "email@example",
    ]

    for word in invalid_words:
        assert clean_internet_word(word) == ""


def test_clean_definition_strips_tabs_newlines_and_short_parenthetical_labels():
    assert clean_definition("  word\tA device that forwards network traffic.  ") == "A device that forwards network traffic."
    assert clean_definition("Line one\nLine two") == "Line one Line two"
    assert clean_definition("(noun) (computing) A machine that stores data.") == "A machine that stores data."


def test_clean_definition_empty_text_returns_current_fallback_message():
    assert clean_definition("") == "No meaning found yet."
    assert clean_definition("   ") == "No meaning found yet."
    assert clean_definition("word\t   ") == "word"


def test_clean_definition_keeps_very_long_parenthetical_prefix_current_behavior():
    long_label = "(" + "x" * 31 + ") Definition stays after long label."
    assert clean_definition(long_label) == long_label


def test_word_matches_difficulty_accepts_current_boundary_lengths():
    assert word_matches_difficulty("ab", "Short meaning.", "beginner") is True
    assert word_matches_difficulty("a" * 8, "m" * 120, "beginner") is True
    assert word_matches_difficulty("abcd", "m" * 160, "medium") is True
    assert word_matches_difficulty("a" * 12, "Medium meaning.", "medium") is True
    assert word_matches_difficulty("a" * 6, "Hard word meaning that may be longer.", "hard") is True
    assert word_matches_difficulty("a" * 25, "Hard word meaning.", "hard") is True
    assert word_matches_difficulty("ab", "Mixed meaning.", "mixed") is True
    assert word_matches_difficulty("a" * 25, "Mixed meaning.", "mixed") is True


def test_word_matches_difficulty_rejects_empty_unknown_and_out_of_range_values():
    assert word_matches_difficulty("", "Meaning.", "beginner") is False
    assert word_matches_difficulty("a", "Meaning.", "beginner") is False
    assert word_matches_difficulty("a" * 9, "Meaning.", "beginner") is False
    assert word_matches_difficulty("abcd", "m" * 161, "medium") is False
    assert word_matches_difficulty("abc", "Meaning.", "medium") is False
    assert word_matches_difficulty("abcde", "Meaning.", "hard") is False
    assert word_matches_difficulty("a" * 26, "Meaning.", "mixed") is False
    assert word_matches_difficulty("router", "Meaning.", "advanced") is False


def test_word_matches_difficulty_rejects_missing_or_name_like_meanings():
    blocked_meanings = [
        "No meaning found yet.",
        "A surname used by a family.",
        "A given name for a person.",
        "An acronym for a phrase.",
    ]

    for meaning in blocked_meanings:
        assert word_matches_difficulty("router", meaning, "mixed") is False


def test_word_matches_search_topic_filters_networking_and_cybersecurity_keywords():
    assert word_matches_search_topic("router", "A device on a network.", "computer networking") is True
    assert word_matches_search_topic("castle", "A stone building.", "computer networking") is False
    assert word_matches_search_topic("malware", "Software used in a cyber attack.", "cybersecurity") is True
    assert word_matches_search_topic("flower", "A garden plant.", "cybersecurity") is False


def test_word_matches_search_topic_returns_true_for_other_topics():
    assert word_matches_search_topic("flower", "A garden plant.", "reading") is True
    assert word_matches_search_topic("", "", "school") is True
