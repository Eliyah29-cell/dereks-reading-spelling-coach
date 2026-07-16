# Derek's Reading & Spelling Coach
## Project Status, Testing Results, and Development Roadmap

## Project Purpose

Derek's Reading & Spelling Coach is a learning application designed to support:

- People with dyslexia
- Students
- People improving reading skills
- People improving spelling and writing
- People building vocabulary
- People improving reading comprehension
- Learners working with cybersecurity or other subjects

Cybersecurity is one important topic, but the application is intended to support many subjects.

The long-term goal is to create a clear, useful, and accessible application that can run on desktop computers, tablets, and cellphones.

---

## Current Project Status

The current program is a working Python application.

All 18 menu options have been tested.

Most core features work, but several usability problems and confirmed bugs were found.

The testing phase is now complete.

No major feature development should begin until:

1. The testing records are documented.
2. The tested project is backed up to GitHub.
3. The GitHub backup is verified.
4. The 8 TB backup process is corrected and verified.
5. Derek approves the next development phase.

---

## Current Working Features

The application currently includes:

- Practice all words
- Spelling tests
- Adding new words
- Viewing the word list
- Missed-word practice
- Viewing missed words
- Clearing missed words
- Viewing word meanings
- Practice by difficulty level
- Score history
- Internet word search
- Pending-word review
- Pending-word approval
- Random word practice
- Random practice by level
- Progress reporting
- Individual word pronunciation
- Quit and restart support

The application can also save:

- Words
- Meanings
- Missed words
- Scores
- Internet word suggestions
- Pending words

---

## Confirmed Successful Tests
All 18 main-menu options were manually tested. Each option opened and performed its primary function without crashing. Confirmed bugs and usability findings are documented in the sections below.
The following core behaviors were confirmed:

- Missed words can be displayed.
- Missed words can be cleared.
- The cleared list can be verified as empty.
- Word meanings can be displayed.
- Practice by level accepts correct answers.
- Practice by level detects incorrect spelling.
- Score history displays saved scores.
- The program quits and closes correctly.
- The application can be reopened.
- Internet word search can return suggestions.
- Internet suggestions can display meanings.
- Suggestions numbered higher than 5 can be selected.
- Selected internet words can be saved as pending.
- Pending words can be displayed.
- Choosing No during approval keeps words pending.
- Choosing Yes approves pending words.
- Approved words are added to the main word list.
- Approved words are removed from the pending list.
- The progress report displays saved information.
- The individual Pronounce a Word feature works.

---

## Confirmed Bugs

### 1. Random practice does not pronounce hidden words

Options 15 and 16 hide the target word and ask the learner to spell it.

However:

- No word is displayed.
- No pronunciation is played.
- The learner cannot know which word to spell.

This makes both activities unusable in their current form.

Affected features:

- Random word practice
- Random practice by level

### Required correction

The application must provide:

- A Play Word button
- A Repeat Word button
- Clear audio pronunciation
- A visible attempt counter
- A way to return to the dashboard

---

### 2. The 8 TB backup can report false success

During testing, the 8 TB drive was not mounted.

The automatic backup displayed errors including:

- Permission denied
- No such file or directory
- Files could not be copied

The application still displayed messages saying that the backup was complete.

### Required correction

The backup system must:

- Check whether the drive is mounted.
- Check whether the destination is writable.
- Stop when copying fails.
- Display Backup Failed when an error occurs.
- Never report success after failed copy operations.
- Verify that backup files exist after copying.
- Record the date and result of each backup.

The 8 TB drive was later mounted manually.

A timestamped safety snapshot was successfully created and tested, but the automatic backup script still needs correction and retesting.

---

### 3. Word and meaning totals do not match

The progress report showed:

- Total words: 64
- Total meanings: 63

The confirmed missing meaning belongs to:

- `sandbox`

### Required correction

Every saved word should have:

- A meaning
- A topic
- A difficulty level
- A review status

The application should detect incomplete records before saving them.

---

## Confirmed Usability Problems

### Long stacked menu

The current menu places all 18 options in one long vertical list.

This creates:

- Visual crowding
- Unnecessary scrolling
- Difficulty finding the next action
- Problems on smaller screens
- Reduced focus for learners with dyslexia

### Menu and report compete for attention

