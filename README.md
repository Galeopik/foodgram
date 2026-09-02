# 🍽️ Foodgram

Foodgram — веб-приложение для публикации, поиска и сохранения рецептов.

Пользователи могут создавать собственные рецепты, добавлять рецепты в избранное, подписываться на других пользователей и формировать список покупок на основе выбранных рецептов.

Проект разработан с использованием Django REST Framework и React, контейнеризирован с помощью Docker и развёрнут на удалённом сервере.

## 🚀 Возможности

### 👤 Пользователи

- регистрация и авторизация;
- JWT-аутентификация;
- просмотр профиля пользователя;
- подписка и отписка от других пользователей;
- просмотр списка подписок.

### 🍳 Рецепты

- создание рецептов;
- редактирование и удаление собственных рецептов;
- просмотр рецептов других пользователей;
- добавление рецептов в избранное;
- удаление рецептов из избранного;
- добавление рецептов в список покупок;
- удаление рецептов из списка покупок;
- фильтрация рецептов по тегам.

### 🛒 Список покупок

На основе выбранных рецептов приложение автоматически формирует список необходимых ингредиентов с учётом их количества.

Сформированный список покупок можно скачать.

### 🏷️ Теги и ингредиенты

В приложении реализована работа с:

- тегами рецептов;
- ингредиентами;
- количеством ингредиентов;
- единицами измерения.

Исходные данные ингредиентов загружаются в базу данных с помощью специальной Django management-команды.

## 🛠️ Технологии

### Backend

- Python 3.12
- Django
- Django REST Framework
- Djoser
- Simple JWT
- PostgreSQL
- Gunicorn

### Frontend

- React
- JavaScript
- HTML
- CSS

### Инфраструктура

- Docker
- Docker Compose
- Nginx
- GitHub Actions
- Docker Hub
- Ubuntu

## 🐳 Запуск проекта

Для запуска проекта необходимо установить Docker и Docker Compose.

Клонировать репозиторий:

    git clone git@github.com:Galeopik/foodgram.git
    cd foodgram

Создать файл `.env` в корне проекта:

    POSTGRES_DB=db_foodgram
    POSTGRES_USER=django_user
    POSTGRES_PASSWORD=your_password

    DB_HOST=db
    DB_PORT=5432

    SECRET_KEY=your_secret_key

    DEBUG=False

    ALLOWED_HOSTS=localhost,127.0.0.1

Запустить контейнеры:

    docker compose up -d --build

После запуска приложение будет доступно по адресу:

    http://localhost:7000

## 🗄️ База данных

В production используется PostgreSQL.

Данные базы данных хранятся в отдельном Docker volume, поэтому пересоздание или обновление контейнеров не приводит к удалению данных.

В базе данных хранятся:

- пользователи;
- рецепты;
- ингредиенты;
- теги;
- избранные рецепты;
- подписки;
- списки покупок.

## 🥕 Загрузка ингредиентов

Для загрузки исходных ингредиентов используется кастомная management-команда Django:

    python manage.py load_ingredients

При использовании Docker:

    docker compose exec backend python manage.py load_ingredients

Данные загружаются из файла:

    data/ingredients.json

## 🔄 CI/CD

Для автоматизации сборки и публикации Docker-образов используется GitHub Actions.

Workflow запускается автоматически при каждом push в ветку `main`.

### Backend

GitHub Actions:

1. получает исходный код репозитория;
2. авторизуется в Docker Hub;
3. собирает Docker-образ backend;
4. публикует образ в Docker Hub.

Docker-образ:

    galeop/foodgram_backend:latest

### Frontend

Frontend также автоматически собирается и публикуется в Docker Hub.

Docker-образ:

    galeop/foodgram_frontend:latest

### Deployment

После публикации новых Docker-образов они используются для обновления приложения на удалённом сервере.

Общий процесс:

    git push
        ↓
    GitHub Actions
        ↓
    Сборка Docker-образов
        ↓
    Push в Docker Hub
        ↓
    Обновление на сервере
        ↓
    Docker Compose
        ↓
    Запущенный Foodgram

## 🌐 Production

Проект развёрнут на удалённой Ubuntu ВМ.

В production используются:

- Ubuntu;
- Docker;
- Docker Compose;
- PostgreSQL;
- Nginx;
- Gunicorn;
- Docker Hub;
- GitHub Actions.

Приложение доступно по адресу:

    https://foodgram-proj.bounceme.net

## 🔑 Основные API endpoints

### Аутентификация

    /api/auth/signup/
    /api/auth/token/login/
    /api/auth/token/logout/

### Пользователи

    /api/users/
    /api/users/me/
    /api/users/subscriptions/

### Рецепты

    /api/recipes/
    /api/recipes/{id}/

### Избранное

    /api/recipes/{id}/favorite/

### Список покупок

    /api/recipes/{id}/shopping_cart/
    /api/recipes/download_shopping_cart/

### Теги

    /api/tags/

### Ингредиенты

    /api/ingredients/

## 🔐 Переменные окружения

Секретные данные не хранятся непосредственно в исходном коде.

Используются следующие переменные окружения:

    SECRET_KEY
    DEBUG
    ALLOWED_HOSTS

    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD

    DB_HOST
    DB_PORT

Файл `.env` не должен добавляться в Git-репозиторий.

## 👨‍💻 Автор

**Galeop**

[Python Backend Developer](https://github.com/Galeopik)

Проект выполнен в рамках обучения и практики разработки backend-приложений на Python и Django.