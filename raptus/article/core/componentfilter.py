from zope import interface, component

from zope.viewlet.interfaces import IViewlet
from zope.publisher.interfaces.http import IHTTPRequest
from zope.publisher.interfaces.browser import IBrowserView
from plone.app.layout.viewlets import interfaces as viewletmanagers

from raptus.article.core import interfaces


ORDERED_VIEWLET_MANAGERS = (('plone.portaltop', viewletmanagers.IPortalTop),
                            ('plone.portalheader', viewletmanagers.IPortalHeader),
                            ('plone.contentviews', viewletmanagers.IContentViews),
                            ('plone.abovecontent', viewletmanagers.IAboveContent),
                            ('plone.abovecontenttitle', viewletmanagers.IAboveContentTitle),
                            ('plone.documentactions', viewletmanagers.IDocumentActions),
                            ('plone.belowcontenttitle', viewletmanagers.IBelowContentTitle),
                            ('plone.abovecontentbody', viewletmanagers.IAboveContentBody),
                            ('plone.belowcontentbody', viewletmanagers.IBelowContentBody),
                            ('plone.belowcontent', viewletmanagers.IBelowContent),
                            ('plone.portalfooter', viewletmanagers.IPortalFooter))
VIEWLET_MANAGER_MAP = dict(ORDERED_VIEWLET_MANAGERS)


class ComponentFilter(object):
    """ Filters and sorts components based on the registration of their viewlets
    """
    interface.implements(interfaces.IComponentFilter)
    component.adapts(interface.Interface, IHTTPRequest, IBrowserView)

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.view = view

    def filter(self, components, manager=None):
        """ Returns a filtered list of components
        """
        order = []
        # temporary provide all interfaces of the registered components
        notprovided = []
        for name, comp in components:
            if not comp.interface.providedBy(self.context):
                notprovided.append(comp.interface)
                interface.alsoProvides(self.context, comp.interface)
        view = component.getMultiAdapter((self.context, self.request), name=u'view')
        if manager is not None:
            manager = component.getMultiAdapter((self.context, self.request, view), VIEWLET_MANAGER_MAP.get(manager, object()), name=manager)
            viewlets = component.getAdapters((self.context, self.request, view, manager), IViewlet)
            viewlets = manager.filter(viewlets)
            viewlets = manager.sort(viewlets)
            for name, viewlet in viewlets:
                order.append(name)
        else:
            for name, iface in ORDERED_VIEWLET_MANAGERS:
                manager = component.getMultiAdapter((self.context, self.request, view), iface, name=name)
                viewlets = component.getAdapters((self.context, self.request, view, manager), IViewlet)
                viewlets = manager.filter(viewlets)
                viewlets = manager.sort(viewlets)
                for name, viewlet in viewlets:
                    order.append(name)
        # no longer provide the interfaces previously set
        for iface in notprovided:
            interface.noLongerProvides(self.context, iface)
        components = [(name, comp) for name, comp in components if comp.viewlet in order]
        components.sort(lambda x, y: cmp(order.index(x[1].viewlet), order.index(y[1].viewlet)))
        return components
