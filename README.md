# Derek's Reading & Spelling Coach

A simple, offline spelling and vocabulary practice app.

This project is being built to help learners who need clear, step-by-step practice with spelling, reading, meanings, and memory.

The app is designed to be helpful for people with dyslexia, learning disabilities, adult learners, and students learning cybersecurity vocabulary.
## Features

- Practice spelling words
- Take a spelling test
- Save missed words
- Practice missed words
- Show word meanings
- Practice by level
- Save score history
- Store app data in a simple data folder
- Run offline without internet
  - ## Project Structure

```text
PythonProject1/
├── reading_spelling_coach.py
├── config.txt
├── backup_to_8tb.sh
├── CONTRIBUTING.md
├── LICENSE
├── .gitignore  
├── data/
│   ├── words.txt
│   ├── missed_words.txt
│   ├── meanings.txt
│   └── score_history.txt
└── README.md
## How to Run the App

Open a terminal inside the project folder:

```bash
cd /home/derek/PycharmProjects/PythonProject1
## Data Files

The app stores its information in the `data` folder.

- `words.txt` stores spelling words.
- `missed_words.txt` stores words that were missed.
- `meanings.txt` stores word meanings.
- `score_history.txt` stores spelling test scores.

The `config.txt` file tells the app where the data folder is located.

Current setting:

```text
APP_FOLDER=data
## Project Goal

The goal of this project is to build a simple, offline, dyslexia-friendly spelling and vocabulary coach.

This app is being built step by step as a learning project. The long-term goal is to make it useful for other learners who need clear instructions, repetition, and simple tools.

This project focuses on:

- Accessibility
- Clear language
- Step-by-step learning
- Spelling practice
- Vocabulary practice
- Cybersecurity terms
- Beginner-friendly Python code
## How to Contribute

This project is open to ideas, feedback, and improvements.

People can help by:

- Testing the app
- Reporting bugs
- Suggesting accessibility improvements
- Improving dyslexia-friendly wording
- Adding beginner-friendly Python comments
- Adding new word lists
- Adding cybersecurity vocabulary
- Improving the user interface
- Helping make the app easier for non-technical users

The goal is to keep the app simple, readable, and helpful.

## License

This project uses the MIT License.

That means other people can use, study, change, and share the code as long as the license notice stays with the project.

See the `LICENSE` file for details. 
## Dashboard Prototype 1

Dashboard Prototype 1 is a separate local desktop interface. It does not replace the terminal app.

Start the dashboard from the project folder with:

```bash
python -m dashboard.app
```

Return to the terminal version at any time with:

```bash
python reading_spelling_coach.py
```

The dashboard uses Python Tkinter from the standard library. It runs locally, does not require a paid service, and does not expose the app to the public internet.
