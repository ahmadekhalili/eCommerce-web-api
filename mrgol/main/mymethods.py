from django.db.models import Max, Min

from decimal import Decimal
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from .models import Product, Post, Root



                           
def get_products(first_index=None, last_index=None, queryset=None):
    if queryset:
        return queryset.filter(visible=True).order_by('-available', '-id') 
    try:
        all_products_count = Product.objects.values_list('id').last()[0] - Product.objects.values_list('id').first()[0] + 1 #Product.objects.aggregate(product_counts=Max('id') - Min('id'))['product_counts'] + 1  #                    #.last run query like: SELECT "app1_product"."id"  FROM "app1_product"  ORDER BY "app1_product"."id" DESC  LIMIT 1               .first is like that but ASC instead of DESC       
        #instead up commend we have 2 way:  1- Product.objects.count()  that is heavy in running in huge amount of objects (tested in sqlite with 1.5m record)   2- #Product.objects.aggregate(product_counts=Max('id') - Min('id'))['product_counts']  this way  in performance is a bit more heavy than .last() and .first()  but use one query(.first .last use 2 query means connect 2 time to database), and also use MIN and MAX fun of database but .last .first use ORDER BY func of database (in sqlite ORDER BY is so fast maybe in another db be diffrent)  so .last .first is a bit faster but Max Min can be more logical.
        #we must havent eny id deleting in this project (and we havent)
        if all_products_count < last_index:
            return Product.objects.filter(visible=True).order_by('-available', '-id')
        else:                                                                                  #we have enough product in our db
            return Product.objects.filter(visible=True).order_by('-available', '-id')[first_index:last_index]        #dont have different beetwen Product.objects.filter(visible=True).order_by('-available', '-id')[first_index:last_index]   or    Product.objects.filter(id__in=list(range(first_index:last_index)), visible=True).order_by('-available', '-id')   they run same query in db.
        #we can use Product.objects.filter(id__in=ips, visible=True) but reverse is a bit faster(tested in sqlite with 1.5m record for retrive 100 object) it is more clear and breaf (dont need  list(range(min_ip, max_ip))) .....   and most important reason: reverse automaticly retrieve other objects if first objects havent our conditions(visible=True)  means if in Product.objects.filter(visible=True).reverse().order_by('id')[:5] we have two object with visible=False  in last 5 objects,  this commend will automaticly will go and retrive two other objects from next objects availabe. and if isnt find at all dont raise error and return founded objects,    query by indexed field(id) with an unindexed field (visible) dont affect speed significant(describe complete in:django/database.py/index)
    except:                                                #when we have no eny products.
        return []


            
def get_posts(first_index=None, last_index=None, queryset=None):
    if queryset:
        return queryset.filter(visible=True).order_by('-id')
    try:
        all_products_count = Post.objects.values_list('id').last()[0] - Post.objects.values_list('id').first()[0] + 1                    #.last run query like: #this line run this query: SELECT "app1_product"."id"  FROM "app1_product"  ORDER BY "app1_product"."id" DESC  LIMIT 1               .first is like that but ASC instead of DESC       
        #instead up commend we have 2 way:  1- Product.objects.count()  that is heave in huge amount of objects (tested in sqlite with 1.5m record)   2- #Product.objects.aggregate(product_counts=Max('id') - Min('id'))['product_counts']  this way  in performance is a bit more haveavy than .last() and .first()  but use one query(.first .last use 2 query means connect 2 time to database), and also use MIN and MAX fun of database but .last .first use ORDER BY func of database (in sqlite ORDER BY is so fast maybe in another db be diffrent)  so .last .first is a bit faster but Max Min can be more logical.
        if all_products_count < last_index:
            return Post.objects.filter(visible=True).order_by('-id')
        else:                                                                                  #we have enough product in our db
            return Post.objects.filter(visible=True).order_by('-id')[first_index:last_index] #we can use Product.objects.filter(id__in=ips, visible=True) but reverse is a bit faster(tested in sqlite with 1.5m record for retrive 100 object) is is more clear and breaf (dont need  list(range(min_ip, max_ip))) .....   and most important reason: reverse automaticly retrieve other objects if first objects havnt our conditions(visible=True)  means if in Product.objects.filter(visible=True).reverse().order_by('id')[:5] we have two object with visible=False  in last 5 objects,  this commend will automaticly will go and retrive two other objects from next objects availabe. and if isnt find at all dont raise error and return founded objects,    query by indexed field(id) with an unindexed field (visible) dont affect speed significant(describe complete in:django/database.py/index)
    except:
        return []     



