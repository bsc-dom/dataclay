
""" Class description goes here. """

from dataclay import dclayMethod
from storage.api import StorageObject


class URI(StorageObject):
    """
    @ClassField host str
    @ClassField path str
    """
    
    # example.com/page.html
    # host = example.com
    # path = page.html
    
    @dclayMethod(uri="str")
    def __init__(self, uri):
        splitted_uri = uri.split('/')
        self.host = splitted_uri[0]
        self.path = '/'.join(splitted_uri[1:]) if len(splitted_uri) > 1 else None


class WebSite(StorageObject):
    """
    @ClassField uri model.classes.URI
    @ClassField pages list<model.classes.WebPage>
    @dclayReplication(afterUpdate='replicateToSlaves', inMaster='False')
    @ClassField replyme str
    @ClassField myself model.classes.WebSite
    """

    @dclayMethod(uri="str")
    def __init__(self, uri):
        self.uri = URI(uri)
        self.pages = list()
        self.replyme = "foo"
        self.myself = self

    @dclayMethod(page="model.classes.WebPage")
    def add_web_page(self, page):
        if self.uri.host == page.uri.host:
            self.pages.append(page)
    
    @dclayMethod(from_site="model.classes.WebSite")    
    def copy_pages(self, from_site):
        for page in from_site.pages:
            p = page.dc_clone()
            self.pages.append(p)
            
    @dclayMethod(from_site="model.classes.WebSite")            
    def update_pages(self, from_site):
        self.dc_update(from_site)

    @dclayMethod(attribute="str", value="anything")
    def replicateToSlaves(self, attribute, value):
        from dataclay.DataClayObjProperties import DCLAY_SETTER_PREFIX
        for exeenv_id in self.get_all_locations().keys():
        #if not exeenv_id is master_location:
            self.run_remote(exeenv_id, DCLAY_SETTER_PREFIX + attribute, value)


class WebPage(StorageObject):
    """
    @ClassField uri model.classes.URI
    @ClassField external_links list<model.classes.WebSite>
    """

    @dclayMethod(uri="str")
    def __init__(self, uri):
        self.uri = URI(uri)
        self.external_links = list()

    @dclayMethod(link="model.classes.WebSite")
    def add_link(self, link):
        if self.uri.host != link.uri.host:
            self.external_links.append(link)


class MissingAttributeConstructor(StorageObject):
    """
    @ClassField present str
    @ClassField missing str
    """
    @dclayMethod(present="str")
    def __init__(self, present):
        self.present = present

    @dclayMethod(s="str")
    def assign_missing(self, s):
        self.missing = s


class HasStrMethod(StorageObject):
    """
    @ClassField msg str
    """
    @dclayMethod(msg="str")
    def __init__(self, msg):
        self.msg = msg

    @dclayMethod(return_="str")
    def __str__(self):
        return "Message: %s" % self.msg


class HasEqMethod(StorageObject):
    """
    @ClassField val int
    """
    @dclayMethod(val="int")
    def __init__(self, val):
        self.val = val

    @dclayMethod(other="model.classes.HasEqMethod", return_="bool")
    def __eq__(self, other):
        if not isinstance(other, HasEqMethod):
            return False

        return other.val == self.val


class FancyUUMethods(StorageObject):
    """
    @ClassField value int
    @ClassField message str
    """

    @dclayMethod(value="int", message="str")
    def __init__(self, value, message):
        self.value = value
        self.message = message

    @dclayMethod(other="model.classes.FancyUUMethods", return_="bool")
    def __eq__(self, other):
        if not isinstance(other, FancyUUMethods):
            return False

        return self.value == other.value

    @dclayMethod(return_="str")
    def __str__(self):
        return "Message[%d]: %s" % (self.value, self.message)

    @dclayMethod(return_="int")
    def __hash__(self):
        return self.value + 42
