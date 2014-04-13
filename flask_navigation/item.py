import collections

from flask import url_for, request

from .utils import freeze_dict


class Item(object):
    """The navigation item object.

    :param label: the display label of this navigation item.
    :param endpoint: the unique name of this navigation item.
                     If this item point to a internal url, this parameter
                     should be acceptable for ``url_for`` which will generate
                     the target url.
    :param args: optional. If this parameter be provided, it will be passed to
                 the ``url_for`` with ``endpoint`` together.
                 Maybe this arguments need to be decided in the Flask app
                 context, then this parameter could be a function to delay the
                 execution.
    :param url: optional. If this parameter be provided, the target url of
                this navigation will be it. The ``endpoint`` and ``args`` will
                not been used to generate url.

    The ``endpoint`` is the identity name of this navigation item. It will be
    unique in whole application. In mostly situation, it should be a endpoint
    name of a Flask view function.
    """

    def __init__(self, label, endpoint, args=None, url=None):
        self.label = label
        self.endpoint = endpoint
        self._args = args
        self._url = url

    @property
    def args(self):
        """The arguments which will be passed to ``url_for``."""
        if self._args is None:
            return {}
        if callable(self._args):
            return dict(self._args())
        return dict(self._args)

    @property
    def url(self):
        """The final url of this navigation item."""
        if self._url is None:
            return url_for(self.endpoint, **self.args)
        return self._url

    @property
    def is_active(self):
        is_internal = (self._url is None)
        has_same_endpoint = (request.endpoint == self.endpoint)
        has_same_args = (request.view_args == self.args)
        return is_internal and has_same_endpoint and has_same_args

    @property
    def ident(self):
        return self.endpoint, freeze_dict(self.args)


class ItemCollection(collections.MutableSequence,
                     collections.Iterable):
    """The collection of navigation items.

    This collection is a mutable sequence. All items have order index, and
    could be found by its endpoint name. e.g.::

        c = ItemCollection()
        c.append(Item(endpoint='doge'))

        print(c['doge'])  # output: Item(endpoint='doge')
        print(c[0])       # output: Item(endpoint='doge')
        print(c)          # output: ItemCollection([Item(endpoint='doge')])
        print(len(c))     # output: 1
    """

    def __init__(self, iterable=[]):
        #: the item collection
        self._items = []
        #: the mapping collection of endpoint -> item
        self._items_mapping = {}
        #: initial extending
        self.extend(iterable)

    def __repr__(self):
        return 'ItemCollection(%r)' % self._items

    def __getitem__(self, index):
        if isinstance(index, int):
            return self._items[index]

        if isinstance(index, tuple):
            endpoint, args = index
        else:
            endpoint, args = index, {}
        ident = (endpoint, freeze_dict(args))
        return self._items_mapping[ident]

    def __setitem__(self, index, item):
        # remove the old reference
        old_item = self._items[index]
        del self._items_mapping[old_item.ident]

        self._items[index] = item
        self._items_mapping[item.ident] = item

    def __delitem__(self, index):
        item = self[index]
        del self._items[index]
        del self._items_mapping[item.ident]

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def insert(self, index, item):
        self._items.insert(index, item)
        self._items_mapping[item.ident] = item
