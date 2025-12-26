import feedparser
import requests
import os
import time
import json
import html

# 配置
TOKEN = os.environ.get('TG_TOKEN')
CHAT_ID = os.environ.get('TG_CHAT_ID')
DB_FILE = "sent_links.txt"
CONFIG_FILE = "feeds.json"
MAX_HISTORY = 1000  # 数据库文件保留的最大条数

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"读取配置失败: {e}")
        return {"feeds": []}

def load_sent_links():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_sent_links(links):
    # 只保留最近的 MAX_HISTORY 条记录
    to_save = links[-MAX_HISTORY:]
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for link in to_save:
            f.write(link + "\n")

def should_filter(title, feed_config, global_exclude):
    title = title.lower()
    # 1. 全局排除词过滤
    if any(word.lower() in title for word in global_exclude):
        return True
    
    # 2. 局部排除词过滤
    exclude = feed_config.get("exclude_keywords", [])
    if any(word.lower() in title for word in exclude):
        return True
    
    # 3. 包含词过滤（如果配置了，则必须包含其中之一）
    #include = feed_config.get("include_keywords", [])
    #if include and not any(word.lower() in title for word in include):
    #    return True
    
    #return False

def send_tg_message(entry, feed_config):
    # 基础信息提取与安全转义（防止标题中含有 < > & 导致发送失败）
    category = feed_config.get("category", "TECH").upper()
    tags = " ".join(feed_config.get("tags", []))
    title = html.escape(entry.title)
    
    # 构造精美排版
    # 🚀 头部：类别
    # ━━━━ 分隔线：视觉分割
    # 📌 标题：加粗显示
    # 🔗 链接：隐藏长网址，文字超链接
    text = (
        f"🚀 <b>{category}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{title}</b>\n\n"
        f"🔗 <a href='{entry.link}'>查看详情</a>\n\n"
        f"🏷️ {tags}"
    )
    
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False  # 设为 True 可以关掉大图预览
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=20)
        if response.status_code == 429:
            retry_after = response.json().get('parameters', {}).get('retry_after', 10)
            time.sleep(retry_after)
            return requests.post(api_url, data=payload).status_code
        return response.status_code
    except Exception as e:
        print(f"发送失败: {e}")
        return None

def main():
    config = load_config()
    feeds = config.get("feeds", [])
    global_exclude = config.get("global_filters", [])
    
    history_links = load_sent_links()
    history_set = set(history_links)
    new_links = list(history_links) # 保持顺序用于切片

    for f_conf in feeds:
        url = f_conf.get("url")
        print(f"正在扫描: {f_conf.get('category')} - {url}")
        try:
            feed = feedparser.parse(url)
            for entry in reversed(feed.entries):
                link = entry.link
                if link not in history_set:
                    # 关键字过滤逻辑
                    if should_filter(entry.title, f_conf, global_exclude):
                        print(f"已过滤: {entry.title}")
                        continue
                        
                    status = send_tg_message(entry, f_conf)
                    if status == 200:
                        new_links.append(link)
                        history_set.add(link)
                        print(f"已推送: {entry.title}")
                        time.sleep(2)
        except Exception as e:
            print(f"源错误 {url}: {e}")

    # 保存并更新数据库（包含自动清理逻辑）
    save_sent_links(new_links)

if __name__ == "__main__":
    main()
