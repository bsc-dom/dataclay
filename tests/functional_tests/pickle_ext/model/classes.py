
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
    
    @dclayMethod()
    def remove_last_web_page(self):
        self.pages.pop()
    
    @dclayMethod(uri="str")
    def modify_uri_str(self, uri):
        self.uri = URI(uri)

    @dclayMethod(uri="model.classes.URI")
    def modify_uri(self, uri):
        self.uri = uri

class WebPage(StorageObject):
    '''
    @ClassField uri model.classes.URI
    @ClassField external_links list<model.classes.WebSite>
    @ClassField num int
    '''

    @dclayMethod(uri="str", num="int")
    def __init__(self, uri, num=None):
        self.uri = URI(uri)
        self.external_links = list()
        self.num = num

    @dclayMethod(link="model.classes.WebSite")
    def add_link(self, link):
        self.external_links.append(link)

    @dclayMethod(uri="str")
    def modify_uri_str(self, uri):
        self.uri = URI(uri)
    
    @dclayMethod(uri="model.classes.URI")
    def modify_uri(self, uri):
        self.uri = uri

    @dclayMethod(num="int")
    def modify_num(self, num):
        self.num = num
