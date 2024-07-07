```sh

# Создание Активация Установка
cd .venv/Scripts && source activate && cd ../.. && pip install -r requirements.txt

# добавить тэг
git tag -a v1.0.0 -m "First release"
git push origin v1.0.0

# Удалить старый тег локально
git tag -d v1.0.0

# Удалить старый тег на удаленном репозитории
git push origin :refs/tags/v1.0.0

# Создать новый тег на последнем коммите
git tag -a v1.0.0 -m "First release"

# Отправить новый тег на удаленный репозиторий
git push origin v1.0.0

# Создайте или обновите тег
git tag -fa v1.0.0 -m "Release update v1.0.0" 
git push origin v1.0.0 --force

# создать или обновить существующий локально без описания
git tag -fa v1.0.0 -m "" && git push origin v1.0.0 --force
```
