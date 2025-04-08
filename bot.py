#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python Trending Bot - GitHub'daki trend olan Python repolarını
Bluesky'de bir thread olarak paylaşan bot.
"""

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
            
            # Ayrıca hızlı büyüyen repoları belirlemek için ek bir sorgu yapalım
            fast_growing_query = "language:python sort:stars created:>30"  # Son 30 günde oluşturulan
            fast_growing_url = f"https://api.github.com/search/repositories?q={fast_growing_query}&per_page=15"
            
            try:
                fast_growing_response = requests.get(fast_growing_url, headers=headers)
                if fast_growing_response.status_code == 200:
                    fast_growing_repos = fast_growing_response.json()["items"]
                    fast_growing_ids = [repo["id"] for repo in fast_growing_repos[:10]]  # En hızlı büyüyen 10 repo
                else:
                    logger.warning(f"Could not fetch fast growing repos: {fast_growing_response.status_code}")
                    fast_growing_ids = []
            except Exception as e:
                logger.warning(f"Error fetching fast growing repos: {e}")
                fast_growing_ids = []
            
            for repo in repos:
                is_fast_growing = repo["id"] in fast_growing_ids
                trending_repos.append({
                    "name": repo["full_name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "created_at": repo["created_at"],
                    "is_fast_growing": is_fast_growing
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
        """Bluesky bot sınıfını başlatır"""
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
    
    def post(self, text, reply_info=None):
        """
        Bluesky'e post gönderir
        
        Args:
            text (str): Gönderilecek metin
            reply_info (dict, optional): Yanıt verilecek post'un bilgileri. 
                                        {"root_uri", "root_cid", "parent_uri", "parent_cid"}
        
        Returns:
            dict: Post response veya None (hata durumunda)
        """
        try:
            # Metnin 300 karakterden kısa olduğundan emin olalım
            if len(text) > 300:
                logger.warning(f"Post text is too long ({len(text)} chars). Truncating to 300 chars.")
                text = text[:297] + "..."
            
            # Reply_info varsa, doğru formatta olduğundan emin olalım
            if reply_info and isinstance(reply_info, dict):
                logger.info(f"Sending post as reply. Root: {reply_info['root_uri'][:30]}..., Parent: {reply_info['parent_uri'][:30]}...")
                
                # atproto kütüphanesi için reply formatı:
                # https://atproto.com/lexicons/app-bsky-feed#appbskyfeedpost
                response = self.client.send_post(
                    text, 
                    reply_to={
                        'root': {
                            'uri': reply_info['root_uri'],
                            'cid': reply_info['root_cid']
                        },
                        'parent': {
                            'uri': reply_info['parent_uri'],
                            'cid': reply_info['parent_cid']
                        }
                    }
                )
            else:
                logger.info("Sending post without reply")
                response = self.client.send_post(text)
                
            logger.info(f"Post sent successfully: {text[:30]}...")
            return response
        except Exception as e:
            logger.error(f"Post failed: {e}")
            return None
    
    def format_trending_repos(self, repos, max_repos=5):
        """
        Trend repoları formatlı bir metin haline getirir ve birden fazla post olarak döndürür
        
        Args:
            repos (list): Repo listesi
            max_repos (int, optional): Gösterilecek maksimum repo sayısı. Defaults to 5.
            
        Returns:
            list: Post metinleri listesi
        """
        if not repos:
            return ["No trending Python repositories found today."]
        
        # Birden fazla post oluşturacağız
        posts = []
        
        # Ana başlık postu
        intro_post = "🐍 Python Trending Daily 🚀\n\nToday's most popular Python repositories:"
        posts.append(intro_post)
        
        # Her repo için ayrı post
        for i, repo in enumerate(repos[:max_repos]):
            # Eğer repo hızlı büyüyorsa, özel bir işaret ekleyelim
            growth_indicator = "🚀 FAST GROWING! " if repo.get("is_fast_growing", False) else ""
            
            post_text = f"{i+1}. {repo['name']}\n"
            post_text += f"⭐ Stars: {repo['stars']} | 🍴 Forks: {repo['forks']}\n"
            
            # Repo yaşını hesaplayalım (opsiyonel)
            if "created_at" in repo:
                try:
                    created_date = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                    days_old = (datetime.now() - created_date).days
                    age_text = f"📅 Age: {days_old} days | "
                except:
                    age_text = ""
            else:
                age_text = ""
            
            # Hızlı büyüyen repo işaretini ekleyelim
            if growth_indicator:
                post_text += f"{growth_indicator}{age_text}\n"
            
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
            root_uri = None
            root_cid = None
            parent_uri = None
            parent_cid = None
            
            for i, post_text in enumerate(posts):
                logger.info(f"Sending post #{i+1}: {post_text[:30]}...")
                
                if i == 0:
                    # İlk postu normal şekilde gönder
                    response = bot.post(post_text)
                    if response:
                        root_uri = response['uri']
                        root_cid = response['cid']
                        parent_uri = response['uri']
                        parent_cid = response['cid']
                        logger.info(f"Sent initial post. URI: {root_uri}")
                    else:
                        logger.error("Failed to send initial post")
                        break
                else:
                    # Sonraki postları reply olarak gönder
                    if root_uri and root_cid:
                        reply_info = {
                            "root_uri": root_uri,
                            "root_cid": root_cid,
                            "parent_uri": parent_uri,
                            "parent_cid": parent_cid
                        }
                        
                        response = bot.post(post_text, reply_info)
                        
                        if response:
                            # Bir sonraki post için parent değerlerini güncelle
                            parent_uri = response['uri']
                            parent_cid = response['cid']
                            logger.info(f"Sent reply post #{i+1}")
                        else:
                            logger.error(f"Failed to send post #{i+1}")
                            break
                    else:
                        logger.error("Root post information missing, can't reply")
                        break
                
                # Hız limiti aşımını önlemek için kısa bir bekleme
                time.sleep(2)
            
            logger.info("Successfully posted trending Python repos thread")
        else:
            logger.warning("No trending repositories found")
    
    except Exception as e:
        logger.error(f"Bot failed with error: {e}")


if __name__ == "__main__":
    main()