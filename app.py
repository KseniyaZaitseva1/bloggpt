import openai
import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Получаем ключи API
openai.api_key = os.getenv("OPENAI_API_KEY")
currentsapi_key = os.getenv("CURRENTS_API_KEY")

# Создаем FastAPI приложение
app = FastAPI()

# Модель запроса с темой (topic)
class TopicRequest(BaseModel):
    topic: str

# Функция для получения актуальных новостей по теме
def get_current_news(topic):
    url = f"https://api.currentsapi.services/v1/search"
    params = {
        "apiKey": currentsapi_key,
        "keywords": topic,
        "language": "ru",
        "pageSize": 5  # Количество новостей
    }
    response = requests.get(url, params=params)
    news_data = response.json()
    
    # Проверим, есть ли новости, если нет, возвращаем пустой список
    if news_data.get("status") == "ok" and news_data.get("news"):
        return news_data["news"]
    return []

# Функция для генерации контента с использованием OpenAI
def generate_post(topic, news):
    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}. Используйте актуальные новости: {news}"
    response_title = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_title}],
        max_tokens=50,
        temperature=0.7,
    )
    title = response_title.choices[0].message.content.strip()

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое мета-описание для поста с заголовком: {title}. Используйте новости: {news}"
    response_meta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_meta}],
        max_tokens=100,
        temperature=0.7,
    )
    meta_description = response_meta.choices[0].message.content.strip()

    # Генерация самого поста
    prompt_post = f"Напишите подробный и увлекательный пост для блога на тему: {topic}. Включите актуальные новости: {news}. Используйте SEO-оптимизацию."
    response_post = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt_post}],
        max_tokens=2048,
        temperature=0.7,
    )
    post_content = response_post.choices[0].message.content.strip()

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }

# Эндпоинт для генерации поста
@app.post("/generate_post/")
async def generate_content(request: TopicRequest):
    topic = request.topic
    news = get_current_news(topic)  # Получаем актуальные новости по теме
    news_headlines = ", ".join([news_item["title"] for news_item in news]) if news else "Нет актуальных новостей"

    content = generate_post(topic, news_headlines)
    
    return content

# Запуск приложения
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
