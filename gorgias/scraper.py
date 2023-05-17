from scrapy import Selector

html = '''
<div class="js-project-group">
    <div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
    </div>
    <div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
        <div class="js-react-proj-card grid-col-12 grid-col-6-sm grid-col-4-lg" data-project="{id:'hehe',people:34}"></div>
    </div>
</div>
'''

# Create a Scrapy Selector from the HTML content
selector = Selector(text=html)

# Extract the data-project attribute value
data_projects = selector.css('.js-react-proj-card::attr(data-project)').getall()

print(data_projects)
