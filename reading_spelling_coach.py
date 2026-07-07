import random
from datetime import datetime
import urllib.error
import urllib.request
import urllib.parse
import json
import subprocess
import os
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
PENDING_WORDS_FILE = APP_FOLDER + "/pending_words.txt"
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




def backup_project_to_8tb():
    print("\nStarting automatic 8TB backup...")

    try:
        project_folder = os.path.dirname(os.path.abspath(__file__))
        backup_script = os.path.join(project_folder, "backup_to_8tb.sh")

        subprocess.run(["bash", backup_script], cwd=project_folder, check=True)

        print("Automatic 8TB backup complete.")
    except FileNotFoundError:
        print("Backup script was not found. Please run ./backup_to_8tb.sh manually.")
    except subprocess.CalledProcessError:
        print("Automatic backup had a problem. Please run ./backup_to_8tb.sh manually.")



def prepare_internet_search_topic(topic):
    topic = topic.strip()
    topic_lower = topic.lower()

    topic_map = {
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

    return topic_map.get(topic_lower, topic)


def word_matches_search_topic(word, meaning, search_topic):
    text = f"{word} {meaning}".lower()
    search_topic = search_topic.lower()

    if search_topic == "computer networking":
        networking_keywords = [
            "computer", "network", "internet", "router", "switch",
            "server", "firewall", "packet", "protocol", "dns",
            "ip", "subnet", "ethernet", "wireless", "wifi",
            "wi-fi", "lan", "wan", "data", "communication"
        ]

        return any(keyword in text for keyword in networking_keywords)

    if search_topic == "cybersecurity":
        security_keywords = [
            "security", "cyber", "password", "malware", "virus",
            "firewall", "encryption", "attack", "threat",
            "network", "computer", "data", "authentication"
        ]

        return any(keyword in text for keyword in security_keywords)

    return True


def clean_internet_word(word):
    word = word.strip().lower()

    if not word:
        return ""

    allowed_characters = "abcdefghijklmnopqrstuvwxyz-"
    for letter in word:
        if letter not in allowed_characters:
            return ""

    if len(word) < 2 or len(word) > 25:
        return ""

    return word


def clean_definition(raw_definition):
    raw_definition = raw_definition.strip()

    if "\t" in raw_definition:
        raw_definition = raw_definition.split("\t", 1)[1]

    raw_definition = raw_definition.replace("\n", " ").strip()

    if not raw_definition:
        return "No meaning found yet."

    return raw_definition


def load_word_set(file_name):
    try:
        with open(file_name, "r") as file:
            return {line.strip().split("|")[0].strip().lower() for line in file if line.strip()}
    except FileNotFoundError:
        return set()


def get_words_from_internet():
    print("\nGet New Words From the Internet")
    print("===============================")
    print("Safety rule: This only downloads text words and meanings.")
    print("It does not download or run code.\n")

    topic = input("Enter a topic or category, like computer networking, cybersecurity, school, or family: ").strip()

    if not topic:
        print("\nNo topic entered. Returning to the main menu.")
        return

    search_topic = prepare_internet_search_topic(topic)

    if search_topic.lower() != topic.lower():
        print(f"Using safer search topic: {search_topic}")

    safe_topic = urllib.parse.quote(search_topic)
    url = f"https://api.datamuse.com/words?ml={safe_topic}&md=d&max=10"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError:
        print("\nInternet error. Check your connection and try again.")
        return
    except TimeoutError:
        print("\nThe internet request took too long. Try again later.")
        return
    except Exception as error:
        print(f"\nSomething went wrong: {error}")
        return

    current_words = load_word_set(WORDS_FILE)
    pending_words = load_word_set(PENDING_WORDS_FILE)
    new_pending_words = []

    for item in data:
        word = clean_internet_word(item.get("word", ""))

        if not word:
            continue

        if word in current_words or word in pending_words:
            continue

        definitions = item.get("defs", [])
        if definitions:
            meaning = clean_definition(definitions[0])
        else:
            meaning = "No meaning found yet."

        if not word_matches_search_topic(word, meaning, search_topic):
            continue

        new_pending_words.append((word, meaning))

    if not new_pending_words:
        print("\nNo new words found for that topic.")
        return

    with open(PENDING_WORDS_FILE, "a") as file:
        for word, meaning in new_pending_words:
            file.write(f"{word}|{meaning}\n")

    print(f"\nSaved {len(new_pending_words)} new word suggestion(s) to pending_words.txt.")
    print("They were NOT added to your main word list yet.")
    print("Use option 13 later to review pending words.")


def show_pending_words():
    print("\nPending Words")
    print("=============")

    try:
        with open(PENDING_WORDS_FILE, "r") as file:
            pending = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("No pending_words.txt file found yet.")
        return

    if not pending:
        print("No pending words yet.")
        return

    for number, line in enumerate(pending, start=1):
        if "|" in line:
            word, meaning = line.split("|", 1)
        else:
            word = line
            meaning = "No meaning found yet."

        print(f"{number}. {word}")
        print(f"   Meaning: {meaning}")


def approve_pending_words():
    print("\nApprove Pending Words")
    print("=====================")

    try:
        with open(PENDING_WORDS_FILE, "r") as file:
            pending = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("No pending_words.txt file found yet.")
        return

    if not pending:
        print("No pending words to approve.")
        return

    print("These words are waiting for approval:\n")

    for number, line in enumerate(pending, start=1):
        if "|" in line:
            word, meaning = line.split("|", 1)
        else:
            word = line
            meaning = "No meaning found yet."

        print(f"{number}. {word} - {meaning}")

    answer = input("\nApprove ALL pending words? Type yes or no: ").strip().lower()

    if answer != "yes":
        print("\nNothing was approved.")
        return

    current_words = load_word_set(WORDS_FILE)
    approved_words = []
    approved_meanings = []

    for line in pending:
        if "|" in line:
            word, meaning = line.split("|", 1)
        else:
            word = line
            meaning = "No meaning found yet."

        word = clean_internet_word(word)

        if not word:
            continue

        if word in current_words:
            continue

        approved_words.append(word)
        approved_meanings.append(meaning.strip())
        current_words.add(word)

    if not approved_words:
        print("\nNo new words were approved.")
        return

    with open(WORDS_FILE, "a") as words_file:
        for word in approved_words:
            words_file.write(f"{word}\n")

    with open(MEANINGS_FILE, "a") as meanings_file:
        for meaning in approved_meanings:
            meanings_file.write(f"{meaning}\n")

    with open(PENDING_WORDS_FILE, "w") as pending_file:
        pending_file.write("")

    print(f"\nApproved {len(approved_words)} word(s).")
    print("The approved words were added to words.txt and meanings.txt.")
    print("pending_words.txt is now clear.")

    backup_project_to_8tb()



def random_word_practice(words):
    print("\nRandom Word Practice")
    print("====================")

    if not words:
        print("No words found. Please add words first.")
        return

    try:
        with open(MEANINGS_FILE, "r") as file:
            meanings = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        meanings = []

    if len(meanings) != len(words):
        meanings = ["No meaning found yet."] * len(words)

    max_words = len(words)

    amount_text = input(f"How many random words do you want to practice? 1 to {max_words}, or type q/menu to go back: ").strip().lower()

    if amount_text in ["q", "quit", "menu"]:
        print("Returning to main menu.")
        return

    try:
        amount = int(amount_text)
    except ValueError:
        print("Please enter a number.")
        return

    if amount < 1:
        print("Please choose at least 1 word.")
        return

    if amount > max_words:
        amount = max_words

    word_pairs = list(zip(words, meanings))
    selected_words = random.sample(word_pairs, amount)

    score = 0

    for number, (word, meaning) in enumerate(selected_words, start=1):
        print(f"\nWord {number} of {amount}")
        print(f"Meaning: {meaning}")

        answer = input("Spell the word, or type q/menu to go back: ").strip().lower()

        if answer in ["q", "quit", "menu"]:
            print("Returning to main menu.")
            return

        if answer == word.lower():
            print("Correct!")
            score += 1
        else:
            print(f"Not quite. The correct spelling is: {word}")
            save_missed_word(word)

    print(f"\nRandom practice complete. Score: {score} out of {amount}")
    save_score(score, amount)


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
    print("12. Get new words from the internet")
    print("13. Show pending words")
    print("14. Approve pending words")
    print("15. Random word practice")


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
        choice = input("\nChoose 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, or 15: ").strip()

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
        elif choice == "12":
            get_words_from_internet()
        elif choice == "13":
            show_pending_words()
        elif choice == "14":
            approve_pending_words()
        elif choice == "15":
            random_word_practice(words)
        else:
            print("\nPlease choose a valid option: 1 through 15.")


main()
