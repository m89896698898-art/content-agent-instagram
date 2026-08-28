# Team Marketplace App

Мобильное приложение для команды: продажи и реклама по Wildberries и Ozon
за день / неделю / месяц, с личными аккаунтами и ролями (админ / сотрудник).

## Структура

```
backend/   Node.js + Express + TypeScript API (SQLite, JWT-авторизация)
mobile/    React Native (Expo) приложение
```

## Как это устроено

- Первый зарегистрированный пользователь автоматически становится **admin**,
  все последующие — **employee**.
- Данные о продажах/рекламе сейчас **демо-моки** — реалистичные, но
  сгенерированные, а не настоящие. Как только появятся API-ключи от
  Wildberries и Ozon, подключение делается в двух местах (см. ниже) без
  изменений на стороне мобильного приложения.
- Экран дашборда показывает переключатель периода (день/неделя/месяц) и
  маркетплейса (все/Wildberries/Ozon), карточки с итогами (продажи, заказы,
  расход на рекламу, ДРР) и график продаж по дням.

## Backend

```bash
cd backend
cp .env.example .env   # при необходимости поменяйте JWT_SECRET
npm install
npm run dev             # http://localhost:4000
```

Основные эндпоинты:

- `POST /auth/register` `{ email, password, name }`
- `POST /auth/login` `{ email, password }`
- `GET /auth/me` (Bearer token)
- `GET /stats?period=day|week|month&marketplace=wildberries|ozon` (Bearer token)
- `GET /stats/credentials` — только для admin, посмотреть статус API-ключей
- `PUT /stats/credentials/:marketplace` — только для admin, задать `{ apiKey, clientId? }`

### Подключение реальных данных Wildberries / Ozon

1. Получите API-ключ в личном кабинете продавца:
   - Wildberries: раздел «Доступ к API» → ключ для Statistics API и Advert API.
   - Ozon: раздел «Seller API» → `Client-Id` + `Api-Key`.
2. Сохраните их через `PUT /stats/credentials/:marketplace` (под админом) —
   ключи хранятся в SQLite и подтягиваются автоматически при каждом запросе
   статистики.
3. Замените заглушки в `backend/src/marketplaces/wildberries.ts` и
   `backend/src/marketplaces/ozon.ts` (места помечены `TODO`) на реальные
   вызовы:
   - WB Statistics API: `https://statistics-api.wildberries.ru/...`
   - WB Advert API: `https://advert-api.wildberries.ru/...`
   - Ozon Seller API: `https://api-seller.ozon.ru/...`
   - Ozon Performance API: `https://performance.ozon.ru/...`
   Приведите ответ к форме `MarketplaceStats` (см. `backend/src/marketplaces/types.ts`)
   — остальной код (роуты, мобильное приложение) менять не нужно.

Пока ключи не заданы, `/stats` отдаёт демо-данные, чтобы приложением можно
было пользоваться и показывать команде уже сейчас — на дашборде такие блоки
помечены бейджем «демо-данные».

## Mobile (Expo)

```bash
cd mobile
npm install
npx expo start
```

По умолчанию приложение обращается к `http://localhost:4000`. Если вы
запускаете Expo Go на телефоне или в эмуляторе, `localhost` не будет
указывать на ваш компьютер — задайте адрес явно:

```bash
EXPO_PUBLIC_API_URL=http://<ваш-ip-в-локальной-сети>:4000 npx expo start
```

## Дальнейшие шаги

- Подключить реальные API Wildberries/Ozon (см. выше).
- Экран управления командой для админа (список сотрудников, приглашения).
- Экран настроек с вводом API-ключей прямо из приложения (сейчас — через
  `PUT /stats/credentials/:marketplace`).
- Пуш-уведомления о резком падении продаж или росте ДРР.
