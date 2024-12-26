import scrapy
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
import os
from django.conf import settings  # Import Django settings for MEDIA_ROOT

class LinksSpider(scrapy.Spider):
    name = 'dossiefoyer_links'
    allowed_domains = []
    start_urls = []

    scrape_normal_links = False
    scrape_image_links = False
    scrape_video_links = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.normal_root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        self.image_root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        self.video_root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        self.scraped_urls = set()
        # Save to MEDIA_ROOT to align with Django's file serving
        self.output_file_path = os.path.join(settings.MEDIA_ROOT, "combined_sitemap.xml")

    def parse(self, response):
        # Scrape normal links
        if self.scrape_normal_links:
            for link in response.css('a::attr(href)'):
                full_url = response.urljoin(link.get())
                if full_url.startswith("http") and full_url not in self.scraped_urls:
                    self.scraped_urls.add(full_url)
                    self.add_url_to_sitemap(full_url, self.normal_root)

        # Scrape image links
        if self.scrape_image_links:
            for img in response.css('img::attr(src)'):
                full_img_url = response.urljoin(img.get())
                if full_img_url.startswith("http") and full_img_url not in self.scraped_urls:
                    self.scraped_urls.add(full_img_url)
                    self.add_url_to_sitemap(full_img_url, self.image_root)

        # Scrape video links
        if self.scrape_video_links:
            for video in response.css('video::attr(src), source::attr(src)'):
                video_src = video.get()
                if video_src:
                    full_video_url = response.urljoin(video_src)
                    if full_video_url.startswith("http") and full_video_url not in self.scraped_urls:
                        self.scraped_urls.add(full_video_url)
                        self.add_url_to_sitemap(full_video_url, self.video_root)

        # Follow pagination
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
        else:
            self.write_combined_sitemap()

    def add_url_to_sitemap(self, url, root):
        url_element = ET.SubElement(root, "url")
        ET.SubElement(url_element, "loc").text = url
        ET.SubElement(url_element, "lastmod").text = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
        ET.SubElement(url_element, "priority").text = "0.80"

    def write_combined_sitemap(self):
        combined_root = ET.Element("sitemap")

        if self.scrape_normal_links:
            combined_root.append(self.normal_root)

        if self.scrape_image_links:
            combined_root.append(self.image_root)

        if self.scrape_video_links:
            combined_root.append(self.video_root)

        # Write XML to file
        xml_str = minidom.parseString(ET.tostring(combined_root)).toprettyxml(indent="  ")
        os.makedirs(os.path.dirname(self.output_file_path), exist_ok=True)  # Ensure the directory exists
        with open(self.output_file_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
        self.log(f"Sitemap successfully written to {self.output_file_path}")
