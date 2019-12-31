
import scrapy
from scrapy_splash import SplashRequest
from scrapy.shell import inspect_response
class MendelsonSpider(scrapy.Spider):
    name = "mendelson"
    start_urls = [
        'http://www.mendelson.co.il/%D7%A7%D7%98%D7%9C%D7%95%D7%92-%D7%9E%D7%95%D7%A6%D7%A8%D7%99%D7%9D',
    ]

    def parse(self, response):
        for href in response.css(".content .triplebox a::attr(href)"):
            yield response.follow(href, self.parse_sub_cat)

    def parse_sub_cat(self, response):
        title = response.css("#pageMaintitle h1::text").get()  
        self.logger.info(title)
        if self._is_category(response):
            for href in response.css(".content .triplebox a::attr(href)").getall():
                yield scrapy.Request(url="http://www.mendelson.co.il{ref}".format(ref=href), callback=self.parse_sub_cat)
        else:
            yield SplashRequest(
                response.url,
                self.parse_table,
                endpoint='render.html',
                args={'wait': 1},)
                

    def parse_table(self, response):
        for item in response.css(".tableofproducts .product_single"):
            yield {
                "title": item.css("div:nth-child(4) a::text").get(),
                "makat": item.css("div:nth-child(3) a::text").get(),
                "img": item.css("div:nth-child(2) img::attr(src)").get(),
                "href": item.css("div:nth-child(3) a::attr(href)").get(),
            }
        script = self._find_next_page(response)
        if script:
            yield self._build_lua_script(response, script)
            
    def _build_lua_script(self, response, script):
        return SplashRequest(
                response.url,
                self.parse_table,
                endpoint='execute',
                args={'lua_source': script},)

    def _find_next_page(self, response):
        page_size = len(response.css(".navigator .getPageItems"))
        page = response.css(".navigator .getPageItems.active::text").get()
        if page == None:
            return
        current_page = int(page)
        self.logger.info("Found {size} pages, in page {cur}".format(size=page_size, cur=current_page))
        if page_size == current_page:
            return
        js = 'document.querySelector(".navigator .getPageItems:nth-child({page})").click()'.format(page=str(current_page + 1))
        script="""
function main(splash)
    splash:go(splash.args.url)
    splash:wait(0.5)
    splash:runjs('{code}')
    splash:wait(0.5)
    return {{
        html = splash:html(),
    }}
end
""".format(code=js)
        return script


    def _is_category(self, response):
        return len(response.css(".content .triplebox a::attr(href)")) != 0

            
