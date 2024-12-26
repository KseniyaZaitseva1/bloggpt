import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")

if not openai.api_key or not currentsapi_key:
    raise ValueError("Переменные окружения OPENAI_API_KEY и CURRENTS_API_KEY должны быть установлены")

class Topic(BaseModel):
    topic: str

def get_recent_news(topic: str):
    """Получает последние новости по теме."""
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    response = requests.get(url, params=params, timeout=10)  # Установим таймаут
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    return "\n".join([article["title"] for article in news_data[:3]])

def generate_content_sync(topic: str):
    """Синхронная генерация контента."""
    recent_news = get_recent_news(topic)

    try:
        # Генерация заголовка, мета-описания и основного текста за один запрос
        prompt = (
            f"Тема: {topic}\n\n"
            f"Свежие новости:\n{recent_news}\n\n"
            f"Сгенерируйте контент для блога, включая следующие элементы:\n"
            f"1. Привлекательный заголовок.\n"
            f"2. Краткое мета-описание.\n"
            f"3. Основной текст (не более 3 параграфов).\n"
            f"Пишите логично и связно."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,  # Ограничение на длину ответа
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()

        # Разбиваем результат на части
        parts = result.split("\n", maxsplit=2)
        if len(parts) < 3:
            raise ValueError("Неполный ответ от модели")

        title = parts[0].strip()
        meta_description = parts[1].strip()
        post_content = parts[2].strip()

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")

def background_generate_content(topic: str):
    """Фоновая задача для генерации контента."""
    content = generate_content_sync(topic)
    # Сохраняем результат в лог, базу данных или отправляем по email
    print("Сгенерированный контент:", content)

@app.post("/generate-post")
async def generate_post_api(topic: Topic, background_tasks: BackgroundTasks):
    background_tasks.add_task(background_generate_content, topic.topic)
    return {"status": "Processing", "message": "Контент генерируется в фоне. Вы получите результат позже."}

@app.get("/")
async def root():
    return {"message": "Service is running"}

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
