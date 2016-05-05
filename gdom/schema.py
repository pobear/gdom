import graphene
from pyquery import PyQuery as pq
import re

GDOM_DEFAULT_HEADERS = {
    'Cookie': 'JSESSIONID=1C6FB72E83982B8309F7B411BC5F4186.tomcat2',
    'Referer': 'http://58.118.0.15/admin/toIndex.dhtml',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/52.0.2716.0 Safari/537.36'
}


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
        for q in selector.split():
            # selector like "td:eq(2) a:eq(3)"
            s = re.search(r'^(.+):eq\((\d+)\)$', q)
            if s:
                p = p and p.find(s.group(1)).eq(int(s.group(2)))\
                    or self._root.find(s.group(1)).eq(int(s.group(2)))
            elif p:
                p = p.find(q).eq(0)

        if not p:
            p = self._root.find(selector)

        print selector, p
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


def get_page(page, headers=None):
    headers = headers or GDOM_DEFAULT_HEADERS
    return pq(page, headers=headers)


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
            href = self._root.attr('href')
            return get_page(href)


class Query(graphene.ObjectType):
    page = graphene.Field(Document,
                          description='Visit the specified page',
                          url=graphene.String(description='The url of the page'),
                          source=graphene.String(description='The source of the page'))

    def resolve_page(self, args, info):
        url = args.get('url')
        source = args.get('source')
        assert url or source, 'At least you have to provide url or source of the page'
        return get_page(url or source)


schema = graphene.Schema(query=Query)
schema.register(Element)