When a feature or report opens, the full menu remains on the screen.

For example, the progress report appears above the menu, while the active prompt is pushed below it.

The selected feature should become the main focus.

### Screen does not automatically move to the active prompt

After long reports and tests, the user may need to scroll manually to find the next prompt.

The application should automatically keep the active task and next action visible.

---

## Dashboard Development Priority

The dashboard should be the main focus of the next development phase.

The dashboard must not be one long stacked menu.

It should organize features into separate visual sections.

Suggested dashboard groups:

### Practice

- Word practice
- Spelling practice
- Missed-word practice
- Random practice

### Reading

- Reading practice
- Reading comprehension
- Passage questions
- Vocabulary from passages

### Words and Meanings

- Word list
- Add a word
- Meanings
- Pronunciation
- Topics
- Difficulty levels

### Internet Words

- Search for words
- Review suggestions
- Approve or reject words
- Review pending words

### Progress

- Progress report
- Score history
- Missed words
- Learning goals

### Settings and Safety

- Audio settings
- Display settings
- Backup status
- GitHub status
- Data management

---

## Dashboard Design Rules

The dashboard should:

- Use separate cards, tiles, or panels.
- Use clear headings.
- Use enough spacing between sections.
- Avoid crowded text.
- Use large readable controls.
- Keep related features together.
- Hide unrelated information during an activity.
- Show one main task at a time.
- Include a clear Back to Dashboard button.
- Automatically keep the active area visible.
- Use icons and labels together.
- Never depend only on color to explain information.

Expandable or drop-down sections may be used.

Only the selected section should open.

Opening one section may automatically close the previous section to keep the interface clean.

---

## Cellphone and Responsive Design Requirements

Cellphone support is an essential future requirement.

Every feature should be planned for:

- Desktop monitors
- Laptops
- Tablets
- Cellphones

The cellphone version should not simply shrink the desktop interface.

It should use:

- Large touch-friendly buttons
- Clear spacing
- Short sections
- One primary task per screen
- No horizontal scrolling
- Clear Play and Repeat audio buttons
- Easy navigation
- Readable text sizes
- Expandable dashboard sections

The desktop and cellphone versions should provide the same learning functions while arranging them appropriately for each screen size.

---

## Topics and Difficulty Must Be Separate

The current application sometimes mixes topic and difficulty.

For example, cybersecurity appears beside Easy, Medium, and Hard.

Future design should ask the learner to choose separately:

### Topic

Examples:

- Cybersecurity
- School
- Recovery
- Daily life
- Work
- Technology
- Science
- Mathematics
- User-created topics

### Difficulty

- Beginner
- Intermediate
- Advanced

A topic should not automatically determine difficulty.

---

## Spelling and Pronunciation Requirements

During a spelling test:

- The target word should not be displayed before the answer.
- The application should pronounce the word.
- The learner should be able to replay it.
- The pronunciation should be clear and consistent.
- The learner should receive three attempts.

The screen should display:

- Attempt 1 of 3
- Play Word
- Repeat Word
- Answer box
- Submit
- Back to Dashboard

After the third incorrect attempt:

- Show the correct spelling.
- Pronounce the word again.
- Save it for later practice.
- Explain the meaning when appropriate.

The three-attempt rule should apply to:

- Spelling tests
- Random word practice
- Random practice by level
- Future combined spelling activities

---

## Combine Random Practice Features

The current application has:

- Random word practice
- Random practice by level

These should be combined into one clearer activity.

The learner should choose:

- Topic
- Difficulty
- Number of words
- Audio or visual practice
- Practice type

This will reduce duplicate menu options and save screen space.

---

## Reading Comprehension Requirements

Reading comprehension is an essential future feature.

It should include:

- Short reading passages
- Different difficulty levels
- User-selected topics
- Main-idea questions
- Detail questions
- Vocabulary questions
- Clear answer feedback
- The ability to read the passage again
- The ability to hear the passage
- Progress tracking
- Missed-question review

Reading comprehension should support many subjects, not only cybersecurity.

---

## Definition and Meaning Improvements

When a new word is added, the application should automatically suggest a definition.

The learner or reviewer must remain in control.

The application should allow the user to:

- Approve the definition
- Reject the definition
- Choose between definitions
- Edit the definition
- Replace the definition
- Change the assigned difficulty
- Select the correct topic

