from selenium import webdriver
import urllib

class duckduckgoSearch:
    def __init__(self):
        self.driver = webdriver.Chrome()

    
    def searchDuckduckgo(self, query: str):
    #     """
    #     Performs a DuckDuckGo search for the given query.
    #     """

    #     # Locate search input
    #     url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&kl=us-en&hl=en&ia=web"
    #     self.driver.get(url)
        q1 = urllib.parse.quote(query)
        q2 = urllib.parse.quote(query + " in English")
        
        url1 = f"https://duckduckgo.com/?q={q2}&kl=us-en&hl=en"
        url2 = f"https://duckduckgo.com/?q={q1}&ia=images&iax=images"

        tabs = self.driver.window_handles

        # First run → create second tab
        if len(tabs) == 1:
            self.driver.get(url1)
            self.driver.execute_script(f"window.open('{url2}', '_blank');")

        # Later runs → reuse tabs
        else:
            self.driver.switch_to.window(tabs[0])
            self.driver.get(url1)

            self.driver.switch_to.window(tabs[1])
            self.driver.get(url2)
        

       

    def teardown(self):
        if self.driver:
            self.driver.quit()