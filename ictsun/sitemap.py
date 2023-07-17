from django.conf import settings
from django.contrib.sites.models import Site

import xml.etree.ElementTree as ET

from main.methods import get_posts_products_by_category, get_page_count


def create_sitemap():  # this method runs in urls.py because there run only one time after running django (with scheduled time)
    # create tag <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"> for writing on sitemap.xml file
    urlset = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')

    try:
        domain = Site.objects.get_current()
    except:
        domain = '127.0.0.1:8000'

    url_body = f'{settings.DEFAULT_SCHEME}://{domain}'    # is like: 'http://ictsun.ir'

    
    product_pages = list(range(1, get_page_count(Product, settings.PRODUCT_STEP) + 1))    # from 1 to n
    
    product_categories = Category.objects.filter(post_product='product')
    post_pk_slug = Post.objects.filter(visible=True).values_list('id', 'slug')
    product_pk_slug = Product.filter(visible=True).values_list('id', 'slug')
    sitemap = []
    sitemap += [{'loc': f'{url_body}/posts/'}]
    sitemap += [{'loc': f'{url_body}/products/'}]
    sitemap += [{'loc': f'{url_body}/posts/categories/'}]
    sitemap += [{'loc': f'{url_body}/products/categories/'}]

    all_posts = list(Post.objects.filter(visible=True))
    all_products = list(Product.objects.filter(visible=True))

    post_pages = list(range(1, get_page_count(all_posts, settings.POST_STEP) + 1))    # from 1 to n
    sitemap += [{'loc': f'{url_body}/posts/{page}/'} for page in post_pages]

    post_categories = Category.objects.filter(post_product='post').values_list('id', flat=True)   # is like: [1,2,3,7,8,9,10]
    for category in post_categories:
        posts_of_cats = [post for post in all_posts if post.category_id in [category.id] + list(filter(None, category.all_childes_id.split(',')))]
        page_count = get_page_count(posts_of_cats, settings.POST_STEP)
        sitemap += [{'loc': f'{url_body}/posts/{page}/<category>/'} for page in list(range(1, page_count+1))]

    product_pages = list(range(1, get_page_count(all_products, settings.PRODUCT_STEP) + 1))    # from 1 to n
    sitemap += [{'loc': f'{url_body}/products/{page}/'} for page in pages]

    product_categories = Category.objects.filter(post_product='product').values_list('id', flat=True)  # is like: [5,6,11,12]
    for category in product_categories:
        products_of_cats = [product for product in all_products if product.category_id in [category.id] + list(filter(None, category.all_childes_id.split(',')))]
        page_count = get_page_count(products_of_cats, settings.PRODUCT_STEP)
        sitemap += [{'loc': f'{url_body}/products/{page}/<category>/'} for page in list(range(1, page_count+1))]

    sitemap += [{'loc': f'{url_body}/posts/detail/{post.id}/{post.slug}/', 'lastmod': str(post.date())} for post in all_posts]  # lastmod format should be str and like: 2023-07-15

    sitemap += [{'loc': f'{url_body}/products/detail/{product.id}/{product.slug}/', 'lastmod': str(product.date())} for product in all_products]

    sitemap += [{'loc': f'{url_body}/cart/'}]         # cart page view

    sitemap += [{'loc': f'{url_body}/orders/'}]       # shipping page (come from cart page to finalize order)

    sitemap += [{'loc': f'{url_body}/orders/orderitems/'}]

    sitemap += [{'loc': f'{url_body}/payment/verify/'}]      # only get or put method have meaning in sitemap, urls with only post method can't be in sitemap (like /payment/)

    # create write urls to sitemap.xml
    for block in sitemap:
        url = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url, 'loc')
        loc.text = block['loc']
        if block.get('lastmod'):
            lastmod = ET.SubElement(url, 'lastmod')
            lastmod.text = block['lastmod']
    file_tree = ET.ElementTree(urlset)
    ET.indent(file_tree, '  ')             # without this all of tag are in one big line, but with this every tag in new line with two space (standard structure)
    file_tree.write('sitemap.xml', encoding='utf-8', xml_declaration=True)  # two last parameter add <?xml version='1.0' encoding='utf-8'?> in first of sitemap.xml file
