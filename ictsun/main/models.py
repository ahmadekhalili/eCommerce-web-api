from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from datetime import datetime

import os
import jdatetime

from .model_methods import set_levels_afterthis_all_childes_id, update_product_stock
from users.models import User
# note1: serializers.py  translation.py  forms.py  admin/save_to_mongo should change after changes models.py
# note2: related objects of Product or Post (etc. Brand, Category, ...) you have to apply changes to it's serialisers like ProductListSerializer, ProductDetailMongoSerializer and mongo product/post saving (in admin.py) if required.


group_choices = [(key, str(key)) for key in range(1, 11)]
genre_choices = [(_('attribute'), 'attribute'), (_('filter'), 'filter'), (_('both'), 'both')]
symbole_choices = [('None', 'None'), (_('icon'), 'icon'), (_('color'), 'color')]  # None has default translation
class Filter(models.Model):
    group = models.PositiveIntegerField(_('group'), choices=group_choices)
    name = models.CharField(_('name'), unique=True, max_length=25)        # name for quering.
    verbose_name = models.CharField(_('verbose name'), max_length=25)     # name for showing. (to user).  for example you have two filter with names: "system amel goshi", "system amele laptop" but both of them have 'system amel' as verbose name.
    genre = models.CharField(_('genre'), max_length=25, choices=genre_choices)
    symbole = models.CharField(_('symbole'), max_length=25, choices=symbole_choices)
    #filter_attributes
    #category_set

    class Meta:
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')

    def __str__(self):
        return str(self.name)




class Brand(models.Model):
    name = models.CharField(_('name'), max_length=25, blank=True)
    slug = models.SlugField(_('slug'), allow_unicode=True, null=True, blank=True, unique=True, db_index=False)
    #category_set

    class Meta:
        verbose_name = _('brand')
        verbose_name_plural = _('brands')

    def __str__(self):
        return self.name




class Category(models.Model):                                  #note: supose roor2 object,  category2.father_category determine father of category2 and category2.child_categories is list of category2's childer,  category with level=1 can has eny father!
    name = models.CharField(_('name'), unique=True, max_length=50)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)
    level = models.PositiveSmallIntegerField(_('level'), default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])        #important: in main/views/ProductCategoryList & ProductDetail and in main/methods/get_posts_products_by_category   we used MaxValueValidator with its posation in validator, so validator[1] must be MaxValueValidator otherwise will raise error.
    father_category = models.ForeignKey('self', related_name='child_categories', related_query_name='childs', null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('father category'))        #if category.level>1 will force to filling this field.
    levels_afterthis = models.PositiveSmallIntegerField(default=0, blank=True)                         #in field neshan midahad chand sath farzand darad in pedar, masalam: <category(1) digital>,  <category(2) mobail>,  <category(3) samsung> farz konid mobail pedare samsung,  digital pedare mobail ast(<category(1) digital>.level=1,  <category(2) mobail>.level=2,  <category(3) samsung>.level=3)   . bala sare digital dar in mesal 2 sath farzand mibashad( mobail va samsung pas <category(1) digital>.levels_afterthis = 2   va <category(2) mobail>.levels_afterthis=1  va <category(3) samsung>.levels_afterthis=0
    previous_father_id = models.PositiveSmallIntegerField(null=True, blank=True)                         #supose you change category.father_category, we cant understant prevouse father was what in Category.save(ony new edited father_category is visible) so we added this field
    all_childes_id = models.TextField(default='', blank=True)                      #list all chiles of that object in this structure: "1,2,3,4"    if this field name was chiles_id maybe raise problem with related_query_name of father_category or other.
    post_product = models.CharField(_('post or product'), max_length=10, default='product')      #this should be radio button in admin panel.
    filters = models.ManyToManyField(Filter, through='Category_Filters', blank=True, verbose_name=_('filters'))
    brands = models.ManyToManyField(Brand, through='Category_Brands', blank=True, verbose_name=_('brands'))
    #child_categories
    #product_set

    class Meta:
        ordering = ('level',)                    #main/views/ProductList/sidebarcategory_link affect order of Category.  ('level', '-father_category_id') '-father_category_id' make in ProductCategoryList products order from last to first (reverse order) -father_category_id  will make childs with same father be in together. and '-' will make decending order like ordering django admin for 'order by ids' means lower ids will go to down.(tested)
        verbose_name = _('category')
        verbose_name_plural = _('categories')
    
    def __str__(self):
        return str(self.level) + ' - ' + self.name
    
    def clean_fields(self, exclude=None):
        if self.level:                                                   #why we put this line?  answer: in adding category, self.father_category is None and raise erro if: 'self.level > 1'
            if self.level > 1 and not self.father_category:                  #other conditions will control by form eazy (for example if self.level==1 father_category must be None)
                raise ValidationError({'father_category': [_('This field is required for level more than 1.')]})
        super().clean_fields(exclude=None)

    def save(self, *args, **kwargs):
        previous_father_queryset = Category.objects.filter(id=self.previous_father_id).select_related('father_category__'*4+'father_category') if self.previous_father_id else None
        self.previous_father_id = self.father_category_id if self.father_category_id else None
        super().save(*args, **kwargs)
        category_queryset = Category.objects.filter(id=self.id).select_related('father_category__'*5+'father_category')    #instead using 6 logn father_category we used more breafer format!
        
        categories_before_join, categories_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, category_queryset, Category._meta.get_field('level').validators[1].limit_value)
        Category.objects.bulk_update(categories_before_join, ['levels_afterthis', 'all_childes_id']) if categories_before_join else None
        Category.objects.bulk_update(categories_after_join, ['levels_afterthis', 'all_childes_id']) if categories_after_join else None

    def delete(self, using=None, keep_parents=False):
        id = self.id
        dell = super().delete(using, keep_parents)
        previous_father_queryset = Category.objects.filter(id=self.father_category_id).select_related('father_category__'*5+'father_category') if self.father_category_id else None
        self.id, self.father_category, self.father_category_id = id, None, None                                               #we need self.id in list_childes_id
        categories_before_join, categories_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, [self], Category._meta.get_field('level').validators[1].limit_value, delete=True)
        Category.objects.bulk_update(categories_before_join, ['levels_afterthis', 'all_childes_id']) if categories_before_join else None
        return dell


