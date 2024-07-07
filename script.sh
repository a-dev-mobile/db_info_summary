#!/bin/sh

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
