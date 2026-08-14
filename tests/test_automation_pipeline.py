from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.automation_utils import atomic_write_json, sha256_file, validated_run_dir
from scripts.generate_ai_scenes import ImageGenerationError, generate_scenes
from scripts.materialize_phase_a import materialize
from scripts.package_automation_result import package_result
from scripts.persist_automation_result import persist
from scripts.schema_validation import SchemaValidationError, validate_instance


SOURCE_ROOT = Path(__file__).resolve().parents[1]


def image_request(slide_number: int = 1, filename: str = "scene_01.png") -> dict:
    return {
        "slide_number": slide_number,
        "prompt": "Dark premium business scene with a strong central object and ample empty space",
        "intended_visual_meaning": "A clear operational bottleneck inside a growing company",
        "composition": "Vertical 4:5 composition, central object, open upper safe zone",
        "aspect_ratio": "4:5",
        "whether_text_must_be_absent": True,
        "output_filename": filename,
        "required": True,
    }


def valid_phase_a(run_id: str = "123", source_commit: str = "a" * 40) -> dict:
    hooks = [f"Существенно разный хук номер {index}" for index in range(1, 16)]
    markdown = "# Раздел\n\n" + ("Проверенный содержательный текст. " * 8)
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "source_commit": source_commit,
        "status": "PHASE_A_COMPLETE",
        "publication_date": "2026-08-14",
        "output_folder": "2026-08-14_test-topic",
        "selected_topic": "Проверяемая тема для растущего бизнеса",
        "topic_type": "evergreen",
        "target_segment": "Собственники действующего растущего малого бизнеса с командой",
        "problem": "Ручной контроль перестал справляться с выросшим количеством операций",
        "objective": "Дать собственнику полезную модель для одного управленческого решения",
        "main_thesis": "Сначала нужно определить результат процесса, а потом автоматизировать действия",
        "angle": "Показать цену автоматизации неясного процесса через конкретное решение",
        "choice_reason": "Тема релевантна ядру аудитории, доказуема и отличается от последних публикаций",
        "alternative_topics": [
            {"topic": f"Альтернативная тема {index}", "reason_not_selected": "Уступает победителю по целевой ценности и новизне"}
            for index in range(1, 4)
        ],
        "practical_takeaway": "Зафиксировать один ожидаемый результат процесса до выбора инструмента",
        "format": "carousel",
        "hooks": {
            "all_15": hooks,
            "shortlist_5": hooks[:5],
            "finalists_3": hooks[:3],
            "winner": hooks[0],
            "winner_reason": "Он сразу обозначает конфликт и понятен нужному собственнику",
        },
        "slides": [
            {
                "slide_number": 1,
                "function": "Хук",
                "main_idea": "Остановить внимание собственника",
                "text": hooks[0],
                "reader_understanding": "Проблема относится к его бизнесу",
                "reason_to_continue": "Нужно понять, где именно возникает ошибка",
                "visual_direction": "Сильный объект и свободная зона под заголовок",
                "ai_scene_output_filename": "",
            },
            {
                "slide_number": 2,
                "function": "Вывод",
                "main_idea": "Дать одно конкретное действие",
                "text": "Сначала назовите результат процесса.",
                "reader_understanding": "Он знает следующий шаг",
                "reason_to_continue": "Это финальный слайд",
                "visual_direction": "Программная схема без AI-сцены",
                "ai_scene_output_filename": "",
            },
        ],
        "caption": "Автоматизация усиливает процесс. Поэтому сначала полезно проверить, какой результат он должен давать.",
        "sources": [
            {
                "title": "Primary source",
                "url": "https://example.com/primary",
                "publication_date": "2026-01-01",
                "accessed_date": "2026-08-14",
                "source_type": "primary",
                "claims_supported": ["Подтверждает центральное проверяемое утверждение публикации"],
                "limitations": "Тестовая структурная запись без реального контента",
            }
        ],
        "content_brief_markdown": markdown,
        "editorial_brief_markdown": markdown,
        "hook_report_markdown": markdown,
        "visual_brief_markdown": markdown,
        "research_report_markdown": markdown,
        "phase_a_quality_notes": "Критических слабых мест на структурном этапе не обнаружено",
        "image_requests": {"schema_version": "1.0", "requests": []},
    }


