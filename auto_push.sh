#!/bin/bash
# Скрипт для автоматического добавления, коммита и пуша изменений в git

# Проверяем есть ли изменения
if [[ -n $(git status -s) ]]; then
  git add .
  git commit -m "Auto commit"
  git push origin main
fi
