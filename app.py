import os
from fastapi import FastAPI, HTTPException
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
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    return "\n".join([article["title"] for article in news_data[:3]])

def generate_paragraph(topic: str, recent_news: str, previous_content: str = "", max_tokens: int = 150):
    """Генерация параграфа с учетом контекста."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Напишите параграф для поста на тему: {topic}. "
                    f"Вот последние новости: {recent_news}. "
                    f"Предыдущий текст: {previous_content if previous_content else 'Отсутствует.'} "
                    "Пишите полный и связный текст, завершая мысли."
                )
            }
        ],
        max_tokens=max_tokens,
        temperature=0.7,
        stop=["\n\n"]
    )
    return response.choices[0].message.content.strip()

def generate_content(topic: str):
    recent_news = get_recent_news(topic)

    try:
        # Генерация заголовка
        title = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Придумайте привлекательный заголовок для поста на тему: {topic}"}],
            max_tokens=50,
            temperature=0.7
        ).choices[0].message.content.strip()

        # Генерация мета-описания
        meta_description = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Напишите краткое мета-описание для поста с заголовком: {title}"}],
            max_tokens=60,
            temperature=0.7
        ).choices[0].message.content.strip()

        # Генерация основного текста
        post_content = ""
        for _ in range(5):  # Генерация до 5 параграфов
            paragraph = generate_paragraph(topic, recent_news, previous_content=post_content)
            if not paragraph:
                break
            post_content += "\n\n" + paragraph

        return {"title": title, "meta_description": meta_description, "post_content": post_content.strip()}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента: {str(e)}")

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    return generate_content(topic.topic)

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
