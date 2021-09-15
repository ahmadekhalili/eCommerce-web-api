class LiveChatMiddleware(object):
    # Check if client IP is allowed
    def process_request(self, request):
        sessionid = if request.COOKIES.get('sessionid') else request.COOKIES.get('vsessionid')   #vsessionid for unauthenticate users of site.
        chats = {}
        if sessionid:
            
        allowed_ips = ['192.168.1.1', '123.123.123.123', etc...] # Authorized ip's
        ip = request.META.get('REMOTE_ADDR') # Get client IP
        if ip not in allowed_ips:
            raise Http403 # If user is not allowed raise Error

       # If IP is allowed we don't do anything
       return None

#if sessionid provided, delete vsessionid
