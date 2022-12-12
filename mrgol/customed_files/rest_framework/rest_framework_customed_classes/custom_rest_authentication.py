from rest_framework.authentication import SessionAuthentication
from django.middleware.csrf import _does_token_match
from rest_framework import exceptions


class CustomSessionAuthentication(SessionAuthentication):            
    def enforce_csrf(self, request):
        if request.method == 'POST' or request.method == 'PUT':
            return None
            try:
                request_csrf_token = request.data['csrfmiddlewaretoken']
                csrf_token = request.COOKIES['csrftoken']                                     #puting like request.COOKIES.get will make running except TypeError when csrf_token or request_csrf_token is none.  except TypeError "unexpected value' should raise only when csrf_token or request_csrf_token have value but in failed type.
                bool_compared = _does_token_match(request_csrf_token, csrf_token)
                if bool_compared:
                    return None
                else:                                                                         #bool_compared = False
                    raise                                                                     #raise make runnin "except:"

            except AttributeError:                                                            #AttributeError error raises when attribute of a object is not definded, for example request is not attribute .data (djago request)
                raise exceptions.PermissionDenied({'CustomSessionAuthentication': 'maybe error accur because you are using django rquest, only rest rquest accepted'})
            except TypeError:                                                                 #this like run when puting value for _does_token_match isnt char for example: csrf_token = {...}              
                raise exceptions.PermissionDenied({'CustomSessionAuthentication': 'CSRF unexpected value'})
            except KeyError:                                                                  #request.data['csrfmiddlewaretoken'] or request.COOKIES['csrftoken'] not provided.                    
                raise exceptions.PermissionDenied({'CustomSessionAuthentication': 'CSRF not provided'})                       #this line run when request.data['csrfmiddlewaretoken'] or request.COOKIES['csrftoken']  arent provided.
            except:                                                                           #bool_compared = False     
                raise exceptions.PermissionDenied({'CustomSessionAuthentication': 'CSRF provided, but Failed'})
