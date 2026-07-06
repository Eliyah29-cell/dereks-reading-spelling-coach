import random
from datetime import datetime
CONFIG_FILE = "config.txt"


def load_app_folder():
    try:
        with open(CONFIG_FILE, "r") as file:
            for line in file:
                line = line.strip()

                if line.startswith("APP_FOLDER="):
                    return line.replace("APP_FOLDER=", "").strip()

    except FileNotFoundError:
        print("config.txt was not found.")

    return "data"


APP_FOLDER = load_app_folder()

WORDS_FILE = APP_FOLDER + "/words.txt"
MISSED_WORDS_FILE = APP_FOLDER + "/missed_words.txt"
MEANINGS_FILE = APP_FOLDER + "/meanings.txt"
SCORE_HISTORY_FILE = APP_FOLDER + "/score_history.txt"

LEVELS = {
    "easy": ["computer", "internet", "software", "hardware", "backup"],
    "medium": ["network", "password", "router", "username", "update"],
    "hard": ["phishing", "malware", "encryption", "authentication"],
    "cybersecurity": [
        "security",
        "password",
        "firewall",
        "malware",
        "phishing",
        "router",
        "encryption",
        "authentication"
    ]
}


def save_words(words):
    with open(WORDS_FILE, "w") as file:
        for word in words:
            file.write(word + "\n")


def load_words():
    default_words = [
        "security",
        "computer",
        "network",
        "password",
        "firewall",
        "malware",
        "phishing",
        "software",
        "hardware",
        "internet",
        "router"
    ]

    try:
        with open(WORDS_FILE, "r") as file:
            saved_words = [line.strip().lower() for line in file if line.strip()]

        if saved_words:
            return saved_words
        else:
            save_words(default_words)
            return default_words

    except FileNotFoundError:
        save_words(default_words)
        return default_words


def load_meanings():
    meanings = {}

    try:
        with open(MEANINGS_FILE, "r") as file:
            for line in file:
                line = line.strip()

                if "|" in line:
                    word, meaning = line.split("|", 1)
                    meanings[word.strip().lower()] = meaning.strip()

    except FileNotFoundError:
        print("Meanings file was not found.")

    return meanings


def save_missed_word(word):
    missed_words = load_missed_words()

    if word not in missed_words:
        missed_words.append(word)

    with open(MISSED_WORDS_FILE, "w") as file:
        for missed_word in missed_words:
            file.write(missed_word + "\n")


def load_missed_words():
    try:
        with open(MISSED_WORDS_FILE, "r") as file:
            return [line.strip().lower() for line in file if line.strip()]
    except FileNotFoundError:
        return []


def clear_missed_words():
    with open(MISSED_WORDS_FILE, "w") as file:
        file.write("")


def save_score(score, total):
    now = datetime.now()
    date_text = now.strftime("%Y-%m-%d %I:%M %p")

    with open(SCORE_HISTORY_FILE, "a") as file:
        file.write(f"{date_text} | Score: {score} out of {total}\n")


def show_score_history():
    print("\nScore History")
    print("==============================")

    try:
        with open(SCORE_HISTORY_FILE, "r") as file:
            scores = [line.strip() for line in file if line.strip()]

        if not scores:
            print("No scores saved yet.")
        else:
            for score in scores:
                print(score)

    except FileNotFoundError:
        print("No score history file found yet.")


def show_menu():
    print("\n==============================")
    print(" Derek's Reading & Spelling Coach")
    print("==============================")
    print("1. Practice all words")
    print("2. Take spelling test")
    print("3. Add a new word")
    print("4. Show word list")
    print("5. Practice missed words")
    print("6. Show missed words")
    print("7. Clear missed words")
    print("8. Show word meanings")
    print("9. Practice by level")
    print("10. Show score history")
    print("11. Quit")


