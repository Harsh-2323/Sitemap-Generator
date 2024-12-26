import os
from django.http import JsonResponse, FileResponse, Http404
from django.shortcuts import render
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor
from webscraper.spiders.dossiefoyer_links import LinksSpider
from django.views.decorators.csrf import csrf_exempt
import threading
from django.conf import settings

# Initialize the Scrapy Runner globally
configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
runner = CrawlerRunner()
reactor_started = False
reactor_thread = None
scraping_in_progress = False  # Flag to indicate scraping status

# Define the absolute path for the sitemap file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from django.conf import settings

# Use MEDIA_ROOT for saving the sitemap
SITEMAP_FILE_PATH = os.path.join(settings.MEDIA_ROOT, 'combined_sitemap.xml')



def index(request):
    """Render the index page."""
    return render(request, 'index.html')


@csrf_exempt
def start_scraping(request):
    """Start the scraping process asynchronously."""
    global reactor_started, reactor_thread, scraping_in_progress

    if request.method == 'POST':
        if scraping_in_progress:
            return JsonResponse({'status': 'error', 'message': 'Scraping is already in progress. Please wait.'})

        # Get user inputs
        site_url = request.POST.get('siteUrl')
        scrape_normal_links = request.POST.get('scrapeNormalLinks') == 'true'
        scrape_image_links = request.POST.get('scrapeImages') == 'true'
        scrape_video_links = request.POST.get('scrapeVideos') == 'true'

        # Validate the URL
        if not site_url or not site_url.startswith("http"):
            return JsonResponse({'status': 'error', 'message': 'Invalid URL'})

        # Configure the Scrapy spider dynamically
        LinksSpider.start_urls = [site_url]
        LinksSpider.scrape_normal_links = scrape_normal_links
        LinksSpider.scrape_image_links = scrape_image_links
        LinksSpider.scrape_video_links = scrape_video_links

        # Start the reactor if not already running
        if not reactor_started:
            reactor_thread = threading.Thread(target=run_reactor)
            reactor_thread.daemon = True
            reactor_thread.start()

        # Start the crawl process
        scraping_in_progress = True
        runner.crawl(LinksSpider).addBoth(lambda _: finish_scraping())

        return JsonResponse({'status': 'success', 'message': 'Scraping started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def check_sitemap_status(request):
    """Check if the sitemap file is ready."""
    if os.path.exists(SITEMAP_FILE_PATH):
        return JsonResponse({'status': 'ready', 'message': 'Sitemap ready'})
    elif scraping_in_progress:
        return JsonResponse({'status': 'pending', 'message': 'Sitemap is being generated...'})
    else:
        return JsonResponse({'status': 'error', 'message': 'No sitemap file found, or generation not started.'})


def run_reactor():
    """Run the Twisted reactor."""
    global reactor_started
    try:
        reactor.run(installSignalHandlers=False)  # Start the reactor
    except RuntimeError:
        pass  # Reactor already running
    finally:
        reactor_started = True


import logging

logger = logging.getLogger(__name__)

def finish_scraping():
    """Reset the scraping flag once scraping is complete."""
    global scraping_in_progress
    try:
        if os.path.exists(SITEMAP_FILE_PATH):
            scraping_in_progress = False
            logger.info(f"Sitemap saved at {SITEMAP_FILE_PATH}")
        else:
            logger.error(f"Sitemap not found at {SITEMAP_FILE_PATH}")
    except Exception as e:
        logger.error(f"Error in finish_scraping: {e}")





def download_sitemap(request):
    """Serve the generated sitemap file for download."""
    if os.path.exists(SITEMAP_FILE_PATH):
        try:
            return FileResponse(open(SITEMAP_FILE_PATH, 'rb'), as_attachment=True, filename='combined_sitemap.xml')
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error serving file: {str(e)}'})
    else:
        raise Http404("Sitemap file not found.")
