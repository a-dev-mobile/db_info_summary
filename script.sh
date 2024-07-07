#!/bin/sh

./script.sh venv                    # Создание виртуального окружения
./script.sh activate                # Активация виртуального окружения
./script.sh dependencies            # Установка зависимостей
./script.sh setup                   # Создание виртуального окружения и установка зависимостей
./script.sh run                     # Запуск приложения
./script.sh tag v1.0.0              # Присваивание тега и отправка в удаленный репозиторий
./script.sh changetag v1.0.0 v1.0.1 # Изменение текущего тега и отправка изменений в удаленный репозиторий




# Создание виртуального окружения
create_venv() {
    python -m venv .venv
}

# Активация виртуального окружения
activate_venv() {
    if [ -d ".venv/Scripts" ]; then
        # Windows (Command Prompt)
        .venv/Scripts/activate
    elif [ -d ".venv/bin" ]; then
        # Unix или MacOS (bash/zsh)
        . .venv/bin/activate
    else
        echo "Не удалось найти скрипт активации виртуального окружения"
        exit 1
    fi
}

# Установка зависимостей
install_dependencies() {
    pip install -r requirements.txt
}

# Объединяем команды для удобства
setup() {
    create_venv
    activate_venv
    install_dependencies
}

# Пример запуска приложения
run_app() {
    python app.py
}

# Основной скрипт
case "$1" in
    venv)
        create_venv
        ;;
    activate)
        activate_venv
        ;;
    dependencies)
        install_dependencies
        ;;
    setup)
        setup
        ;;
    run)
        run_app
        ;;
    *)
        echo "Usage: $0 {venv|activate|dependencies|setup|run}"
        exit 1
        ;;
esac
