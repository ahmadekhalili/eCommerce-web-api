'''
from modeltranslation.translator import translator, TranslationOptions

from main.models import *
# note1: You have to update serializers and forms after adding a field. for example after adding 'name' to FilterTranslation, add g_t('name') to FilterSerializer.Meta.fields and add 'name_fa' 'name_en' fields to FilterForm with proper widget.


class FilterTranslation(TranslationOptions):
    fields = ('name', 'verbose_name')

translator.register(Filter, FilterTranslation)


class BrandTranslation(TranslationOptions):
    fields = ('name', 'slug')

translator.register(Brand, BrandTranslation)


class CategoryTranslation(TranslationOptions):
    fields = ('name', 'slug')

translator.register(Category, CategoryTranslation)


class Filter_AttributeTranslation(TranslationOptions):
    fields = ('name', 'slug')

translator.register(Filter_Attribute, Filter_AttributeTranslation)


class Image_iconTranslation(TranslationOptions):
    fields = ('alt',)

translator.register(Image_icon, Image_iconTranslation)


class ProductTranslation(TranslationOptions):
    exclude = ['id', 'visible', 'created', 'updated', 'filter_attributes', 'category', 'brand', 'rating', 'size']    # 'id' mustn't be in fields otherwise raise error. created and updated should implement in future.
    all_fields = [field.name for field in Product._meta.fields] + [field.name for field in Product._meta.many_to_many]

    def fields_generator(exclude, all_fields):       # we can't use exclude and product_fields in list comprehence without this method.
        return [field for field in all_fields if field not in exclude]

    fields = fields_generator(exclude, all_fields)         # we have definded fields dynamicly, means if we add a field in models.Product, it will add here automatically. size is not 'mostaqel' field so size translating has not means, we have created size_pr size_en just for future updating.

translator.register(Product, ProductTranslation)                # age field is required in amdinpanel, because we definded it blank=False in models.py, if we had definded null=True blank=True for age field that was unrequired.


class ShopFilterItemTranslation(TranslationOptions):
    fields = ('previous_stock', 'stock', 'price', 'available')

translator.register(ShopFilterItem, ShopFilterItemTranslation)


class ImageTranslation(TranslationOptions):
    fields = ('alt',)

translator.register(Image, ImageTranslation)


class ImageSizesTranslation(TranslationOptions):
    fields = ('alt',)

translator.register(ImageSizes, ImageSizesTranslation)


class StateTranslation(TranslationOptions):
    fields = ('name',)

translator.register(State, StateTranslation)


class TownTranslation(TranslationOptions):
    fields = ('name',)

translator.register(Town, TownTranslation)
'''