class Category_Filters(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_('category'))
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE, verbose_name=_('filter'))

    class Meta:
        verbose_name = _('Category Filter')
        verbose_name_plural = _('Category Filters')

    def __str__(self):
        return _('Category Filters') + str(self.id)

Category_Filters._meta.auto_created = True                        #if you dont put this you cant use filter_horizontal in admin.py for  Filter.categories or other manytomany fields that use Filter_Categories.


class Category_Brands(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_('category'))
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name=_('brand'))

    class Meta:
        verbose_name = _('Category Brand')
        verbose_name_plural = _('Category Brands')

    def __str__(self):
        return _('Category Brand') + str(self.id)

Category_Brands._meta.auto_created = True




class Filter_Attribute(models.Model):
    name = models.CharField(_('name'), max_length=25)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)
    symbole_value = models.CharField(_('symbole value'), max_length=255, blank=True)                  # if filter.symbole was 'icon' symbole_value have to be icon url and if was 'color', symbole_value have to be hash color
    filterr = models.ForeignKey(Filter, on_delete=models.CASCADE, related_name='filter_attributes', verbose_name=_('filter'))                 #filter is reserved name by python
    #product_set
    #product_filter_attributes_set
    #shopfilteritems

    class Meta:
        ordering = ('filterr',)
        verbose_name = _('Filter Attribute')
        verbose_name_plural = _('Filter Attributes')

    def __str__(self):
        return str(self.name)




class Rating(models.Model):                                                   #math operation of Rating will done in view. 
    submiters = models.PositiveIntegerField(_('submiters'), default=0)
    rate = models.DecimalField(_('rate'), max_digits=2, decimal_places=1, default='0')       # don't need add MaxValueValidator, rating of every product is created in Product.save() with controled value.

    class Meta:
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')

    def __str__(self):
        return str(self.rate)




class ProductManager(models.Manager):                             #we have two seperate way for creating an object,  .create( product.objects.create ) and .save( p=product(..) p.save() ), it is important for us in two way rating creation suported same.
    def create(self, *args, **kwargs):
        product = super().create(*args, **kwargs)
        if product.stock==0 or product.available==False:
            product.stock = 0
            product.available = False
        r = Rating.objects.create()
        product.rating = r
        product.save()
        return product