Definitions should become more detailed at higher learning levels.

### Beginner

- Short
- Plain language
- One clear meaning

### Intermediate

- More explanation
- A simple example
- Relevant context

### Advanced

- More detail
- Subject-specific use
- Multiple meanings when needed
- More complex examples

---

## Internet Word Search Improvements

The future internet-word process should:

1. Ask for a topic.
2. Ask for a difficulty.
3. Display suggested words before saving.
4. Display each word with its meaning.
5. Let the user approve or reject each word.
6. Show a final review screen.
7. Save only approved words.

The selection prompt should clearly state the full number range.

Example:

> Enter any numbers from 1 to 13, separated by commas.

The application should also consider:

- Number ranges such as `1-5`
- Yes or No buttons
- Checkboxes or selection cards
- Exact-word searching
- Better topic matching
- Clear explanations when no useful words are found

The separate pending-word menu may later be renamed or simplified after the internet workflow is improved.

---

## Score and Progress Improvements

Score history currently displays:

- Date
- Time
- Score

Future score records should also include:

- Topic
- Difficulty
- Activity type
- Words missed
- Number of attempts
- Accuracy percentage

The progress dashboard should clearly separate:

- Recent activity
- Words needing practice
- Reading comprehension progress
- Spelling progress
- Vocabulary growth
- Topic progress
- Current learning goals

Progress information should be visual but not crowded.

---

## Missed-Word Improvements

Future missed-word management should include:

- Number of missed words
- Topic of each word
- Date last missed
- Number of incorrect attempts
- Number of correct reviews
- Optional cleanup after a selected time
- Confirmation before deletion
- A message showing how many words were erased

---

## Accessibility Principles

All changes should be reviewed with dyslexia and learning accessibility in mind.

Important principles include:

- Plain language
- Short instructions
- Clear headings
- Consistent button placement
- Limited clutter
- Strong visual separation
- Readable spacing
- Repetition when helpful
- Audio support
- Large controls
- Clear feedback
- One task at a time
- No unnecessary scrolling

Appearance is an essential part of usability.

The visual design should be developed with input from people who understand dyslexia, education, and accessible user-interface design.

---

## Contributor Opportunities

The project welcomes help from:

- Python programmers
- User-interface designers
- Mobile-app developers
- Dyslexia specialists
- Teachers
- Reading specialists
- Students
- Cybersecurity learners
- Accessibility testers
- Documentation writers
- Open-source contributors

Contributors may help with:

- Reviewing the current code
- Improving accessibility
- Designing the dashboard
- Building reading-comprehension activities
- Reviewing word definitions
- Testing pronunciation
- Improving progress tracking
- Writing automated tests
- Improving backup safety
- Planning cellphone support
- Reviewing cybersecurity vocabulary
- Testing with real learners

---

## Contribution Safety Rules

Contributors should:

- Keep changes small and understandable.
- Explain what each change does.
- Add or update tests.
- Preserve working code.
- Create backups before major changes.
- Avoid deleting learner data.
- Follow accessibility requirements.
- Keep topics separate from difficulty.
- Test desktop and cellphone layouts.
- Never expose private learner information.
- Never report backup success without verification.

---

## Local AI Agent Plan

A future open-source local AI agent may assist with this project.

Initial AI-agent access should be restricted.

The agent may first be used to:

- Read project files
- Explain code
- Organize bugs
- Review documentation
- Suggest tests
- Recommend changes

The agent should not initially be allowed to:

- Change the tested copy automatically
- Delete files
- Push directly to GitHub
- Access unrelated personal folders
- Access the 8 TB drive without approval
- Run unrestricted system commands

A separate agent-testing copy should be created before allowing code changes.

The project currently plans to use a local open-source model after documentation and backups are complete.

---

## Backup and Repository Requirements

Before development continues:

1. Update this project report.
2. Review the testing results.
3. Commit the approved data and documentation changes.
4. Push the tested project to GitHub.
5. Verify that GitHub contains the correct files.
6. Correct the automatic 8 TB backup.
7. Verify the 8 TB backup.
8. Create a separate development copy.
9. Begin the next development phase only after approval.

`ModuleSixAssignment.py` is not part of this project and should be excluded from project backups, GitHub updates, and AI-agent work.

---

