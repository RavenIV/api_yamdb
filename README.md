# Проект YaMDb

## Описание
Проект YaMDb собирает отзывы пользователей на различные произведения.
Запросы к API начинаются с /api/v1/.

## Алгоритм регистрации пользователей
1. Пользователь отправляет POST-запрос на добавление нового пользователя с параметрами email и username на эндпоинт /api/v1/auth/signup/.
2. YaMDB отправляет письмо с кодом подтверждения (confirmation_code) на адрес email.
3. Пользователь отправляет POST-запрос с параметрами username и confirmation_code на эндпоинт /api/v1/auth/token/, в ответе на запрос ему приходит token (JWT-токен).
4. При желании пользователь отправляет PATCH-запрос на эндпоинт /api/v1/users/me/ и заполняет поля в своём профайле (описание полей — в документации).

## Пользовательские роли
- Аноним — может просматривать описания произведений, читать отзывы и комментарии.
- Аутентифицированный пользователь (user) — может, как и Аноним, читать всё, дополнительно он может публиковать отзывы и ставить оценку произведениям (фильмам/книгам/песенкам), может комментировать чужие отзывы; может редактировать и удалять свои отзывы и комментарии. Эта роль присваивается по умолчанию каждому новому пользователю.
- Модератор (moderator) — те же права, что и у Аутентифицированного пользователя плюс право удалять любые отзывы и комментарии.
- Администратор (admin) — полные права на управление всем контентом проекта. Может создавать и удалять произведения, категории и жанры. Может назначать роли пользователям.
- Суперюзер Django — обладет правами администратора (admin)

## Регистрация нового пользователя
Получить код подтверждения на переданный email. Права доступа: Доступно без токена. Использовать имя 'me' в качестве username запрещено. Поля email и username должны быть уникальными. Должна быть возможность повторного запроса кода подтверждения.

## Получение JWT-токена
Получение JWT-токена в обмен на username и confirmation code. Права доступа: Доступно без токена.

## USERS
Пользователи

### Примеры
Получить список всех пользователей: GET /api/v1/users/. Права доступа: Администратор.
Добавить нового пользователя: POST /api/v1/users/ с данными {"username": "<username>", "email": "<email>", "first_name": "<first_name>", "last_name": "<last_name>", "bio": "<bio>", "role": "<role>"}. Права доступа: Администратор.
Получить пользователя по username: GET /api/v1/users/{username}/. Права доступа: Администратор.
Изменить данные пользователя по username: PATCH /api/v1/users/{username}/ с данными {"username": "<username>", "email": "<email>", "first_name": "<first_name>", "last_name": "<last_name>", "bio": "<bio>", "role": "<role>"}. Права доступа: Администратор.
Удалить пользователя по username: DELETE /api/v1/users/{username}/. Права доступа: Администратор.
Получить данные своей учетной записи: GET /api/v1/users/me/. Права доступа: Любой авторизованный пользователь.

## CATEGORIES
Категории (типы) произведений

### Примеры
Получить список всех категорий: GET /api/v1/categories/. Права доступа: Доступно без токена.
Добавить новую категорию: POST /api/v1/categories/ с данными {"name": "<name>", "slug": "<slug>"}. Права доступа: Администратор.
Удалить категорию: DELETE /api/v1/categories/{slug}/. Права доступа: Администратор.

## GENRES
Категории жанров

### Примеры
Получить список всех жанров: GET /api/v1/genres/. Права доступа: Доступно без токена.
Добавить новый жанр: POST /api/v1/genres/ с данными {"name": "<name>", "slug": "<slug>"}. Права доступа: Администратор.
Удалить жанр: DELETE /api/v1/genres/{slug}/. Права доступа: Администратор.

## TITLES
Произведения, к которым пишут отзывы (определённый фильм, книга или песенка).

### Примеры
Получить список всех произведений: GET /api/v1/titles/. Права доступа: Доступно без токена.
Добавить новое произведение: POST /api/v1/titles/ с данными {"name": "<name>", "year": <year>, "description": "<description>", "genre": ["<genre>"], "category": "<category>"}. Права доступа: Администратор.
Получить информацию о произведении: GET /api/v1/titles/{titles_id}/. Права доступа: Доступно без токена.
Частичное обновление информации о произведении: PATCH /api/v1/titles/{titles_id}/ с данными {"name": "<name>", "year": <year>, "description": "<description>", "genre": ["<genre>"], "category": "<category>"}. Права доступа: Администратор.
Удалить произведение: DELETE /api/v1/titles/{titles_id}/. Права доступа: Администратор.

## REVIEWS
Отзывы

### Примеры
Получить список всех отзывов: GET /api/v1/titles/{title_id}/reviews/. Права доступа: Доступно без токена.
Добавить новый отзыв: POST /api/v1/titles/{title_id}/reviews/ с данными {"text": "<text>", "score": <score>}. Права доступа: Аутентифицированные пользователи.
Получить отзыв по id: GET /api/v1/titles/{title_id}/reviews/{review_id}/. Права доступа: Доступно без токена.
Частичное обновление отзыва по id: PATCH /api/v1/titles/{title_id}/reviews/{review_id}/ с данными {"text": "<text>", "score": <score>}. Права доступа: Автор отзыва, модератор или администратор.
Удалить отзыв по id: DELETE /api/v1/titles/{title_id}/reviews/{review_id}/. Права доступа: Автор отзыва, модератор или администратор.

## COMMENTS
Комментарии к отзывам

### Примеры
Получить список всех комментариев к отзыву: GET /api/v1/titles/{title_id}/reviews/{review_id}/comments/. Права доступа: Доступно без токена.
Добавить новый комментарий для отзыва: POST /api/v1/titles/{title_id}/reviews/{review_id}/comments/ с данными {"text": "<text>"}. Права доступа: Аутентифицированные пользователи.
Получить комментарий для отзыва по id: GET /api/v1/titles/{title_id}/reviews/{review_id}/comments/{comment_id}/. Права доступа: Доступно без токена.
Частичное обновление комментария к отзыву по id: PATCH /api/v1/titles/{title_id}/reviews/{review_id}/comments/{comment_id}/ с данными {"text": "<text>"}. Права доступа: Автор комментария, модератор или администратор.
Удалить комментарий к отзыву по id: DELETE /api/v1/titles/{title_id}/reviews/{review_id}/comments/{comment_id}/. Права доступа: Автор комментария, модератор или администратор.


## Использованные технологии
В проекте были использованы следующие фреймворки и библиотеки:
Django (3.2): Высокоуровневый веб-фреймворк Python.
djangorestframework (3.12.4): Гибкий фреймворк для построения веб-API.
requests (2.26.0): Библиотека Python для отправки HTTP-запросов.
rest_framework_simplejwt: Библиотека для работы с JWT-токенами.
