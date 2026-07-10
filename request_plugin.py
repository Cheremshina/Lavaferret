import requests
import json

# Базовый URL API и заголовки
BASE_URL = "https://api.modrinth.com"
HEADERS = {
    "User-Agent": "MyModrinthApp (your@email.com)"  # Замените на свои данные
}


def search_projects(query, project_type=None):

    params = {
        "query": query,
        "limit": 10  # Максимальное количество результатов
    }

    # Добавляем фильтр по типу проекта, если он указан
    if project_type:
        params["facets"] = json.dumps([[f"project_type:{project_type}"]])  # <-- Основной фильтр

    response = requests.get(f"{BASE_URL}/v2/search", params=params, headers=HEADERS)
    response.raise_for_status()  # Проверяем, не возникла ли ошибка

    return response.json()


# --- Примеры использования ---

m = input("Введите название мода: ")
p = input("Введите название плагина: ")

print(f"--- Поиск модов {m} ---")
mods = search_projects(query=m, project_type="mod")
for hit in mods.get('hits', []):
    print(f"- {hit['title']} (Slug: {hit['slug']}) {hit['icon_url']} {hit['description']}")

# 2. Поиск плагинов по названию "essentials"
print(f"\n--- Поиск плагинов {p} ---")
plugins = search_projects(query=p, project_type="plugin")
for hit in plugins.get('hits', []):
    print(f"- {hit['title']} (Slug: {hit['slug']})")