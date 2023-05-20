from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files import File
from django.db import models

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

import io
import os
import ast
from datetime import datetime
from PIL import Image as PilImage
from djongo import models as djongo_models
from ckeditor_uploader.fields import RichTextUploadingField

from .model_methods import set_levels_afterthis_all_childes_id, update_product_stock
from customed_files.django.classes import model_fields_custom
from customed_files.date_convertor import MiladiToShamsi
from users.models import User
# note1: changing classes places may raise error when creating tables(makemigrations), for example changing Content with Post will raise error(Content use Post in its field and shuld be definded after Post)
# note2: if you add or remove a field, you have to apply it in translation.py 'fields' if was required.
# note3: if you make changes Product or it's related objects (etc. Brand, Category, ...) you have to apply changes to it's serialisers like ProductListSerializer, ProductDetailMongoSerializer and mongo product saving (in admin.py) if required.
# note4: if you make changes in a model, you have to apply changes to it's serializers if needed.


group_choices = [(key, str(key)) for key in range(1, 11)]
class Filter(models.Model):
    group = models.PositiveIntegerField(_('group'), choices=group_choices)
    name = models.CharField(_('name'), unique=True, max_length=25)        # name for quering.
    verbose_name = models.CharField(_('verbose name'), max_length=25)     # name for showing. (to user).  for example you have two filter with names: "system amel goshi", "system amele laptop" but both of them have 'system amel' as verbose name.
    #selling = models.BooleanField(_('selling filter'), default=False)
    #filter_attributes
    #category_set

    class Meta:
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')

    def __str__(self):
        return str(self.name)




class Brand(models.Model):
    name = models.CharField(_('name'), max_length=25, null=True, blank=True)
    slug = models.SlugField(_('slug'), allow_unicode=True, null=True, blank=True, db_index=False)
    #category_set

    class Meta:
        verbose_name = _('brand')
        verbose_name_plural = _('brands')

    def __str__(self):
        return self.name




class Category(models.Model):                                  #note: supose roor2 object,  category2.father_category determine father of category2 and category2.child_categories is list of category2's childer,  category with level=1 can has eny father!
    name = models.CharField(_('name'), unique=True, max_length=50)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)
    level = models.PositiveSmallIntegerField(_('level'), default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])        #important: in main/views/ProductCategoryList & ProductDetail and in main/mymethods/get_posts_products_by_category   we used MaxValueValidator with its posation in validator, so validator[1] must be MaxValueValidator otherwise will raise error.
    father_category = models.ForeignKey('self', related_name='child_categories', related_query_name='childs', null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('father category'))        #if category.level>1 will force to filling this field.
    levels_afterthis = models.PositiveSmallIntegerField(default=0, blank=True)                         #in field neshan midahad chand sath farzand darad in pedar, masalam: <category(1) digital>,  <category(2) mobail>,  <category(3) samsung> farz konid mobail pedare samsung,  digital pedare mobail ast(<category(1) digital>.level=1,  <category(2) mobail>.level=2,  <category(3) samsung>.level=3)   . bala sare digital dar in mesal 2 sath farzand mibashad( mobail va samsung pas <category(1) digital>.levels_afterthis = 2   va <category(2) mobail>.levels_afterthis=1  va <category(3) samsung>.levels_afterthis=0
    previous_father_id = models.PositiveSmallIntegerField(null=True, blank=True)                         #supose you change category.father_category, we cant understant prevouse father was what in Category.save(ony new edited father_category is visible) so we added this field
    filters = models.ManyToManyField(Filter, through='Category_Filters', blank=True, verbose_name=_('filters'))
    brands = models.ManyToManyField(Brand, through='Category_Brands', blank=True, verbose_name=_('brands'))
    all_childes_id = models.TextField(default='', blank=True)                      #list all chiles of that object in this structure: "1,2,3,4"    if this field name was chiles_id maybe raise problem with related_query_name of father_category or other.
    post_product = models.CharField(_('post or product'), max_length=10, default='product')      #this should be radio button in admin panel.
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




def path_selector(instance, filename):                        #note: if you use method in upload_to, strftime ("%Y/%m/%d/") dont work and should provided manualy.
    now = datetime.now()
    y, m, d = MiladiToShamsi(now.year, now.month, now.day).result()
    return f'{instance.path}_images/icons/{y}/{m}/{d}/{filename}'                         

