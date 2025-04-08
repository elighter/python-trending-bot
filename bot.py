#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
from atproto import Client

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger("python-trending-bot")

# .env dosyasından değişkenleri yükle
load_dotenv()

# Konfigürasyon
BLUESKY_USERNAME = os.getenv("BLUESKY_USERNAME", "")
BLUESKY_PASSWORD = os.getenv("BLUESKY_PASSWORD", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")  # Opsiyonel
POST_INTERVAL = int(os.getenv("POST_INTERVAL", "3600"))  # Varsayılan: 1 saat
POST_COUNT = int(os.getenv("POST_COUNT", "5"))  # Kaç repo gösterilecek


def fetch_trending_python_repos(time_period="daily"):
    """
    GitHub'dan trend olan Python repolarını çeker.
    time_period: daily, weekly veya monthly olabilir
    """
    logger.info(f"Fetching {time_period} trending Python repositories...")
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # Python repolarını yıldıza göre sıralayıp en son güncellenenlerden alıyoruz
    query = "language:python sort:stars-desc"
    if time_period == "daily":
        # Son 24 saatte güncellenenler
        date_since = datetime.now().date().isoformat()
        query += f" pushed:>={date_since}"
    
    url = f"https://api.github.com/search/repositories?q={query}&per_page=10"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            repos = response.json()["items"]
            trending_repos = []
            
            for repo in repos:
                trending_repos.append({
                    "name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"]
                })
            
            logger.info(f"Found {len(trending_repos)} trending repositories")
            return trending_repos
        else:
            logger.error(f"Error fetching trending repos: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception when fetching repos: {e}")
        return []


class BlueskyBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = Client()
        self.login()
    
    def login(self):
        """Bluesky hesabına giriş yapar"""
        try:
            self.client.login(self.username, self.password)
            logger.info(f"Logged in as {self.username}")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise e
    
    def post(self, text, reply_to=None):
        """Bluesky'e post gönderir"""
        try:
            # Metnin 300 karakterden kısa olduğundan emin olalım
            if len(text) > 300:
                logger.warning(f"Post text is too long ({len(text)} chars). Truncating to 300 chars.")
                text = text[:297] + "..."
            
            response = self.client.send_post(text, reply_to=reply_to)
            logger.info(f"Post sent successfully")
            return response
        except Exception as e:
            logger.error(f"Post failed: {e}")
            return None
    
    def format_trending_repos(self, repos, max_repos=5):
        """Trend repoları formatlı bir metin haline getirir ve birden fazla post olarak döndürür"""
        if not repos:
            return ["No trending Python repositories found today."]
        
        # Birden fazla post oluşturacağız
        posts = []
        
        # Ana başlık postu
        intro_post = "🐍 Python Trending Daily 🚀\n\nToday's most popular Python repositories:"
        posts.append(intro_post)
        
        # Her repo için ayrı post
        for i, repo in enumerate(repos[:max_repos]):
            post_text = f"{i+1}. {repo['name']}\n"
            post_text += f"⭐ Stars: {repo['stars']} | 🍴 Forks: {repo['forks']}\n"
            
            if repo['description']:
                description = repo['description']
                if len(description) > 100:
                    description = description[:97] + "..."
                post_text += f"📝 {description}\n"
            
            post_text += f"🔗 {repo['url']}"
            posts.append(post_text)
        
        # Son post (hashtag'ler)
        final_post = "#PythonDev #GitHub #Trending #Python #Coding\n\n@pythontrending.bsky.social"
        posts.append(final_post)
        
        return posts


def main():
    """Ana bot fonksiyonu"""
    logger.info("Starting Python Trending Bot")
    
    if not BLUESKY_USERNAME or not BLUESKY_PASSWORD:
        logger.error("Bluesky credentials are missing. Please set BLUESKY_USERNAME and BLUESKY_PASSWORD in .env file")
        return
    
    try:
        # Bot oluştur
        bot = BlueskyBot(BLUESKY_USERNAME, BLUESKY_PASSWORD)
        
        # GitHub'dan trend Python repolarını al
        repos = fetch_trending_python_repos()
        
        if repos:
            # Post metinlerini formatla (birden fazla post)
            posts = bot.format_trending_repos(repos, max_repos=POST_COUNT)
            
            # Thread oluştur
            previous_response = None
            for i, post_text in enumerate(posts):
                if i == 0:
                    # İlk postu normal şekilde gönder
                    response = bot.post(post_text)
                    previous_response = response
                else:
                    # Sonraki postları reply olarak gönder
                    if previous_response:
                        response = bot.post(post_text, reply_to=previous_response["uri"])
                        previous_response = response
                
                # Hız limiti aşımını önlemek için kısa bir bekleme
                time.sleep(1)
            
            logger.info("Successfully posted trending Python repos thread")
        else:
            logger.warning("No trending repositories found")
    
    except Exception as e:
        logger.error(f"Bot failed with error: {e}")


if __name__ == "__main__":
    main()