import re


class AdDeleter:
    ad_ids = [
        'ads_feed_placeholder',
        'ads_left',
        'ads_ads_news_wrap'
    ]

    ad_props = [
        'data-da',
        'data-ad-view'
    ]

    def __init__(self, html):
        self.html = html

    def get_content_without_ads(self):
        self.find_and_replace_add()
        return self.html

    def find_and_replace_add(self):
        for id in AdDeleter.ad_ids:
            self.html = re.sub(rf'<div([^>]*)id="{id}"([^>]*)>([^<]*)</div>', '', self.html)
        for prop in AdDeleter.ad_props:
            self.html = re.sub(rf'<div([^>]*){prop}=([^>]*)>([^<]*)</div>', '', self.html)