class Image_icon(models.Model):
    image = models.FileField(_('image'), upload_to=path_selector)
    alt = models.CharField(_('alt'), max_length=55, unique=True, null=True, default='')    # alt should not be dublicate because we used alt instead image_icon id in def __str__(self)
    path = models.CharField(_('path'), max_length=20, default='products')                  # can be value like: "products"  or  "posts" ....    

    class Meta:
        verbose_name = _('Image icon')
        verbose_name_plural = _('Image icones')

    def __str__(self):
        return self.alt

    def save(self, *args, **kwargs):
        image_icon = super().save(*args, **kwargs)       
        image = image_icon.image if image_icon else self.image              #only in creating new Image_icon, image_icon is not None, in editing we must use self (image_icon is None).
        if image:
            file = PilImage.open(image.path)
            resized = file.resize((200, 200))
            resized.save(image.path)


class Post(models.Model):
    title = models.CharField(_('title'), max_length=60)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)   #default db_index=True
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), validators=[MaxLengthValidator(160)], blank=True, default='')    
    brief_description = models.TextField(_('brief description'), validators=[MaxLengthValidator(1000)])
    detailed_description = RichTextUploadingField(_('detailed description'), blank=True)
    visible = models.BooleanField(_('delete'), default=True)
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)
    image_icon = models.OneToOneField(Image_icon, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('image icon'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('category'))
    author = models.ForeignKey(User, related_name='written_posts', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    #comment_set                                                   #backward relation

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        represantaion = self.title[:30]+'...' if len(self.title) > 40 else self.title[:30]
        return represantaion




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
    name = models.CharField(_('name'), max_length=60)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)             #default db_index of slug is True
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), validators=[MaxLengthValidator(160)], blank=True, default='')
    brief_description = models.TextField(_('brief description'), validators=[MaxLengthValidator(1000)])
    detailed_description = RichTextUploadingField(_('detailed description'), blank=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default='0')    # for $ prices we need 2 decimal places like 19.99$ and for rial it's x.00 that should serialize to x    if default=0 (instead default='0') products with price=0 will saves in database as 0 instead '0.00' while all other prices are in two decimal format, this removes integrity and cause problems in like main/tests/test_add_to_session.
    available = models.BooleanField(_('available'), default=False, db_index=True)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)                #we use visible for deleting an object, for deleting visible=False, in fact we must dont delete any product.    
    created = models.DateTimeField(_('created date'), auto_now_add=True)
    updated = models.DateTimeField(_('updated date'), auto_now=True)
    filter_attributes = models.ManyToManyField(Filter_Attribute, through='Product_Filter_Attributes', blank=True, verbose_name=_('filter attributes'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('category'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('brand'))          # brand field as CharField is not logical and should be ForeignKey why? because for example in adding product1 we may add brand "nokia" and in second product2 add "Nokia". when products increased (supose more than 100) it will raise real problems
    image_icon = models.OneToOneField(Image_icon, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('image icon'))     #in home page(page that list of product shown) dont query product.image_set.all()[0] for showing one image of product, instead query product.image_icon   (more fster)
    rating = models.OneToOneField(Rating, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('rating'))
    stock = models.PositiveIntegerField(_('stock'), default=0)                        # important: stock before creating first shopfilteritem of product shoud be 0 otherwise it will sum with shopfilteritem.stock, example: supose we have product1.stock = 10  now after creating shopfilteritem1 with stock=12 product1.stock will be 10+12   (address: in ShopFilterItem.save and model_methods.py/update_product_stock
    weight = models.FloatField(_('weight'), null=True, blank=False)                   # weight is in gram and used in orders/mymethods/profile_order_detail/PostDispatchPrice  but if you dont specify weight in saving a product, it will be None and will ignore in PostDispatchPrice. its better null=True easier in creating products in tests.
    size = models.CharField(_('size'), max_length=25, blank=True)          # value should be in mm  and like '100,150,150'  this field seperate to 3 field in ProductForm in __init__ and save func), also we use size in mymethods.PostDispatchPrice  to define which box size should choice for posting.
    #image_set                                                    backward relation field
    #comment_set
    #product_filter_attributes_set
    #smallimages
    #shopfilteritems
    ##order_items
    objects = ProductManager()

    class Meta:
        #default_permissions =  ('add', 'change', 'delete', 'view')
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




class MDetailProduct(djongo_models.Model):
    id = djongo_models.IntegerField(blank=False, null=False, primary_key=True)
    json = djongo_models.JSONField()
    #name = djongo_models.CharField(_('name'), max_length=60)
    #slug = djongo_models.CharField(_('slug'), max_length=60)
    #meta_title = djongo_models.CharField(_('meta title'), max_length=60, blank=True, default='')
    #meta_description = djongo_models.TextField(_('meta description'), validators=[MaxLengthValidator(160)], blank=True, default='')
    #brief_description = djongo_models.TextField(_('brief description'), validators=[MaxLengthValidator(1000)])
    #detailed_description = RichTextUploadingField(_('detailed description'), blank=True)
    #price = djongo_models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=0) 
    #available = djongo_models.BooleanField(_('available'), default=False)
    objects = djongo_models.DjongoManager()

    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __str__(self):
        try:
            return self.json['name']                      # self.json.get   raise error.
        except:
            return 'nameless'                             # return None can't accept (error)




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

    def __str__(self):                                           # important: because we query to 2 another table in ShopFilterItem.str so its important to use query optimize when reading ShopFilterItem objects (like .select_related('product').select_related('filter_attribute')). example:    in mrgol\main\templatetags\admin\main\shopfilteritem\admin_list.py: cl.result_list.select_related('product').select_related('filter_attribute')     cl.result_list is objects of shopfilteritem will diplay in list_display of shopfilteritem.
        return self.product.name + ' - ' + self.filter_attribute.name if self.filter_attribute else super().__str__()         # in testing (like in cart.tests.ShopFilterItemCartTestCase) we create ShopFilterItem with least fields (without filter_attribute)




class Image(models.Model):
    image = models.ImageField(_('image'), upload_to='products_images/%Y/%m/%d/')
    alt = models.CharField(_('alt'), max_length=55, unique=True, null=True, default='')                    # alt should not be dublicate because we used alt instead image id in def __str__(self)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_('product'))

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

    def __str__(self):
        return self.alt




class SmallImage(models.Model):
    image = models.ImageField(_('image'), upload_to='products_images/%Y/%m/%d/smallimages/')
    alt = models.CharField(_('alt'), max_length=55, blank=True, default='')
    father = models.OneToOneField(Image, on_delete=models.CASCADE, verbose_name=_('father'))
    product = models.ForeignKey(Product, related_name='smallimages', on_delete=models.CASCADE, verbose_name=_('product'))

    class Meta:
        verbose_name = _('SmallImage')
        verbose_name_plural = _('SmallImages')

    def __str__(self):
        return self.alt

def save_smallimage(sender, **kwargs):
    if kwargs['created']:
        image = kwargs['instance']
        smallimage = SmallImage(alt=image.alt, father=image, product=image.product)
        smallimage.image.save(os.path.basename(image.image.path), File(open(image.image.path, 'rb')))                         #why save image handy and dont save like SmallImage.objects.create(image=image.image, ....)?  is worse because directory creating(like /media/2020/5/2/small/) and url of that image you expected by "upload_to" copied from image.image and dont see do SmallImage.image at all!!!. so why? because  you're assigning an image directly not uploading file(for saving image Image.image we upload its image by a form) so note upload_to and creating directory you specefid in it will done just when you upload image or save handi that image!!!!   
        smallimage.save()
        file = PilImage.open(smallimage.image.path)
        resized = file.resize((100, 100))
        resized.save(smallimage.image.path)

post_save.connect(save_smallimage, sender=Image)




statuses = [('1', _('not checked')), ('2', _('confirmed')), ('3', _('not confirmed')), ('4', _('deleted'))]
class Comment(models.Model):
    status = models.CharField(_('status'), default='1', max_length=1, choices=statuses)               # review site comments by admin and show comment in site if confirmed, '1' = confirmed     '2' = not checked(admin should check comment to confirm or not)      '3' = not confirmed(admin can confirm afters if want)    '4' = deleted
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)           # published_date should translate in front. for example comment1 (1390/1/27) can translate like: comment1 (2016/4/16)
    content = models.TextField(_('content'), validators=[MaxLengthValidator(500)])
    author = models.ForeignKey(User, related_name='written_comments', related_query_name='comments_author', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    reviewer = models.ForeignKey(User, related_name='reviewed_comments', related_query_name='comments_reviewer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('reviewer'))        # reviewer is last admin changed comment.status
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('post'))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_('product'))

    class Meta:
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')

    def __str__(self):
        return _('Comment') + ' ' + str(self.id)




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
