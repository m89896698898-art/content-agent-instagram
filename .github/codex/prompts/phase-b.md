# PHASE B — FINAL ASSEMBLY AND QA

Продолжи уже подготовленную публикацию. Не начинай новый тематический или исследовательский цикл.

## Обязательные входы

1. Прочитай `AGENTS.md`, `knowledge/`, профильные `skills/` и текущую историю, чтобы применить все финальные проверки.
2. Прочитай внутри переданного run directory:
   - `phase_a_state.json`;
   - `image_requests.json`;
   - `image_results.json`;
   - `scenes/`;
   - все подготовленные briefs и research report.
3. Считай содержание PHASE A утверждённым промежуточным состоянием. Не меняй тему и центральный тезис без критической причины. При критическом дефекте заверши фазу ошибкой, а не подменяй публикацию другой.

## Сборка

1. Создай run-specific renderer только внутри run directory и используй существующие `scripts/render_utils.py`, Pillow и встроенные шрифты.
2. AI-сцены используй только как исходный визуальный слой. Всю критически важную русскую типографику, цифры и подписи накладывай программно.
3. Собирай публикацию только в `automation_state/<run_id>/staged_output/<output_folder>/`.
4. Финальные слайды: последовательные `01.jpg`, `02.jpg`, …; каждый строго 1080×1350 px, RGB JPEG.
5. Сохрани в staged publication:
   - финальные JPG;
   - `caption.txt`;
   - `sources.md`;
   - `content_brief.md`;
   - `quality_report.md`;
   - `editorial_brief.md`;
   - `hook_report.md`;
   - `visual_brief.md`;
   - `research_report.md`;
   - `contact_sheet.jpg`;
   - `preview_safe_sheet.jpg`.
6. Выполни FINAL RENDER GATE, POST-RENDER INSPECTION и PREVIEW-SAFE TEST. Открой каждый финальный JPG и проверь кириллицу, safe zones, контраст, порядок чтения, мобильную читаемость и соответствие смысловой карте.
7. Повтори anti-repeat gate перед финалом.

## История и атомарность

- Не изменяй рабочий `data/posts_history.csv`.
- Только после успешного полного QA создай его копию в `automation_state/<run_id>/staged_data/posts_history.csv` и добавь ровно одну строку созданной тестовой публикации.
- Не меняй существующие строки и заголовок CSV.
- `publication_url` и все Instagram-метрики оставь пустыми.
- Статус новой строки — `ready_for_review_not_published`.
- Если любой обязательный check не пройден, не создавай успешный ответ PHASE B.

## Запреты

- Не выполняй новый web research и не вызывай Image API.
- Не генерируй дополнительные AI-сцены.
- Не публикуй, не подключай Instagram/Meta и не отправляй материалы наружу.
- Не выполняй Git-операции.
- Не записывай готовый результат напрямую в обычный `output/`: promotion выполнит доверенный технический шаг только после валидации.

Верни только один JSON-объект, строго соответствующий `automation/phase_b_result.schema.json`. Не добавляй Markdown-ограждения и пояснения вне JSON. Динамические `run_id` и run directory передаются в запускающем prompt.
