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
        "language": "ru",  # Используем русский язык для новостей
        "keywords": topic,
        "apiKey": currentsapi_key
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    # Возвращаем только 3 самые актуальные новости
    return "\n".join([article["title"] + ": " + article["description"] for article in news_data[:3]])

def generate_content(topic: str):
    recent_news = get_recent_news(topic)

    try:
        # Генерация заголовка
        title = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Используем модель gpt-4o-mini
            messages=[{
                "role": "user", 
                "content": f"Создайте заголовок для статьи на тему '{topic}' с учетом последних новостей:\n{recent_news}. Заголовок должен быть привлекательным и соответствовать теме."
            }],
            max_tokens=50,
            temperature=0.7,
            stop=["\n"]
        ).choices[0].message.content.strip()

        # Генерация мета-описания
        meta_description = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Используем модель gpt-4o-mini
            messages=[{
                "role": "user", 
                "content": f"Напишите мета-описание для статьи с заголовком '{title}'. Мета-описание должно быть информативным и отражать суть темы с учетом свежих новостей:\n{recent_news}."
            }],
            max_tokens=150,
            temperature=0.7,
            stop=["."]
        ).choices[0].message.content.strip()

        # Генерация контента поста
        post_content = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Используем модель gpt-4o-mini
            messages=[{
                "role": "user", 
                "content": f"Напишите подробный и содержательный пост на тему '{topic}', используя следующие последние новости:\n{recent_news}. Текст должен быть логичным, интересным и завершённым, объёмом не менее 1000 символов."
            }],
            max_tokens=1200,  # Увеличено количество токенов для генерации длинного контента
            temperature=0.7,
            stop=["\n"]
        ).choices[0].message.content.strip()

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content
        }
    
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