class AutomationTestCase(unittest.TestCase):
    def make_project(self, temporary: Path) -> Path:
        project = temporary / "project"
        (project / "automation").mkdir(parents=True)
        (project / "data").mkdir()
        (project / "output").mkdir()
        (project / "automation_state").mkdir()
        for name in (
            "image_requests.schema.json",
            "phase_a_state.schema.json",
            "phase_b_result.schema.json",
        ):
            shutil.copy2(SOURCE_ROOT / "automation" / name, project / "automation" / name)
        (project / "data" / "posts_history.csv").write_text(
            "post_id,status,publication_url,reach,impressions,likes,comments,saves,sends,profile_visits,follows,leads\n",
            encoding="utf-8",
        )
        return project

    def test_schema_rejects_additional_property(self) -> None:
        schema = json.loads((SOURCE_ROOT / "automation" / "image_requests.schema.json").read_text())
        instance = {"schema_version": "1.0", "requests": [], "unexpected": True}
        with self.assertRaises(SchemaValidationError):
            validate_instance(instance, schema)

    def test_materialize_phase_a_without_touching_history(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            project = self.make_project(Path(name))
            run_dir = project / "automation_state" / "123"
            run_dir.mkdir()
            response = run_dir / "phase_a_response.json"
            atomic_write_json(response, valid_phase_a())
            history = project / "data" / "posts_history.csv"
            baseline = sha256_file(history)
            materialize(response, run_dir, "123", "a" * 40, baseline, project)
            self.assertTrue((run_dir / ".phase_a_complete").is_file())
            self.assertEqual(sha256_file(history), baseline)

    def test_run_directory_cannot_escape_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            project = Path(name)
            (project / "automation_state").mkdir()
            with self.assertRaises(ValueError):
                validated_run_dir(project / "outside" / "123", "123", project)

    def test_image_adapter_generates_valid_png_and_reuses_it(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            project = self.make_project(Path(name))
            run_dir = project / "automation_state" / "456"
            run_dir.mkdir()
            (run_dir / ".phase_a_complete").write_text("PHASE_A_COMPLETE\n")
            atomic_write_json(
                run_dir / "image_requests.json",
                {"schema_version": "1.0", "requests": [image_request()]},
            )
            generated = Image.new("RGB", (1024, 1280), (18, 20, 22))
            buffer = io.BytesIO()
            generated.save(buffer, "PNG")
            calls: list[dict] = []

            def fake_transport(api_key: str, payload: dict) -> bytes:
                self.assertEqual(api_key, "test-only-key")
                self.assertEqual(payload["model"], "gpt-image-2")
                self.assertEqual(payload["quality"], "medium")
                calls.append(payload)
                return buffer.getvalue()

            first = generate_scenes(
                run_dir,
                "456",
                "test-only-key",
                transport=fake_transport,
                project_root=project,
            )
            second = generate_scenes(
                run_dir,
                "456",
                "test-only-key",
                transport=fake_transport,
                project_root=project,
            )
            self.assertEqual(first["api_calls"], 1)
            self.assertEqual(second["api_calls"], 0)
            self.assertEqual(second["reused_count"], 1)
            self.assertEqual(len(calls), 1)
            with Image.open(run_dir / "scenes" / "scene_01.png") as image:
                self.assertEqual(image.size, (1024, 1280))

    def test_missing_key_fails_with_required_message(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            project = self.make_project(Path(name))
            run_dir = project / "automation_state" / "789"
            with self.assertRaisesRegex(ImageGenerationError, "OPENAI_API_KEY secret is required"):
                generate_scenes(run_dir, "789", "", project_root=project)

    def test_image_failure_does_not_create_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            project = self.make_project(Path(name))
            run_dir = project / "automation_state" / "790"
            run_dir.mkdir()
            (run_dir / ".phase_a_complete").write_text("PHASE_A_COMPLETE\n")
            atomic_write_json(
                run_dir / "image_requests.json",
                {"schema_version": "1.0", "requests": [image_request()]},
            )

            def failing_transport(_api_key: str, _payload: dict) -> bytes:
                raise ImageGenerationError("simulated Image API failure")

            with self.assertRaisesRegex(ImageGenerationError, "simulated Image API failure"):
                generate_scenes(
                    run_dir,
                    "790",
                    "test-only-key",
                    transport=failing_transport,
                    project_root=project,
                )
            self.assertFalse((run_dir / ".images_complete").exists())

    def test_persist_refuses_history_race(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            repository = root / "repository"
            artifact = root / "artifact"
            payload = artifact / "repository_payload"
            (repository / "data").mkdir(parents=True)
            (repository / "output").mkdir()
            (payload / "data").mkdir(parents=True)
            publication = payload / "output" / "2026-08-14_test-topic"
            publication.mkdir(parents=True)
            (publication / "caption.txt").write_text("caption", encoding="utf-8")
            current_history = repository / "data" / "posts_history.csv"
            current_history.write_text("changed\n", encoding="utf-8")
            (payload / "data" / "posts_history.csv").write_text("new\n", encoding="utf-8")
            files = []
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    files.append(
                        {
                            "path": path.relative_to(payload).as_posix(),
                            "bytes": path.stat().st_size,
                            "sha256": sha256_file(path),
                        }
                    )
            atomic_write_json(
                artifact / "AUTOMATION_ARTIFACT_MANIFEST.json",
                {
                    "schema_version": "1.0",
                    "run_id": "1",
                    "source_commit": "a" * 40,
                    "base_posts_history_sha256": "0" * 64,
                    "output_folder": "2026-08-14_test-topic",
                    "files": files,
                },
            )
            with self.assertRaisesRegex(ValueError, "changed since the run started"):
                persist(artifact, repository)
            self.assertFalse((repository / "output" / "2026-08-14_test-topic").exists())

    def test_package_and_persist_completed_payload(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            project = self.make_project(root)
            history = project / "data" / "posts_history.csv"
            base_sha = sha256_file(history)
            folder = "2026-08-14_test-topic"
            publication = project / "output" / folder
            publication.mkdir()
            (publication / "caption.txt").write_text("Готовое описание", encoding="utf-8")
            run_dir = project / "automation_state" / "100"
            run_dir.mkdir()
            (run_dir / ".run_complete").write_text("RUN_COMPLETE\n", encoding="utf-8")
            atomic_write_json(run_dir / "phase_a_state.json", {"output_folder": folder})
            atomic_write_json(
                run_dir / "run_metadata.json",
                {
                    "source_commit": "a" * 40,
                    "base_posts_history_sha256": base_sha,
                },
            )
            atomic_write_json(run_dir / "image_results.json", {"status": "IMAGES_COMPLETE"})
            atomic_write_json(run_dir / "phase_b_response.json", {"status": "PHASE_B_COMPLETE"})
            artifact = package_result(run_dir, "100", project)

            repository = root / "destination"
            (repository / "data").mkdir(parents=True)
            (repository / "output").mkdir()
            shutil.copy2(history, repository / "data" / "posts_history.csv")
            destination = persist(artifact, repository)
            self.assertEqual(destination.name, folder)
            self.assertEqual(
                (destination / "caption.txt").read_text(encoding="utf-8"),
                "Готовое описание",
            )

    def test_workflow_has_manual_safe_contract(self) -> None:
        workflow = (SOURCE_ROOT / ".github" / "workflows" / "content-agent-manual.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("cron:", workflow)
        self.assertEqual(workflow.count("uses: openai/codex-action@v1"), 2)
        self.assertIn("default: false", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("OPENAI_API_KEY secret is required", workflow)
        self.assertEqual(workflow.count("contents: write"), 1)
        self.assertNotRegex(workflow, r"sk-[A-Za-z0-9_-]{20,}")


if __name__ == "__main__":
    unittest.main()
