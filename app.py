import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")  # Изменено на ключ CurrentsAPI

if not openai.api_key or not currentsapi_key:
    raise ValueError("Переменные окружения OPENAI_API_KEY и CURRENTS_API_KEY должны быть установлены")

class Topic(BaseModel):
    topic: str

def get_recent_news(topic: str):
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": currentsapi_key  # Используем ключ CurrentsAPI
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    return "\n".join([article["title"] for article in news_data[:3]])

def generate_content(topic: str):
    recent_news = get_recent_news(topic)

    try:
        # Генерация заголовка
        title = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Придумайте привлекательный заголовок для поста на тему: {topic}"}],
            max_tokens=50,
            temperature=0.7
        ).choices[0].message.content.strip()

        # Генерация мета-описания
        meta_description = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Напишите краткое мета-описание для поста с заголовком: {title}"}],
            max_tokens=60,
            temperature=0.7
        ).choices[0].message.content.strip()

        # Генерация контента поста
        post_content = ""
        remaining_tokens = 100  # Ограничение на 100 токенов за раз
        
        # Итерация, чтобы гарантировать завершенность предложений
        while remaining_tokens > 0:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user", 
                    "content": f"Напишите продолжение поста на тему: {topic}, учитывая последние новости:\n{recent_news}\nПродолжите, чтобы завершить мысль."
                }],
                max_tokens=remaining_tokens,
                temperature=0.7,
                stop=[".", "!", "?"]  # Ожидаем завершения предложений
            )
            new_content = response.choices[0].message.content.strip()
            post_content += " " + new_content

            # Пересчитываем оставшиеся токены (максимум 100 токенов для каждого шага)
            remaining_tokens -= len(new_content.split())
            if len(new_content.split()) == 0:
                break  # Завершаем, если нет нового контента

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
