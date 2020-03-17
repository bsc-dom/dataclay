
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject

class URI(StorageObject):
    '''
    @ClassField host str
    @ClassField path str
    '''
    
    # example.com/page.html
    # host = example.com
    # path = page.html
    
    @dclayMethod(uri="str")
    def __init__(self, uri):
        splitted_uri = uri.split('/')
        self.host = splitted_uri[0]
        self.path = '/'.join(splitted_uri[1:]) if len(splitted_uri) > 1 else None
        
class WebSite(StorageObject):
    '''
    @ClassField uri model.classes.URI
    @ClassField pages list<model.classes.WebPage>
    '''

    @dclayMethod(uri="str")
    def __init__(self, uri):
        self.uri = URI(uri)
        self.pages = list()

    @dclayMethod(page="model.classes.WebPage")
    def add_web_page(self, page):
        if(self.uri.host == page.uri.host):
            self.pages.append(page)
        
class WebPage(StorageObject):
    '''
    @ClassField uri model.classes.URI
    @ClassField external_links list<model.classes.WebSite>
    '''

    @dclayMethod(uri="str")
    def __init__(self, uri):
        self.uri = URI(uri)
        self.external_links = list()

    @dclayMethod(link="model.classes.WebSite")
    def add_link(self, link):
        if(self.uri.host != link.uri.host):
            self.external_links.append(link)
