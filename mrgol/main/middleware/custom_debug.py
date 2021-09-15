from debug_toolbar import middleware

def show_toolbar(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    return True
middleware.show_toolbar = show_toolbar

class Custom_DebugToolbarMiddleware(middleware.DebugToolbarMiddleware):
    pass
