#!/bin/bash

PROJECT_FOLDER="/home/derek/PycharmProjects/PythonProject1"
BACKUP_FOLDER="/media/derek/75c9eeae-958c-4234-a97b-6779ea87125b/Dereks-Spelling-Coach-Project-Backup"

echo "Starting backup..."

mkdir -p "$BACKUP_FOLDER"

cp "$PROJECT_FOLDER/reading_spelling_coach.py" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/config.txt" "$BACKUP_FOLDER/"
cp -r "$PROJECT_FOLDER/data" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/README.md" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/LICENSE" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/CONTRIBUTING.md" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/.gitignore" "$BACKUP_FOLDER/"
cp "$PROJECT_FOLDER/backup_to_8tb.sh" "$BACKUP_FOLDER/"

echo "Backup complete."
echo "Saved to:"
echo "$BACKUP_FOLDER"