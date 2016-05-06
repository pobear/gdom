import urlparse
import graphene
from pyquery import PyQuery as pq
import re
import requests
from requests.packages import chardet

GDOM_HEADERS = {
    'Referer': 'http://www.baidu.com',
    'Upgrade-Insecure-Requests': '1',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/52.0.2716.0 Safari/537.36'
}


class QueryClient(object):
    headers = {
        'Referer': 'http://www.baidu.com',
        'Upgrade-Insecure-Requests': '1',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/52.0.2716.0 Safari/537.36'
    }
    host = None
    client_type = 'requests'

    def get_query(self, page, headers=None, client_type=None, is_host=False):
        if headers:
            self.headers.update(headers)
        if client_type:
            self.client_type = client_type

        page = page.strip()
        if re.search('^https?://', page):
            print page
            p = urlparse.urlparse(page)

            if is_host:
                self.host = '%s://%s' % (p.scheme, p.netloc)

            if self.client_type == 'requests':
                r = requests.get(page, headers=self.headers)
                print r.encoding
                # r.encoding = chardet.detect(r.content).get('encoding')
                return pq(r.content)
            else:
                return pq(page, headers=self.headers)
        else:
            return pq(page)


class Node(graphene.Interface):
    """A Node represents a DOM Node"""
    content = graphene.String(description='The html representation of the subnodes for the selected DOM',
                              selector=graphene.String())
    html = graphene.String(description='The html representation of the selected DOM',
                           selector=graphene.String())
    text = graphene.String(description='The text for the selected DOM',
                           selector=graphene.String())
    tag = graphene.String(description='The tag for the selected DOM',
                          selector=graphene.String())
    attr = graphene.String(description='The DOM attr of the Node',
                           selector=graphene.String(),
                           name=graphene.String().NonNull)
    _is = graphene.Boolean(description='Returns True if the DOM matches the selector',
                           name='is', selector=graphene.String().NonNull)
    query = graphene.List('Element',
                          description='Find elements using selector traversing down from self',
                          selector=graphene.String().NonNull)
    children = graphene.List('Element',
                             description='The list of children elements from self',
                             selector=graphene.String())
    parents = graphene.List('Element',
                            description='The list of parent elements from self',
                            selector=graphene.String())
    parent = graphene.Field('Element',
                            description='The parent element from self')
    siblings = graphene.List('Element',
                             description='The siblings elements from self',
                             selector=graphene.String())
    next = graphene.Field('Element',
                          description='The immediately following sibling from self',
                          selector=graphene.String())
    next_all = graphene.List('Element',
                             description='The list of following siblings from self',
                             selector=graphene.String())
    prev = graphene.Field('Element',
                          description='The immediately preceding sibling from self',
                          selector=graphene.String())
    prev_all = graphene.List('Element',
                             description='The list of preceding siblings from self',
                             selector=graphene.String())

    def _query_selector(self, args):
        selector = args.get('selector')
        if not selector:
            return self._root

        p = None
        pattern = r'([\w.-]+):eq\((\d+)\)'
        if re.search(pattern, selector):
            for q in selector.split():
                # selector like "td:eq(2) a:eq(3)"
                s = re.search(pattern, q)
                p = p or self._root
                if s:
                    p = p.find(s.group(1)).eq(int(s.group(2)))
                else:
                    p = p.find(q).eq(0)

        if not p:
            p = self._root.find(selector)

        # print selector, p
        return p

    def resolve_content(self, args, info):
        return self._query_selector(args).eq(0).html()

    def resolve_html(self, args, info):
        return self._query_selector(args).outerHtml()

    def resolve_text(self, args, info):
        return self._query_selector(args).eq(0).remove('script').text()

    def resolve_tag(self, args, info):
        el = self._query_selector(args).eq(0)
        if el:
            return el[0].tag

    def resolve__is(self, args, info):
        return self._root.is_(args.get('selector'))

    def resolve_attr(self, args, info):
        attr = args.get('name')
        return self._query_selector(args).attr(attr)

    def resolve_query(self, args, info):
        return self._query_selector(args).items()

    def resolve_children(self, args, info):
        selector = args.get('selector')
        return self._root.children(selector).items()

    def resolve_parents(self, args, info):
        selector = args.get('selector')
        return self._root.parents(selector).items()

    def resolve_parent(self, args, info):
        parent = self._root.parents().eq(-1)
        if parent:
            return parent

    def resolve_siblings(self, args, info):
        selector = args.get('selector')
        return self._root.siblings(selector).items()

    def resolve_next(self, args, info):
        selector = args.get('selector')
        _next = self._root.nextAll(selector)
        if _next:
            return _next.eq(0)

    def resolve_next_all(self, args, info):
        selector = args.get('selector')
        return self._root.nextAll(selector).items()

    def resolve_prev(self, args, info):
        selector = args.get('selector')
        prev = self._root.prevAll(selector)
        if prev:
            return prev.eq(0)

    def resolve_prev_all(self, args, info):
        selector = args.get('selector')
        return self._root.prevAll(selector).items()


# def get_page(page, headers=None, client_type=None):
#     page = page.strip()
#     print page
#     if re.search('^https?://', page):
#         headers = headers and GDOM_HEADERS.update(headers) or GDOM_HEADERS
#         if client_type == 'requests':
#             r = requests.get(page, headers=headers)
#             print r.encoding
#             # r.encoding = chardet.detect(r.content).get('encoding')
#             return pq(r.content)
#         else:
#             return pq(page, headers=headers)
#     else:
#         return pq(page)


class Document(Node):
    """
    The Document Type represent any web page loaded and
    serves as an entry point into the page content
    """
    title = graphene.String(description='The title of the document')

    def resolve_title(self, args, info):
        return self._root.find('title').eq(0).text()


class Element(Node):
    """
    A Element Type represents an object in a Document
    """

    visit = graphene.Field(Document,
                           description='Visit will visit the href of the link and return the corresponding document')

    def resolve_visit(self, args, info):
        # If is a link we follow through href attr
        # return the resulting Document
        if self._root.is_('a'):
            url = self._root.attr('href')
            if not re.search(r'https?://', url):
                url = urlparse.urljoin(query_client.host, url)

            return query_client.get_query(url)


class Query(graphene.ObjectType):
    page = graphene.Field(Document,
                          description='Visit the specified page',
                          url=graphene.String(description='The url of the page'),
                          source=graphene.String(description='The source of the page'),
                          headers=graphene.String(description='The headers of the page'),
                          client=graphene.String(description='HTTP client: requests or pyquery'))

    def resolve_page(self, args, info):
        url = args.get('url')
        source = args.get('source')
        header = args.get('headers')
        client_type = args.get('client')
        headers = header and dict([map(lambda x: x.strip(), h.split(':')) for h in header.split('|')]) or {}

        assert url or source, 'At least you have to provide url or source of the page'
        return query_client.get_query(
            url or source, headers=headers, client_type=client_type, is_host=True)


schema = graphene.Schema(query=Query)
schema.register(Element)
query_client = QueryClient()
