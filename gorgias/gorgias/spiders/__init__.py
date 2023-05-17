import json
from pathlib import Path
from urllib.parse import urlencode
import datetime
import scrapy
from scrapy import Selector

API_KEY = '23d3ba9b-0468-4141-bbc5-d9ca071b9406'


def get_scrapeops_url(url):
    payload = {'api_key': API_KEY, 'url': url, 'bypass': 'cloudflare'}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url


class KickstarterSpider(scrapy.Spider):
    name = "kickstarter"
    projects_url = "https://www.kickstarter.com/discover/advanced?raised=2&sort=end_date&page="
    page = 0
    project_data = {}

    def start_requests(self):
        self.page += 1
        url = self.projects_url + str(self.page)
        yield scrapy.Request(url=get_scrapeops_url(url), callback=self.parse_projects_list)

    def scrape_profile(self):
        url = f"https://www.kickstarter.com/profile/{str(self.project_data['creator']['id'])}/about"
        yield scrapy.Request(url=get_scrapeops_url(url), callback=self.parse_profile)

    def parse_projects_list(self, response):
        now = datetime.datetime.now()
        filename = f"pages/kickstarter-projects-{now.year}-{now.month}-{now.day}-{str(self.page)}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")
        selector = Selector(response)
        all_projects = selector.css('.js-react-proj-card::attr(data-project)').getall()
        for project in all_projects:
            self.set_project_data(project)
            self.scrape_profile()
            return
        # project_group = selector.css('.js-project-group')
        # for project in project_group.css('.js-react-proj-card'):
        #     self.set_project_data(project)
        #     self.scrape_profile()
        #     return

    def parse_profile(self, response):
        print(response.url)
        now = datetime.datetime.now()
        filename = f"profiles/{self.project_data['creator']['id']}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")

    def set_project_data(self, project_data_text):
        project_data = json.loads(project_data_text)
        filename = f"projects/project-{project_data['id']}.json"
        f = open(filename, 'w')
        f.write(project_data_text)
        f.close()
        self.project_data = project_data

