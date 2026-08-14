# CONTENT AGENT: GitHub Actions automation V1

## Статус

Это подготовленный технический слой для будущего автономного запуска. Workflow запускается только вручную через `workflow_dispatch`; расписания и публикации в Instagram нет. По умолчанию `persist_result=false`, поэтому успешный результат остаётся GitHub Actions Artifact и не записывается в `main`.

## Архитектура

`PHASE A → Image API → PHASE B → Artifact → optional PERSIST RESULT`

### PHASE A

Официальный `openai/codex-action@v1` читает существующие `AGENTS.md`, `knowledge/`, `skills/`, `data/` и `output/`, выполняет текущий research/fact-check, anti-repeat, редакционный конвейер и создаёт строгое промежуточное состояние. Результат валидируется по `automation/phase_a_state.schema.json`. На этой фазе рабочий `posts_history.csv` не изменяется.

Raw-ответ Codex передаётся в отдельный job с новым checkout: materialize и validation выполняются неизменённым доверенным кодом из repository, а не файлами, которые могла изменить агентная фаза.

Каждый запуск изолирован в `automation_state/<github_run_id>/`. Эти каталоги временные и исключены из Git.

### OpenAI Image API

`scripts/generate_ai_scenes.py` читает строгий `image_requests.json` и вызывает фиксированный endpoint генерации изображений с моделью `gpt-image-2`. Параметры по умолчанию:

- качество `medium`;
- размер исходной вертикальной сцены `1024x1280` (4:5);
- максимум 4 AI-сцены на карусель;
- одна сцена на один обязательный запрос;
- PNG без финальной типографики.

Адаптер принимает только безопасные имена `scene_NN.png`, не принимает произвольный URL, проверяет каждый файл через Pillow, сохраняет SHA-256 manifest и повторно использует уже подтверждённую сцену внутри того же run. При отсутствии любой обязательной сцены job завершается ошибкой.

### PHASE B

Второй `openai/codex-action@v1` получает только подтверждённое состояние и сцены. Он использует существующие Pillow-примитивы и встроенные кириллические шрифты, собирает результат в staging, выполняет FINAL RENDER GATE, POST-RENDER INSPECTION и PREVIEW-SAFE TEST. Финальные слайды должны быть RGB JPEG 1080×1350.

После PHASE B raw staging проверяет отдельный job с чистым checkout и без API key. Только этот доверенный job может поместить результат в финальный Artifact.

Рабочий `posts_history.csv` не меняется во время агентной фазы. Сначала создаётся staged-копия с одной новой строкой без URL и Instagram-метрик. Доверенный валидатор проверяет весь комплект и только затем переносит его в ephemeral checkout для Artifact.

## GitHub Secret

Перед первым реальным запуском в private repository потребуется Actions secret с точным именем:

`OPENAI_API_KEY`

Ключ не хранится в repository, JSON, Markdown, output или Artifact. Он передаётся только как input двух шагов `openai/codex-action@v1`, через безопасную архитектуру Action, и как step-level environment для ограниченного Image API adapter. Job-level и global environment для ключа не используются. Preflight без ключа завершается сообщением `OPENAI_API_KEY secret is required`.

## Ручной запуск

Workflow: `.github/workflows/content-agent-manual.yml`.

Параметры:

- `persist_result` — по умолчанию `false`;
- `image_quality` — `low`, `medium` или `high`, по умолчанию `medium`;
- `max_ai_scenes` — 1–4, по умолчанию 4.

Первый тест следует запускать с `persist_result=false`. Workflow из технической ветки не разрешает persist в `main`; запись становится доступна только после отдельного решения о переносе workflow в `main`.

## Artifact

При успешной сборке Artifact содержит:

- папку готовой публикации с финальными JPG;
- `contact_sheet.jpg` и `preview_safe_sheet.jpg`;
- caption, sources, content/editorial/visual briefs, hook/research/quality reports;
- обновлённый `posts_history.csv` как repository payload;
- технические manifests с SHA-256.

Сырые credentials, secret, cache и временные файлы не включаются.

## Persist

Отдельный job имеет `contents: write`, но не получает `OPENAI_API_KEY`. Он запускается только после полного успеха всех предыдущих jobs, только при `persist_result=true` и только для workflow, запущенного из `main`. Перед копированием проверяются SHA-256 и отсутствие изменений исходной истории; затем создаётся один автоматический commit и push в `main`.

## Ошибки и конкурентность

Любая критическая ошибка research/Codex/Image API/сцены/рендера/JPG/QA завершает workflow как `FAILED`. Частичный результат не помечается готовым, не загружается как финальный Artifact и не сохраняется в `main`. `concurrency` не позволяет двум CONTENT AGENT run выполняться одновременно.

## Расходы API

Расходы возникают только во время будущего реального запуска:

1. PHASE A через Codex Action;
2. каждый фактически выполненный Image API call;
3. PHASE B через Codex Action.

Качество и число AI-сцен ограничиваются входными параметрами. Программные слайды не требуют Image API.

## Будущее расписание и rollback

Cron/schedule намеренно отсутствует. Его можно обсуждать только после успешного ручного dry-run. Для rollback технической автоматизации удалить или откатить её отдельный commit/branch; стабильные `main` commit `3d0730ccae4b28ee7dbc18209afe792886436c4c` и tag `content-agent-v1-cloud-ready` этим этапом не меняются.

Официальные основы: [Codex GitHub Action](https://learn.chatgpt.com/docs/github-action), [OpenAI Image generation](https://developers.openai.com/api/docs/guides/image-generation), [GPT Image 2](https://developers.openai.com/api/docs/models/gpt-image-2).