## Immediate Next Priorities

### Priority 1

Complete and review contributor-ready documentation.

### Priority 2

Create and verify the GitHub backup.

### Priority 3

Correct and verify the 8 TB backup system.

### Priority 4

Create a protected development and AI-agent workspace.

### Priority 5

Plan the dashboard before coding it.

### Priority 6

Correct pronunciation in random practice and spelling activities.

### Priority 7

Begin approved feature development one feature at a time.

---

## Project Direction

The project has a usable foundation.

It is not ready for public release, but it already demonstrates practical value for:

- Spelling practice
- Vocabulary development
- Pronunciation
- Progress tracking
- Structured learning
- Focus and repetition

The project will continue carefully, with testing, accessibility, backup safety, and learner needs taking priority over speed.

---

## Dashboard Prototype 1 Status

Dashboard Prototype 1 has been added for human review. It is a local Tkinter desktop dashboard that runs separately from the terminal application.

### Prototype 1 decisions

- The terminal application remains available as the fallback interface.
- The dashboard starts with `python -m dashboard.app`.
- Tkinter was chosen because it is included with normal Python installs, avoids a web server, avoids paid services, works offline, and keeps the prototype low risk on Linux Mint.
- A browser-based dashboard remains a possible future option for phone or tablet support, but it would require more web-server code and security review.
- No deployment has been performed.

### Prototype 1 features

- Grouped dashboard home screen for Practice, Word Library, Review and Progress, and Application controls.
- Separate activity screen instead of one long terminal-style menu.
- Random Practice dashboard flow with visible word, meaning, repeat pronunciation, answer entry, scoring, and missed-word saving.
- Spelling Test dashboard flow with hidden word before answer, repeat pronunciation, answer entry, scoring, and reveal after an incorrect answer.
- Score history now supports new activity labels while preserving old unlabeled score records.
- Dashboard Clear Missed Words asks for confirmation before clearing.
- Basic adjustable text size and high-contrast display controls are included.
- Auto-scroll state logic is present for keeping the active prompt visible while allowing manual review pauses.

### Future missed-word improvement recorded

A future version should add a learner-controlled `Mark as learned` action. The learner should confirm removal, only the selected word should be removed, and missed words should not be removed automatically after a correct practice answer.

### Known Prototype 1 limits

- Visual accessibility has not been fully tested by Derek yet.
- Phone and tablet support is not implemented yet.
- Some dashboard buttons are wired as Prototype 1 placeholders and still direct the learner to use the terminal workflow for full behavior.
- Dashboard Random Practice and Spelling Test currently start with one word to keep the prototype small and safe.
- Internet-word workflows are not run during automated tests and need more dashboard-specific implementation later.
- Backup workflows are not run from automated tests.

### Dashboard Prototype 1 Revision Notes

Human review found blockers in the first dashboard prototype. The revision corrected these items before local testing:

- Dashboard Home now uses a scrollable Tkinter canvas with a scrollbar, mouse-wheel support, and keyboard scrolling for Page Up, Page Down, Home, and End.
- Prototype 1 buttons are now clearly classified: finished controls are clickable, and unfinished controls are disabled with `Not available in Prototype 1` in the label.
- Random Practice no longer silently uses only the first word. The learner chooses a group, chooses how many words to practice from 1 through the available maximum, and the dashboard uses random selection.
- Spelling Test no longer silently uses only the first word. It uses the current spelling-test word set and shows question number and total.
- The real Tkinter dashboard now calls the auto-scroll state when activity prompts and feedback are shown, detects manual upward scrolling, and provides `Jump to current question` when auto-scroll is paused.
- Accessibility changes for text size, spacing, and high contrast re-render the current view without creating a new activity session.
- Back and Home are now different: Home returns to Dashboard Home, while Back returns to the previous dashboard screen where possible.

Functional Prototype 1 dashboard controls:

- Spelling Test
- Random Practice
- Show Word List
- Show Word Meanings
- Show Missed Words
- Clear Missed Words
- Score History
- Return Home
- Exit Dashboard

Unfinished Prototype 1 dashboard controls:

- Practice All Words
- Practice by Level
- Practice Missed Words
- Add a New Word
- Pronounce a Word
- Get New Words from the Internet
- Show Pending Words
- Approve Pending Words
- Progress Report