class Product(models.Model):                                     #.order_by('-available') shoud be done in views and in admin hasndy
    name = models.CharField(_('name'), max_length=150)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)             #default db_index of slug is True
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), validators=[MaxLengthValidator(160)], blank=True, default='')
    brief_description = models.TextField(_('brief description'), validators=[MaxLengthValidator(1000)], blank=True)
    detailed_description = models.TextField(_('detailed description'), blank=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default='0')    # for $ prices we need 2 decimal places like 19.99$ and for rial it's x.00 that should serialize to x    if default=0 (instead default='0') products with price=0 will saves in database as 0 instead '0.00' while all other prices are in two decimal format, this removes integrity and cause problems in like main/tests/test_add_to_session.
    available = models.BooleanField(_('available'), default=False, db_index=True)
    visible = models.BooleanField(_('visible'), default=True, db_index=True)                #we use visible for deleting an object, for deleting visible=False, in fact we must dont delete any product.
    created = models.DateTimeField(_('created date'), auto_now_add=True)
    updated = models.DateTimeField(_('updated date'), auto_now=True)
    stock = models.PositiveIntegerField(_('stock'), default=0)                        # important: stock before creating first shopfilteritem of product shoud be 0 otherwise it will sum with shopfilteritem.stock, example: supose we have product1.stock = 10  now after creating shopfilteritem1 with stock=12 product1.stock will be 10+12   (address: in ShopFilterItem.save and model_methods.py/update_product_stock
    weight = models.FloatField(_('weight'), null=True, blank=False)                   # weight is in gram and used in orders/methods/profile_order_detail/PostDispatchPrice  but if you dont specify weight in saving a product, it will be None and will ignore in PostDispatchPrice. its better null=True easier in creating products in tests.
    size = models.CharField(_('size'), max_length=25, blank=True)          # value should be in mm  and like '100,150,150'  this field seperate to 3 field in ProductAdminForm in __init__ and save func), also we use size in methods.PostDispatchPrice  to define which box size should choice for posting.
    rating = models.OneToOneField(Rating, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('rating'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('category'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('brand'))          # brand field as CharField is not logical and should be ForeignKey why? because for example in adding product1 we may add brand "nokia" and in second product2 add "Nokia". when products increased (supose more than 100) it will raise real problems
    filter_attributes = models.ManyToManyField(Filter_Attribute, through='Product_Filter_Attributes', blank=True, verbose_name=_('filter attributes'))
    #images                                                    backward relation field
    #image_icon_set
    #comment_set
    #product_filter_attributes_set
    #shopfilteritems
    ##order_items
    objects = ProductManager()

    class Meta:
        #default_permissions = ('add', 'change', 'delete', 'view')
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        create_Rating = True if not self.pk else False                                     #when you create new object like p = product(..)  p.save()   self.pk here is None
        self.available = False if self.stock < 1 else True                                 #self.available should always folow self.stock value not reverse, means if admin select stock=0 our availlable should be False, but puting availabe false cant make our stock=0, stock has priority and its logical.
        from main.signals import FillCategoryfilters_brands
        pre_product = Product.objects.get(id=self.id) if self.id else None
        FillCategoryfilters_brands.pre_category, FillCategoryfilters_brands.pre_brand_id = (pre_product.category, pre_product.brand_id) if pre_product else (None, None)
        super().save(*args, **kwargs)
        FillCategoryfilters_brands.category_brand_changed(self)
        if create_Rating:
            r = Rating.objects.create()
            self.rating = r
            self.save()


class Product_Filter_Attributes(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('product'))
    filter_attribute = models.ForeignKey(Filter_Attribute, on_delete=models.CASCADE, verbose_name=_('Filter Attribute'))

    class Meta:
        verbose_name = _('Product_Filter_Attribute')
        verbose_name_plural = _('Product_Filter_Attributes')

    def __str__(self):
        return _('Product_Filter_Attribute') + ' ' + str(self.id)

Product_Filter_Attributes._meta.auto_created = True

from main.signals import FillCategoryfilters_brands         # this cause "m2m_changed.connect(filter_attributes_changed, sender=Product.filter_attributes.through)" loads here. changing Category.brands Category.filters automatically related to several fields, one of them is product.filter_attributes, we collected all related fields to one class 'FillCategoryfilters_bradns to clearer structure and design.




class ShopFilterItem(models.Model):
    filter_attribute = models.ForeignKey(Filter_Attribute, on_delete=models.SET_NULL, null=True, verbose_name=_('filter attribute'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='shopfilteritems', verbose_name=_('product'))         #why we dont use ShopFilterItem as manytomany field in Product? because we want one object of ShopFilterItem only point to one product (supose one  object of ShopFilterItem as shopfilteritem_1 if thos shopfilteritem_1 point to several product instead one product, so eny changes on shopfilteritem_1 like decreasing shopfilteritem_1.price will affect on other products!!!!
    previous_stock = models.PositiveIntegerField(blank=True)
    stock = models.PositiveIntegerField(_('stock'))                                     # important: before creating first shopfilteritem for a product, product of that shopfilteritem should have stock=0 (shopfilteritem.product.stock=0) because shopfilteritem.sotck will assign to shopfilteritem.product.stock
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)            # product.price shoud be arbitrary for filling, but this no!!! (if you have shopfilteritem.price it is btter and more logical shopfilteritem.product.price be 0)
    available = models.BooleanField(_('available'), default=False, db_index=True)

    class Meta:
        ordering = ['-product']                                             # order shopfilteritem objects by field 'product_id' (foreignkey field in db). now order of shopfilteitems in same withs products
        verbose_name = _('shopfilteritem')
        verbose_name_plural = _('shopfilteritems')

    def save(self, *args, **kwargs):
        update_product_stock(self, self.product, saving=True)
        self.previous_stock = self.stock
        self.available = False if self.stock < 1 else True
        super().save(*args, **kwargs)

    def __str__(self):                                           # important: because we query to 2 another table in ShopFilterItem.str so its important to use query optimize when reading ShopFilterItem objects (like .select_related('product').select_related('filter_attribute')). example:    in ictsun\main\templatetags\admin\main\shopfilteritem\admin_list.py: cl.result_list.select_related('product').select_related('filter_attribute')     cl.result_list is objects of shopfilteritem will diplay in list_display of shopfilteritem.
        return self.product.name + ' - ' + self.filter_attribute.name if self.filter_attribute else super().__str__()         # in testing (like in cart.tests.ShopFilterItemCartTestCase) we create ShopFilterItem with least fields (without filter_attribute)



def icon_path_selector(instance, filename):                        #note: if you use method in upload_to, strftime ("%Y/%m/%d/") dont work and should provided manualy.
    if settings.IMAGES_PATH_TYPE == 'jalali':
        date = jdatetime.datetime.fromgregorian(date=datetime.now()).strftime('%Y %-m %-d').split()
    else:
        date = datetime.now().strftime('%Y %-m %-d').split()
    return f'{instance.path}_images/icons/{date[0]}/{date[1]}/{date[2]}/{filename}'  # instance.path == Image_icon.path

class Image_icon(models.Model):
    image = models.ImageField(_('image'), upload_to=icon_path_selector)
    alt = models.CharField(_('alt'), max_length=55, unique=True, null=True)    # alt should not be dublicate because we used alt instead image_icon id in def __str__(self)
    path = models.CharField(_('path'), max_length=20, default='products')      # "products" / "posts", ...
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('product'))

    class Meta:
        verbose_name = _('Image icon')
        verbose_name_plural = _('Image icones')

    def __str__(self):
        return self.alt if self.alt else self.image.path


def image_path_selector(instance, filename, path=None):                        #note: if you use method in upload_to, strftime ("%Y/%m/%d/") dont work and should provided manualy.
    if settings.IMAGES_PATH_TYPE == 'jalali':
        date = jdatetime.datetime.fromgregorian(date=datetime.now()).strftime('%Y %-m %-d').split()
    else:
        now = datetime.now()
        date = f"{now.year} {now.month} {now.day}".split()
    path = path or instance.path
    return os.path.join(f'{path}_images/{date[0]}/{date[1]}/{date[2]}/{filename}')


class Image(models.Model):
    image = models.ImageField(_('image'), upload_to=image_path_selector, blank=True, null=True)    # here save default size of image to prevent additional query to ImageSizes class.
    alt = models.CharField(_('alt'), max_length=55, unique=True, null=True)                    # alt should not be dublicate because we used alt instead image id in def __str__(self)
    path = models.CharField(_('path'), max_length=20, default='products')                  # "products" / "posts", ...
    # related_name='images' is required because uses in serializers.ProductDetailSerializer.images
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', null=True, verbose_name=_('product'))
    #imagesizes

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

    def __str__(self):
        try:
            name = self.product.name
        except:
            name = self.id
        return f'{name} - {self.alt}'


# here saves different sizes of Image model (except default size that saves in Image.image)
class ImageSizes(models.Model):
    image = models.ImageField(_('image'), blank=True, null=True)  # upload_to sets in __init__ dynamically
    alt = models.CharField(_('alt'), max_length=55, unique=True, null=True)
    size = models.CharField(_('size'), max_length=20)
    father = models.ForeignKey(Image, related_name='imagesizes', on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('image'))

    class Meta:
        verbose_name = _('Image size')
        verbose_name_plural = _('Images sizes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._meta.get_field('image').upload_to = lambda instance, filename: image_path_selector(instance, filename, path=self.father.path)

    def __str__(self):
        if '-' in self.alt:      # if alt has size, like: 'banana-240'
            return self.alt
        return f'{self.alt} {self.size}'


statuses = [('1', _('not checked')), ('2', _('confirmed')), ('3', _('not confirmed')), ('4', _('deleted'))]
class Comment(models.Model):
    name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(_('status'), default='1', max_length=1, choices=statuses)               # review site comments by admin and show comment in site if confirmed, '1' = confirmed     '2' = not checked(admin should check comment to confirm or not)      '3' = not confirmed(admin can confirm afters if want)    '4' = deleted
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)           # published_date should translate in front. for example comment1 (1390/1/27) can translate like: comment1 (2016/4/16)
    content = models.TextField(_('content'), validators=[MaxLengthValidator(500)])
    post = models.CharField(max_length=100, blank=True)  # stores ObjectID, foreignkey implementation of mongodb
    author = models.ForeignKey(User, related_name='written_comments', related_query_name='comments_author', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    reviewer = models.ForeignKey(User, related_name='reviewed_comments', related_query_name='comments_reviewer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('reviewer'))        # reviewer is last admin changed comment.status
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('product'))
    # replies

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return _('Comment') + ' ' + str(self.id)


class Reply(models.Model):
    name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(_('status'), default='1', max_length=1, choices=statuses)
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)
    content = models.TextField(_('content'), validators=[MaxLengthValidator(500)])
    author = models.ForeignKey(User, related_name='written_replies', related_query_name='reply_author', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    reviewer = models.ForeignKey(User, related_name='reviewed_replies', related_query_name='reply_reviewer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('reviewer'))
    comment = models.ForeignKey(Comment, related_name='replies', related_query_name='replies', on_delete=models.SET_NULL, null=True, verbose_name=_('comment'))

    class Meta:
        verbose_name = _('Reply')
        verbose_name_plural = _('Replies')

    def __str__(self):
        return _('Reply') + ' ' + str(self.id) + ',' + _('Comment') + str(self.comment_id)


class State(models.Model):
    key = models.CharField(max_length=10, unique=True, verbose_name=_('key'))
    name = models.CharField(max_length=30, verbose_name=_('name'))
    #towns

    class Meta:
        verbose_name = _('State')
        verbose_name_plural = _('States')
        
    def __str__(self):
        return 'State' + ' ' + self.name


class Town(models.Model):
    key = models.CharField(max_length=10, unique=True, verbose_name=_('key'))
    name = models.CharField(max_length=30, verbose_name=_('name'))
    state = models.ForeignKey(State, to_field='key', related_name='towns', on_delete=models.SET_NULL, null=True, verbose_name=_('state'))
  
    class Meta:
        verbose_name = _('Town')
        verbose_name_plural = _('Towns')
        
    def __str__(self):
        return 'Town' + ' ' + self.name
