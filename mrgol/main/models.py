from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
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
#note: changing classes places may raise error when creating tables(makemigrations), for example changing Content with Post will raise error(Content use Post in its field and shuld be definded after Post)



class Root(models.Model):                                  #note: supose roor2 object,  root2.father_root determine father of root2 and root2.root_childs is list of root2's childer,  root with level=1 can has eny father!
    name = models.CharField(_('name'), unique=True, max_length=50)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)
    level = models.PositiveSmallIntegerField(_('level'), default=1, validators=[MinValueValidator(1), MaxValueValidator(6)])        #important: in main/views/ProductRootList & ProductDetail and in main/mymethods/get_posts_products_by_root   we used MaxValueValidator with its posation in validator, so validator[1] must be MaxValueValidator otherwise will raise error.
    levels_afterthis = models.PositiveSmallIntegerField(default=0, blank=True)                         #in field neshan midahad chand sath farzand darad in pedar, masalam: <root(1) digital>,  <root(2) mobail>,  <root(3) samsung> farz konid mobail pedare samsung,  digital pedare mobail ast(<root(1) digital>.level=1,  <root(2) mobail>.level=2,  <root(3) samsung>.level=3)   . bala sare digital dar in mesal 2 sath farzand mibashad( mobail va samsung pas <root(1) digital>.levels_afterthis = 2   va <root(2) mobail>.levels_afterthis=1  va <root(3) samsung>.levels_afterthis=0
    previous_father_id = models.PositiveSmallIntegerField(null=True, blank=True)                         #supose you change root.father_root, we cant understant prevouse father was what in Root.save(ony new edited father_root is visible) so we added this field
    father_root = models.ForeignKey('self', related_name='root_childs', related_query_name='childs', null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('father root'))        #if root.level>1 will force to filling this field.     
    all_childes_id = models.TextField(default='', blank=True)                      #list all chiles of that object in this structure: "1,2,3,4"    if this field name was chiles_id maybe raise problem with related_query_name of father_root or other.
    post_product = models.CharField(_('post or product'), max_length=10, default='product')      #this should be radio button in admin panel.
    #root_childs
    #filter_set
    
    class Meta:
        ordering = ('level',)                    #main/views/ProductList/sidebarmenu_link affect order of Root.  ('level', '-father_root_id') '-father_root_id' make in ProductRootList products order from last to first (reverse order) -father_root_id  will make childs with same father be in together. and '-' will make decending order like ordering django admin for 'order by ids' means lower ids will go to down.(tested)
        verbose_name = _('menu')
        verbose_name_plural = _('menus')
    
    def __str__(self):
        return str(self.level) + ' - ' + self.name
    
    def clean_fields(self, exclude=None):
        if self.level:                                                   #why we put this line?  answer: in adding root, self.father_root is None and raise erro if: 'self.level > 1' 
            if self.level > 1 and not self.father_root:                  #other conditions will control by form eazy (for example if self.level==1 father_root must be None)
                raise ValidationError({'father_root': [_('This field is required for level more than 1.')]})
        super().clean_fields(exclude=None)

    def save(self, *args, **kwargs):
        previous_father_queryset = Root.objects.filter(id=self.previous_father_id).select_related('father_root__'*4+'father_root') if self.previous_father_id else None
        self.previous_father_id = self.father_root_id if self.father_root_id else None
        super().save(*args, **kwargs)
        root_queryset = Root.objects.filter(id=self.id).select_related('father_root__'*5+'father_root')    #instead using 6 logn father_root we used more breafer format!      
        
        roots_before_join, roots_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, root_queryset, Root._meta.get_field('level').validators[1].limit_value) 
        Root.objects.bulk_update(roots_before_join, ['levels_afterthis', 'all_childes_id']) if roots_before_join else None     
        Root.objects.bulk_update(roots_after_join, ['levels_afterthis', 'all_childes_id']) if roots_after_join else None

    def delete(self, using=None, keep_parents=False):
        id = self.id
        dell = super().delete(using, keep_parents)
        previous_father_queryset = Root.objects.filter(id=self.father_root_id).select_related('father_root__'*5+'father_root') if self.father_root_id else None
        self.id, self.father_root, self.father_root_id = id, None, None                                               #we need self.id in list_childes_id
        roots_before_join, roots_after_join = set_levels_afterthis_all_childes_id(previous_father_queryset, [self], Root._meta.get_field('level').validators[1].limit_value, delete=True) 
        Root.objects.bulk_update(roots_before_join, ['levels_afterthis', 'all_childes_id']) if roots_before_join else None 
        return dell




group_choices = [(key, str(key)) for key in range(1, 11)]
class Filter(models.Model):
    group = models.PositiveIntegerField(_('group'), choices=group_choices)
    name = models.CharField(_('name'), unique=True, max_length=25)        # name for quering. 
    verbose_name = models.CharField(_('verbose name'), max_length=25)     # name for showing. (to user).  for example you have two filter with names: "system amel goshi", "system amele laptop" but both of them have 'system amel' as verbose name.
    #selling = models.BooleanField(_('selling filter'), default=False)
    roots = models.ManyToManyField(Root, through='Filter_Roots', verbose_name=_('roots'))
    #filter_attributes

    class Meta:
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')

    def __str__(self):
        return str(self.name)

class Filter_Roots(models.Model):
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE, verbose_name=_('filter'))
    root = models.ForeignKey(Root, on_delete=models.CASCADE, verbose_name=_('root'))

    class Meta:
        verbose_name = _('Filter Root')
        verbose_name_plural = _('Filter Roots')

    def __str__(self):
        return _('Filter Roots') + str(self.id)

