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

def trim_to_last_sentence(text, max_tokens):
    """
    Обрезает текст до последнего полного предложения, чтобы уложиться в лимит токенов.
    """
    from transformers import GPT2TokenizerFast
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    
    tokens = tokenizer.tokenize(text)
    if len(tokens) <= max_tokens:
        return text

    truncated_text = tokenizer.decode(tokenizer.encode(text)[:max_tokens])
    sentences = truncated_text.split(". ")
    
    if len(sentences) > 1:
        return ". ".join(sentences[:-1]) + "."
    return sentences[0] + "."

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
        post_content = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Напишите подробный пост на тему: {topic}, учитывая последние новости:\n{recent_news}"}],
            max_tokens=150,
            temperature=0.7
        ).choices[0].message.content.strip()

        # Обрезаем текст до последнего полного предложения
        post_content_trimmed = trim_to_last_sentence(post_content, max_tokens=100)

        return {
            "title": title,
            "meta_description": meta_description,
            "post_content": post_content_trimmed
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