def practice_words(words):
    if not words:
        print("\nNo words to practice.")
        return

    meanings = load_meanings()

    print("\nPractice Words")
    print("Read the meaning, then type the word exactly as you see it.\n")

    for word in words:
        print(f"Word: {word}")

        if word in meanings:
            print(f"Meaning: {meanings[word]}")
        else:
            print("Meaning: No meaning saved yet.")

        answer = input("Type the word: ").strip().lower()

        if answer == word:
            print("Correct!\n")
        else:
            print(f"Not quite. The correct spelling is: {word}\n")
            save_missed_word(word)


def spelling_test(words):
    if not words:
        print("\nNo words available for the test.")
        return

    print("\nSpelling Test")
    print("I will show you the word.")
    print("Then you will type it from memory.\n")

    test_words = words.copy()
    random.shuffle(test_words)

    score = 0
    missed_words = []

    for word in test_words:
        print(f"Study this word: {word}")
        input("Press Enter when you are ready to spell it...")

        print("\n" * 20)

        answer = input("Spell the word: ").strip().lower()

        if answer == word:
            print("Correct!\n")
            score += 1
        else:
            print(f"Incorrect. The correct spelling is: {word}\n")
            missed_words.append(word)
            save_missed_word(word)

    print("==============================")
    print(" Test Results")
    print("==============================")
    print(f"Score: {score} out of {len(test_words)}")

    save_score(score, len(test_words))

    if missed_words:
        print("\nWords to practice again:")
        for word in missed_words:
            print(f"- {word}")
    else:
        print("\nGreat job! You spelled every word correctly.")


def add_word(words):
    new_word = input("\nEnter a new word to add: ").strip().lower()

    if new_word == "":
        print("No word was added.")
    elif new_word in words:
        print("That word is already in the list.")
    else:
        words.append(new_word)
        save_words(words)
        print(f"Added and saved word: {new_word}")
        print("You can add a meaning for it later in meanings.txt.")


def show_word_list(words):
    print("\nCurrent Word List")
    print("==============================")

    for word in words:
        print(f"- {word}")


def practice_missed_words():
    missed_words = load_missed_words()

    if not missed_words:
        print("\nNo missed words yet. Great job.")
    else:
        print("\nPractice Missed Words")
        print("==============================")
        practice_words(missed_words)


def show_missed_words():
    missed_words = load_missed_words()

    print("\nMissed Words")
    print("==============================")

    if not missed_words:
        print("No missed words saved.")
    else:
        for word in missed_words:
            print(f"- {word}")


def show_word_meanings(words):
    meanings = load_meanings()

    print("\nWord Meanings")
    print("==============================")

    for word in words:
        print(f"\n{word}")

        if word in meanings:
            print(f"Meaning: {meanings[word]}")
        else:
            print("Meaning: No meaning saved yet.")


def practice_by_level():
    print("\nPractice by Level")
    print("==============================")
    print("1. Easy")
    print("2. Medium")
    print("3. Hard")
    print("4. Cybersecurity")
    print("5. Go back")

    level_choice = input("\nChoose 1, 2, 3, 4, or 5: ").strip()

    if level_choice == "1":
        practice_words(LEVELS["easy"])
    elif level_choice == "2":
        practice_words(LEVELS["medium"])
    elif level_choice == "3":
        practice_words(LEVELS["hard"])
    elif level_choice == "4":
        practice_words(LEVELS["cybersecurity"])
    elif level_choice == "5":
        print("\nReturning to main menu.")
    else:
        print("\nPlease choose a valid level.")


def main():
    words = load_words()

    while True:
        show_menu()
        choice = input("\nChoose 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, or 11: ").strip()

        if choice == "1":
            practice_words(words)
        elif choice == "2":
            spelling_test(words)
        elif choice == "3":
            add_word(words)
        elif choice == "4":
            show_word_list(words)
        elif choice == "5":
            practice_missed_words()
        elif choice == "6":
            show_missed_words()
        elif choice == "7":
            clear_missed_words()
            print("\nMissed words cleared.")
        elif choice == "8":
            show_word_meanings(words)
        elif choice == "9":
            practice_by_level()
        elif choice == "10":
            show_score_history()
        elif choice == "11":
            print("\nGoodbye. Keep practicing.")
            break
        else:
            print("\nPlease choose a valid option: 1 through 11.")


main()