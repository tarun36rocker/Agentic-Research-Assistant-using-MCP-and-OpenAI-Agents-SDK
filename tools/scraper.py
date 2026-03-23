from newspaper import Article

def scrape_url(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text[:2000]
    except:
        return ""