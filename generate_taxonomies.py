#!/usr/bin/env python3
import argparse
import json
import logging
import os
import shutil
import sys
import urllib.error
import urllib.request
import frontmatter

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:latest"
CONTENT_DIR = "content/news"
BACKUP_DIR = "backups"
LOG_FILE = "taxonomy_generation.log"
MAX_BODY_CHARS = 4000

# Canonical default categories to seed consistency
DEFAULT_CATEGORIES = [
    "Политика", "Общество", "Происшествия", "Экономика", "Бизнес",
    "Образование", "Здравоохранение", "Спорт", "Культура", "Технологии",
    "Наука", "Транспорт", "ЖКХ", "Туризм", "Погода"
]

GENERIC_TAGS_BLACKLIST = {"новости", "новость", "события", "информация", "статья", "публикация"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)

def create_backup(file_path: str):
    rel_path = os.path.relpath(file_path)
    backup_path = os.path.join(BACKUP_DIR, rel_path)
    if os.path.exists(backup_path):
        return  # Keep original initial backup
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(file_path, backup_path)

def build_prompt(title: str, content: str, known_cats: set, known_tags: set) -> str:
    categories_str = ", ".join(sorted(known_cats))
    tags_str = ", ".join(sorted(known_tags)[:100])  # limit prompt size if tags grow large

    return f"""Ты — классификатор новостных статей на русском языке для сайта Hugo.
Проанализируй заголовок и текст статьи и выбери 1 категорию и от 3 до 7 тегов.

ПРАВИЛА КАТЕГОРИЙ:
- Выбери СТРОГО 1 категорию.
- Категория должна быть широкой и обобщенной.
- Доступные категории: [{categories_str}].
- Отдавай БЕЗОГОВОРЧНОЕ преимущество категориям из списка выше, если статья подходит под них. Создавай новую только если статья абсолютно не подходит.

ПРАВИЛА ТЕГОВ:
- Верни от 3 до 7 конкретных тегов (существительные в именительном падеже или устойчивые словосочетания).
- Исполнение названий: используй каноничные формы (например, "Грозный" вместо "г. Грозный", "Чечня" вместо "Чеченская Республика").
- Ранее использованные теги: [{tags_str}]. Переиспользуй их, если они подходят.
- Запрещено использовать бессмысленные общие теги: новости, событие, информация.

Формат ответа: СТРОГО JSON без Markdown, без флагов ```json, без пояснений.

Пример ответа:
{{
  "category": "Общество",
  "tags": ["Грозный", "Чечня", "строительство", "инфраструктура"]
}}

ЗАГОЛОВОК: {title}
ТЕКСТ СТАТЬИ:
{content}
"""

def query_ollama(prompt: str) -> dict:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1}
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return json.loads(res.get("response", "{}"))

def validate_response(data: dict) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Response is not a JSON object"
    cat = data.get("category")
    tags = data.get("tags")

    if not cat or not isinstance(cat, str) or not cat.strip():
        return False, "Invalid or missing 'category'"
    if not isinstance(tags, list) or not (3 <= len(tags) <= 7):
        return False, f"'tags' must be a list of 3 to 7 items (got {len(tags) if isinstance(tags, list) else 'none'})"
    
    cleaned_tags = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    if len(set(cleaned_tags)) != len(cleaned_tags):
        return False, "Duplicate tags present"
    if any(t.lower() in GENERIC_TAGS_BLACKLIST for t in cleaned_tags):
        return False, "Contains blacklisted generic tag"

    return True, ""

def find_posts(root_dir: str) -> list[str]:
    posts = []
    for root, _, files in os.walk(root_dir):
        if "index.md" in files:
            posts.append(os.path.join(root, "index.md"))
    return sorted(posts)

def main():
    parser = argparse.ArgumentParser(description="Generate categories and tags for Hugo posts via Ollama.")
    parser.add_argument("--dry-run", action="store_true", help="Run without modifying files or making backups")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of posts to process (0 = all)")
    args = parser.parse_args()

    posts = find_posts(CONTENT_DIR)
    if args.limit > 0:
        posts = posts[:args.limit]

    total = len(posts)
    print(f"Found {total} posts to process.\n")

    known_categories = set(DEFAULT_CATEGORIES)
    known_tags = set()

    processed = updated = skipped = errors = 0

    for idx, path in enumerate(posts, 1):
        print(f"[{idx}/{total}] {path}")
        try:
            post = frontmatter.load(path)
            title = post.get("title", "")
            body = post.content[:MAX_BODY_CHARS]

            if not body.strip() and not title:
                print("  ✗ Skipped — empty post content")
                skipped += 1
                continue

            prompt = build_prompt(title, body, known_categories, known_tags)
            llm_res = query_ollama(prompt)

            valid, err_msg = validate_response(llm_res)
            if not valid:
                print(f"  ✗ LLM error — {err_msg}")
                logging.error(f"Validation failed for {path}: {err_msg}. Raw response: {llm_res}")
                errors += 1
                continue

            category = llm_res["category"].strip()
            tags = [t.strip() for t in llm_res["tags"]]

            print(f"  Category: {category}")
            print(f"  Tags:     {', '.join(tags)}")

            if args.dry_run:
                print("  ✓ Dry run — file not modified\n")
            else:
                create_backup(path)
                post["categories"] = [category]
                post["tags"] = tags

                with open(path, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(post))
                print("  ✓ Updated\n")

            known_categories.add(category)
            known_tags.update(tags)
            processed += 1
            updated += 1

        except Exception as e:
            print(f"  ✗ Error — {e}\n")
            logging.exception(f"Unhandled error processing {path}")
            errors += 1

    print("-" * 32)
    print("Processing complete\n")
    print(f"Total posts:      {total}")
    print(f"Processed:        {processed}")
    print(f"Updated:          {updated}")
    print(f"Skipped:          {skipped}")
    print(f"Errors:           {errors}")
    print("-" * 32)

if __name__ == "__main__":
    main()