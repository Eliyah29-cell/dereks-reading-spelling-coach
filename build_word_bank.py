# Derek's Reading & Spelling Coach
# Word Bank Builder

import os

APP_FOLDER = "data"
WORDS_FILE = os.path.join(APP_FOLDER, "words.txt")
MEANINGS_FILE = os.path.join(APP_FOLDER, "meanings.txt")

WORD_BANK = [
    ("security", "Protection from danger, damage, or unauthorized access."),
    ("computer", "An electronic device that stores and processes information."),
    ("network", "A group of connected computers or devices that can share information."),
    ("password", "A secret word or phrase used to access an account or system."),
    ("firewall", "A security tool that helps block unsafe network traffic."),
    ("malware", "Harmful software made to damage, steal, or take control of a computer."),
    ("phishing", "A fake message or website that tries to steal private information."),
    ("software", "Programs and apps that tell a computer what to do."),
    ("hardware", "The physical parts of a computer."),
    ("internet", "A worldwide network that connects computers and websites."),
    ("router", "A device that sends network traffic between devices and the internet."),
    ("encryption", "A way to scramble information so only allowed people can read it."),
    ("authentication", "The process of proving who you are."),
    ("username", "The name used to identify a person on a computer or website."),
    ("backup", "A saved copy of important files."),
    ("update", "A change that fixes, improves, or protects software."),
    ("cybersecurity", "Protecting computers, networks, and data from attacks."),
    ("privacy", "Keeping personal information protected."),
    ("risk", "The chance that something bad could happen."),
    ("threat", "Something that could cause harm to a system or data."),
    ("vulnerability", "A weakness that can be used to attack a system."),
    ("ransomware", "Malware that locks files and demands payment."),
    ("browser", "A program used to visit websites."),
    ("folder", "A place where files are stored."),
    ("terminal", "A tool used to type commands into the computer."),
    ("command", "An instruction typed into the terminal."),
    ("directory", "Another name for a folder."),
    ("linux", "An operating system often used for security, servers, and learning."),
    ("python", "A programming language used for scripts, apps, and learning."),
    ("script", "A file that contains commands or code to run."),
    ("input", "Information the user gives to a program."),
    ("output", "Information a program shows to the user."),
    ("string", "Text used in a program."),
    ("integer", "A whole number."),
    ("boolean", "A value that is either True or False."),
    ("list", "A Python container that stores multiple items in order."),
    ("dictionary", "A Python container that stores key and value pairs."),
    ("loop", "Code that repeats while a condition is true."),
    ("function", "A block of code that performs a task."),
    ("error", "A problem in code that stops it or makes it work incorrectly."),
    ("assignment", "School work that must be completed."),
    ("chapter", "A section of a book or lesson."),
    ("discussion", "Talking or writing about a topic with others."),
    ("explain", "To make something clear or easy to understand."),
    ("learning", "Gaining knowledge or skill."),
    ("module", "A section of a course or class."),
    ("project", "A larger task that takes planning and work."),
    ("question", "A sentence that asks for information."),
    ("research", "Looking for information to learn about a topic."),
    ("summary", "A short explanation of the main ideas."),
]


def build_word_files():
    os.makedirs(APP_FOLDER, exist_ok=True)

    with open(WORDS_FILE, "w", encoding="utf-8") as words_file:
        for word, meaning in WORD_BANK:
            words_file.write(word + "\n")

    with open(MEANINGS_FILE, "w", encoding="utf-8") as meanings_file:
        for word, meaning in WORD_BANK:
            meanings_file.write(word + "|" + meaning + "\n")

    print("Word bank complete.")
    print(f"Words saved to: {WORDS_FILE}")
    print(f"Meanings saved to: {MEANINGS_FILE}")
    print(f"Total words: {len(WORD_BANK)}")


if __name__ == "__main__":
    build_word_files()