Filter_Roots._meta.auto_created = True                        #if you dont put this you cant use filter_horizontal in admin.py for  Filter.roots or other manytomany fields that use Filter_Roots.




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
    rate = models.DecimalField(_('rate'), max_digits=2, decimal_places=1, default=0)       # don't need add MaxValueValidator, rating of every product is created in Product.save() with controled value.

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
    detailed_description = RichTextUploadingField(_('detailed description'), blank=True, null=True)
    visible = models.BooleanField(_('delete'), default=True)
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)
    image_icon = models.OneToOneField(Image_icon, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('image icon'))
    root = models.ForeignKey(Root, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('root'))
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    #comment_set                                                   #backward relation

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        represantaion = self.title[:30]+'...' if len(self.title) > 40 else self.title[:30]
        return represantaion




class Brand(models.Model):
    name = models.CharField(_('name'), max_length=25, null=True, blank=True)
    slug = models.SlugField(_('slug'), allow_unicode=True, db_index=False)

    class Meta:
        verbose_name = _('brand')
        verbose_name_plural = _('brands')

    def __str__(self):
        return self.name


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
    detailed_description = RichTextUploadingField(_('detailed description'), blank=True, null=True)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=0)       # for $ prices we need decimal_places fpr example price: 19.99$ has 2 decimal places
    available = models.BooleanField(_('available'), default=False, db_index=True)
    visible = models.BooleanField(_('delete'), default=True, db_index=True)                #we use visible for deleting an object, for deleting visible=False, in fact we must dont delete any product.    
    created = models.DateTimeField(_('created date'), auto_now_add=True)
    updated = models.DateTimeField(_('updated date'), auto_now=True)
    filter_attributes = models.ManyToManyField(Filter_Attribute, through='Product_Filter_Attributes', blank=True, verbose_name=_('filter attributes'))
    root = models.ForeignKey(Root, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('root'))
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('brand'))          # brand field as CharField is not logical and should be ForeignKey why? because for example in adding product1 we may add brand "nokia" and in second product2 add "Nokia". when products increased (supose more than 100) it will raise real problems
    image_icon = models.OneToOneField(Image_icon, on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('image icon'))     #in home page(page that list of product shown) dont query product.image_set.all()[0] for showing one image of product, instead query product.image_icon   (more fster)
    rating = models.OneToOneField(Rating, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('rating'))
    stock = models.PositiveIntegerField(_('stock'), default=0)                        # important: stock before creating first shopfilteritem of product shoud be 0 otherwise it will sum with shopfilteritem.stock, example: supose we have product1.stock = 10  now after creating shopfilteritem1 with stock=12 product1.stock will be 10+12   (address: in ShopFilterItem.save and model_methods.py/update_product_stock
    weight = models.FloatField(_('weight'), null=True, blank=False)                   # weight is in gram and used in orders/mymethods/profile_order_detail/PostDispatchPrice  but if you dont specify weight in saving a product, it will be None and will ignore in PostDispatchPrice. its better null=True easier in creating products in tests.
    size = models.CharField(_('size'), max_length=25, null=True, blank=True)          # value should be in mm  and like '100,150,150'  this field seperate to 3 field in ProductForm in __init__ and save func), also we use size in mymethods.PostDispatchPrice  to define which box size should choice for posting.
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
        super().save(*args, **kwargs)
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




class MDetailProduct(djongo_models.Model):
    id = djongo_models.IntegerField(blank=False, null=False, primary_key=True)
    json = djongo_models.JSONField()
    #name = djongo_models.CharField(_('name'), max_length=60)
    #slug = djongo_models.CharField(_('slug'), max_length=60)
    #meta_title = djongo_models.CharField(_('meta title'), max_length=60, blank=True, default='')
    #meta_description = djongo_models.TextField(_('meta description'), validators=[MaxLengthValidator(160)], blank=True, default='')
    #brief_description = djongo_models.TextField(_('brief description'), validators=[MaxLengthValidator(1000)])
    #detailed_description = RichTextUploadingField(_('detailed description'), blank=True, null=True)
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
    product =  models.ForeignKey(Product, on_delete=models.CASCADE, related_name='shopfilteritems', verbose_name=_('product'))         #why we dont use ShopFilterItem as manytomany field in Product? because we want one object of ShopFilterItem only point to one product (supose one  object of ShopFilterItem as shopfilteritem_1 if thos shopfilteritem_1 point to several product instead one product, so eny changes on shopfilteritem_1 like decreasing shopfilteritem_1.price will affect on other products!!!!
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
    confirm_status = models.CharField(_('confirm status'), default='1', max_length=1, choices=statuses)               #confirm site comments by admin and show comment in site if confirmed, '1' = confirmed     '2' = not checked(admin should check comment to confirm or not)      '3' = not confirmed(admin can confirm afters if want)    '4' = deleted
    published_date = models.DateTimeField(_('published date'), auto_now_add=True)
    content = models.TextField(_('content'), validators=[MaxLengthValidator(500)])
    author = models.ForeignKey(User, related_name='comment_set_author', related_query_name='comments_author', on_delete=models.SET_NULL, null=True, blank=False, verbose_name=_('author'))
    confermer = models.ForeignKey(User, related_name='comment_set_confermer', related_query_name='comments_confermer', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('confermer'))
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
