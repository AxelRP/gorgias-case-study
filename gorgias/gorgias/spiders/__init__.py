import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import scrapy
from scrapy import Selector
import requests
import os
import segment.analytics as segment

SCRAPEOPS_API_KEY = '23d3ba9b-0468-4141-bbc5-d9ca071b9406'
SEGMENT_KEY = 'Q6QwJI6Zo7Alfp5UxKoKncwh0xu3nk2O'
COGNISM_API_KEY = '<API_KEY>'


def get_scrapeops_url(url):  # Use ScrapeOps to bypass anti-scraping security
    payload = {'api_key': SCRAPEOPS_API_KEY, 'url': url, 'bypass': 'cloudflare'}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url


def call_it_a_day(project_data):
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday < datetime.fromtimestamp(project_data['deadline'])  # Exit strategy


class GetProjects(scrapy.Spider):
    name = "getProjects"
    base_url = "https://www.kickstarter.com/discover/advanced?raised=2&sort=end_date&page="
    page = 1
    urls = []

    def start_requests(self):
        self.urls.append(self.base_url + str(self.page))  # Add starting url
        for url in self.urls:
            yield scrapy.Request(url=get_scrapeops_url(url), callback=self.parse_projects_list)

    def parse_projects_list(self, response):
        selector = Selector(response)
        all_projects = selector.css('.js-react-proj-card::attr(data-project)').getall()
        for project in all_projects:
            self.save_project_data(project)

    def save_project_data(self, project_data_text):
        project_data = json.loads(project_data_text)
        if call_it_a_day(project_data):
            return
        filename = f"projects/{project_data['id']}.json"
        f = open(filename, 'w')
        f.write(project_data_text)
        f.close()

        #  Add next projects page
        self.page += 1
        self.urls.append(self.base_url + str(self.page))  # Add next url


class GetProfiles(scrapy.Spider):
    name = "getProfiles"
    projects = []
    projects_path = 'projects'

    def load_projects(self):
        for filename in os.listdir(self.projects_path):
            with open(os.path.join(self.projects_path, filename)) as json_file:
                self.projects.append(json.load(json_file))

    def start_requests(self):
        self.load_projects()
        for project in self.projects:
            url = f"https://www.kickstarter.com/profile/{project['creator']['id']}/about"
            yield scrapy.Request(url=get_scrapeops_url(url), callback=self.parse_profile, cb_kwargs={'project_data': project})
        self.clean_projects_dir()  # Clean projects directory for tomorrow's execution

    def parse_profile(self, response, project_data):
        selector = Selector(response)
        website = selector.css('.menu-submenu a::text').get()
        if website is not None:
            company = company_enrichment(website)
            if company['uses_shopify'] == 'yes':
                contacts = get_people_from_company_domain(company['domain'])
                for contact in contacts:
                    segment_track_call(contact, project_data)

    def clean_projects_dir(self):
        for filename in os.listdir(self.projects_path):
            file_path = os.path.join(self.projects_path, filename)
            os.remove(file_path)


def company_enrichment(domain):
    #  Get company data from datamorf.io
    data = {
        "domain": domain
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(
        'https://us-central1-call-center-d08cb.cloudfunctions.net/v1/LKCGrUC41ILEUmFVQN/trigger/domain',
        data=json.dumps(data),
        headers=headers
    )
    return response.json()


def segment_track_call(contact, project):
    segment.write_key = SEGMENT_KEY
    segment.track(contact['email'], 'kickstarter-campaign-completed', {
        'name': contact['name'],
        'project_name': project['name'],
        'total_funding_amount': project['pledged'],
        'company_name': contact['company_name'],
        'email': contact['email']
    })


def get_people_from_company_domain(domain):
    headers = {
        "Authorization": f"Bearer {COGNISM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "filters": {
            "domain": domain,
            "job_titles": ["customer support", "support"]
        }
    }

    response = requests.post("https://api.cognism.com/v1/people/search", headers=headers, json=payload)
    contacts = []
    if response.status_code == 200:
        data = response.json()
        redeem_ids = []
        for person in data['results']:
            redeem_ids.append(person['redeemId'])
        ids = json.dumps(redeem_ids)
        redeem_response = requests.post(
            f"https://api.cognism.com/v1/contacts/redeem",
            data=ids,
            headers=headers
        )
        if redeem_response.status_code == 200:
            redeemed_contacts = redeem_response.json()
            for contact in redeemed_contacts['result']:
                contacts.append({
                    'name': contact['firstName'],
                    'email': contact['email']['address'],
                    'company_name': contact['account']['name']
                })
    return contacts