'''
def childest_root(root, childs=[]):                 
    for child_root in root.root_childs.all():
        childs.append(childest_root(child_root))
    return root
def get_childs_and_root(root, return_self=True):                    
    childs = childest_root(root)
    if return_self:
        return [*childs, root]
    return childs
'''


def get_root_and_fathers(root):                    
    root_and_fathers = [root]
    for i in range(root.level-1):
        root = root.father_root
        if root:
            root_and_fathers += [root]
    return root_and_fathers



def get_posts_products_by_root(root):   
    if root.level < Root._meta.get_field('level').validators[1].limit_value:
        children_root_ids = list(filter(None, root.all_childes_id.split(',')))           #why we used filter? root.all_childes_id.split(',') may return: [''] that raise error in statements like  filter(in__in=['']) so we ez remove blank str of list by filter.
        children_root_ids = [root.id] + children_root_ids
    else:
        children_root_ids = [root.id]
    if root.post_product == 'product':
        return get_products(queryset=Product.objects.filter(root__id__in=children_root_ids))
    else:
        return get_posts(queryset=Post.objects.filter(root__id__in=children_root_ids) )       




class PostDispatchPrice:                       #weight in gram, and length in cm.
    def __init__(self, weight, dimensions):    #weight str, dimensions is like ["20,20,15", "30,25,20"]
        self.weight = weight
        self.dimensions = dimensions
        post_cartons_dimensions = {'1': [15, 10, 10], '2': [20, 15, 10], '3': [20, 20, 15], '4': [30, 20, 20], '5': [35, 25, 20], '6': [45, 25, 20], '7': [40, 30, 25], '8': [45, 40, 30], '9': [55, 45, 35]}

    @property
    def carton_size(self):
        post_cartons_volumes = {'1': 1500, '2': 3000, '3': 6000, '4': 12000, '5': 17500, '6': 22500, '7': 30000, '8': 54000, '9': 86625}
        goods_volume = 0                 #in cm3(cm*cm*cm)
        for size_str in self.dimensions:
            L = [int(i) for i in size_str.split(',')]
            goods_volume += L[0] * L[1] * L[2]
        for volume in post_cartons_volumes:
            if volume in ['4', '6', '7', '9']:                #we limited post cartons to only 4 size ('4', '6', '7', '9')
                if goods_volume < post_cartons_volumes[volume]:
                    return volume
                
    def get_price(self, from_state, from_town, to_state, to_town):                       #from_state and others is str (like '1')
        CIPHERS = ('DEFAULT:!DH')
        class DESAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = create_urllib3_context(ciphers=CIPHERS)
                kwargs['ssl_context'] = context
                return super(DESAdapter, self).init_poolmanager(*args, **kwargs)
            def proxy_manager_for(self, *args, **kwargs):
                context = create_urllib3_context(ciphers=CIPHERS)
                kwargs['ssl_context'] = context
                return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)
        session = requests.Session()
        session.mount('https://parcelprice.post.ir', DESAdapter())
        
        data1 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "",
                 "__VIEWSTATE": "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htqv2YTYp9iv2LQI2KjZhtmK2YYK2KjZiNiq2KfZhhDYqNmI2KrYs9mI2KfZhtinFtio2YjYsdqv2YrZhtin2YHYp9iz2Ygf2KjZiNiz2YbZiiDZiCDZh9ix2LLZhyDar9mI2YrZhgzYqNmI2YTZitmI2YoO2KjZitmE2KfYsdmI2LMQ2b7Yp9ix2Kfar9mI2KbZhwzZvtin2YbYp9mF2KcO2b7Yp9qp2LPYqtin2YYM2b7Ysdiq2LrYp9mEBtm+2LHZiA3ZvtmE2Yog2YbYstmKEtiq2KfYrNmK2qnYs9iq2KfZhhDYqtin2YbYstin2YbZitinDNiq2KfZitmE2YbYrwzYqtin2YrZiNin2YYe2KrYsdmK2YbZitiv2KfYr9mI2KrZiNio2KfaqdmIEtiq2LHaqdmF2YbYs9iq2KfZhgrYqtix2qnZitmHCtiq2Yjar9mI2YYI2KrZiNmG2LMK2KrZiNmG2q/YpwzYqtmI2YjYp9mE2YgT2KrZitmF2YjYsSDYtNix2YLZihDYrNin2YXYp9im2YraqdinE9is2KjZhCDYp9mE2LfYp9ix2YIV2KzYstin2YrYsSDYotmG2KrZitmEF9is2LLYp9mK2LEg2LPZhNmK2YXYp9mGDNis2YrYqNmI2KrZigbahtin2K8G2obZitmGBNqG2qkO2K/Yp9mG2YXYp9ix2qkO2K/ZiNmF2YrZhtmK2qkQ2K/ZiNmF2YrZhtmK2qnZhgzYsdmI2KfZhtiv2KcK2LHZiNiz2YrZhwzYsdmI2YXYp9mG2YoI2LLYptmK2LEM2LLYp9mF2KjZitinDtiy2YrZhdio2KfZiNmHCNqY2KfZvtmGDtiz2KfYptmI2KrZhdmHEdiz2KfYrdmE4oCM2LnYp9isFdiz2KfZhdmI2KfZiiDYutix2KjZihDYs9ix2YrZhNin2YbaqdinE9iz2YYg2b7YsdmI2YXZitqv2YgP2LPZhiDZhNmI2KbZitizDdiz2YYg2YbZvtin2YQL2LPZhiDZh9mE2YYT2LPZhiDaqdix2YrYs9iq2YjZgQ7Ys9mG2q/Yp9m+2YjYsQrYs9mG2q/Yp9mECNiz2YjYptivCtiz2YjYptmK2LMS2LPZiNin2YrYstmK2YTZhtivCtiz2YjYr9in2YYO2LPZiNix2YrZhtin2YUK2LPZiNix2YrZhwzYs9mI2YXYp9mE2YoQ2LPZitix2KfZhNim2YjZhgjYs9mK2LTZhAjYtNmK2YTZig7Ytdix2KjYs9iq2KfZhgjYudix2KfZgg7Yudix2KjYs9iq2KfZhgjYudmF2KfZhgbYutmG2KcM2YHYsdin2YbYs9mHDNmB2YbZhNin2YbYrwjZgdmK2KzZig7ZgdmK2YTZitm+2YrZhgjZgtio2LHYsxLZgtix2YLZitiy2LPYqtin2YYQ2YLYstin2YLYs9iq2KfZhgbZgti32LEK2q/Yp9io2YjZhgzar9in2YXYqNmK2KcO2q/Ysdin2YbYp9iv2KcO2q/Ysdis2LPYqtin2YYQ2q/ZiNin2KrZhdin2YTYpxDar9mI2KfYr9in2YTZiNm+Ctqv2YjZitin2YYZ2q/ZiNmK2KfZhuKAjNmB2LHYp9mG2LPZhwjar9mK2YbZhxnar9mK2YbZh+KAjNin2LPYqtmI2KfZitmKF9qv2YrZhtmH4oCM2KjZitiz2KfYptmICtmE2KfYptmI2LMK2YTYqNmG2KfZhgrZhNiq2YjZhtmKCtmE2LPZiNiq2YgM2YTZh9iz2KrYp9mGFNmE2Yjaqdiy2KfZhdio2YjYsdqvDNmE2YrYqNix2YrYpwjZhNmK2KjZig7ZhNmK2KrZiNin2YbZihfZhNmK2K7YqtmGINin2LTYqtin2YrZhhTZhdin2K/Yp9qv2KfYs9qp2KfYsRDZhdin2LHYqtmK2YbZitqpDNmF2KfZhNin2YjZigjZhdin2YTYqgzZhdin2YTYr9mK2YgK2YXYp9mE2LLZigjZhdin2YTZigzZhdin2qnYp9im2YgQ2YXYrNin2LHYs9iq2KfZhgrZhdix2Kfaqdi0BtmF2LXYsRDZhdi62YjZhNiz2KrYp9mGDtmF2YLYr9mI2YbZitmHENmF2YjYsdmK2KrYp9mG2YoK2YXZiNix2YrYsxDZhdmI2LLYp9mF2KjZitqpDtmF2YjZhNiv2KfZiNmKDNmF2YjZhtin2qnZiA7ZhdmI2YbYqtix2KfYqhjZhdmK2KfZhtmF2KfYsSjYqNix2YXZhykK2YXaqdiy2YraqQjZhtin2LHZiA7Zhtin2YXZitio2YrYpwjZhtm+2KfZhAjZhtix2YjamAjZhtmK2KzYsQzZhtmK2KzYsdmK2YcQ2YbZitmI2LLZitmE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",
                  "__EVENTVALIDATION": "/wEWGwL2gPj1DwKa78W2DwK3792fCgKi79mfCgLixem4DQKAy5njBQLugq82Apbs76AOAtiWlokLAvTEvGMC75LX6QkC8JLX6QkC8ZLX6QkC8pLX6QkC85LX6QkC9JLX6QkC9ZLX6QkC9pLX6QkC55LX6QkC6JLX6QkC8JKX6gkC8JKb6gkCzs262AwCn4j0wQ8Cn4jcmw0CteHziQoC7N2XU2cEmlx9IBG5LlhNWRuVZovt1Slp",
                  "g1": "rdoEMS", "g2": "rdoPackage", "txtWeight": self.weight, "cbopackageSize": self.carton_size,
                  "g4": "rdoSPS22", "btnnext": "مرحله بعد"}    
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data1)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        #g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri), but dont differrent in price at all, so we dont use "rdoCity".
        data2_2 = {"__EVENTTARGET": "cboFromState", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": "1", "cboToState": ""}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_2)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']
        
        data2_4 = {"__EVENTTARGET": "cboToState", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_4)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']
        
        data2_5 = {"__EVENTTARGET": "cboToCity", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state, "cboToCity": to_town}
        form2 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_5)
        soup = BeautifulSoup(form2.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        data2_6 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "g3": "rdoBetweenCity", "tlsDropDown": "0", "btnnext": "مرحله بعد",
                   "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation, "cboFromState": from_state, "cboFromCity": from_town, "cboToState": to_state, "cboToCity": to_town}#g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri) not for rdoCity you must not put cboToState and cboToCity 
        form3 = session.post('https://parcelprice.post.ir/default.aspx', data=data2_6)
        soup = BeautifulSoup(form3.content.decode('UTF-8'), 'html.parser')
        str_viewstate = soup.find('input', id='__VIEWSTATE')['value']
        str_eventvalidation = soup.find('input', id='__EVENTVALIDATION')['value']

        data3 = {"__EVENTTARGET": "", "__EVENTARGUMENT": "", "__LASTFOCUS": "", "cboInsurType": "1", "DropDown_extra": "0", "btnnext": "مرحله بعد",
                 "__VIEWSTATE": str_viewstate, "__EVENTVALIDATION": str_eventvalidation}                                                                     #g3 can be: "rdoCity"(shahri) or "rdoBetweenCity"(beinshahri) not for rdoCity you must not put cboToState and cboToCity 
        form4 = session.post('https://parcelprice.post.ir/default.aspx', data=data3)
        soup = BeautifulSoup(form4.content.decode('UTF-8'), 'html.parser')
        
        price = soup.find('font', face="PostFont", color="Red", size="5").get_text()
        price = ''.join(price[:-1].split(','))     #price is like: '199,545', we conver rial to toman (price[:-1])
        return Decimal(price)




class make_next:                             #for adding next to list you shold use iter like:  list_with_next = iter(L) but for using that you should call like: next(list_with_next) or list_with_next.__init__() and you cant next of use list_with_next in template like next(list_with_next) or list_with_next.__next__ or list_with_next.__init__() is error you must define simple method as def next(self) insinde list_with_next for using intemplate like: list_with_next.next
    def __init__(self, list):
        self.list = iter(list)
    def next(self):
        try:                                                
            nex = next(self.list)
        except:                            #if we input blank list in make_next like:   ob = make_next([])  now ob.next or ob.next()  dont raise error and return blank list instead or loop more than len(L) like: L=[1,2,3] ob=make_next(L) now [ob.next() for i in range(30}] doesnt raise error and return blank list instead.                           
            nex = []
        return nex


