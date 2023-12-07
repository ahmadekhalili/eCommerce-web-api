from main.models import Product, Category_Filters, Filter_Attribute
from django.db.models.signals import m2m_changed
from django.db.models import Count


class FillCategoryfilters_brands:
    # in this class, filled Category.filters and Category.brands based on Product.filter_attributes & Product.brand &
    # Product.category changes
    pre_category = None       # pre_category and pre_brand_id must fill before calling category_brand_changed()
    pre_brand_id = None

    def category_brand_changed(current_product):            # this method used in product.save(). with this we can identify product.category is changed in last product saving or not.
        current_category, pre_category, remove_filters_id = current_product.category, FillCategoryfilters_brands.pre_category, []
        current_brand_id, pre_brand_id = current_product.brand_id, FillCategoryfilters_brands.pre_brand_id
        filters_id = list(current_product.filter_attributes.values_list('filterr_id', flat=True))
        if current_category and current_category != pre_category:       # *Add Phase*, should come to this condition: 1- if we add category1 to product1.category for first time (pre_category=None) (note in first product's creation like: p1=Product.objects.create(name='p1', filter_attributes=1, category=1) here filters_id==None and filling category done by 'filter_attributes_changed')   2- if we edit product1.category like: product.category = category2 product.save(), current_category=category2 and pre_category=category1    should not come to this condition: 1- if we delete product1.category, here current_category=None and pre_category=category2  2- if we edit eny fields of product1  except .category, like edit product.name ... current_category==pre_category
            current_category.filters.add(*filters_id)           # if we change product.category and remove a filter_attribute of product in same time, here add that filter_attribute.filterr to product and after .save(), remove it again. (product.filter_attributes.remove(..) or product.filter_attributes.add(..) calls after product.save() so filter_attributes_changed calls after .save() to remove that filter.
            if current_brand_id:           # we want to prevent error when don't fill product.brand in product creation
                current_category.brands.add(current_brand_id)
        if pre_category and current_category.id != pre_category.id:     # *Remove Phase*, should came to this condition: 1- if we edit product1.category like: product.category = category2 product.save()  2- if we delete product1.category, here current_category=None and pre_category=category1
            for filter_id in filters_id:
                if not Product.objects.filter(filter_attributes__filterr_id=filter_id, category=pre_category).exists():
                    remove_filters_id.append(filter_id)
            pre_category.filters.remove(*remove_filters_id)
            if pre_brand_id and not Product.objects.filter(category=pre_category, brand=pre_brand_id).exists():   # we check pre_brand_id because we don't want get error when don't fill product.brand in product creation
                pre_category.brands.remove(pre_brand_id)       # this support all type of brand saving like: 1- if we have edited category and add brand for the first time like product1.brand=brand1 product1.save() pre_brand_id=None and pre_category.brands.remove(None) don't run and dont cause eny problem  2- if we have edited category and edit brand too, current_brand_id==2 pre_brand_id==1 and pre_category.brands.remove(1) should do  3- if wehave edited category and delete brand like product1_.brand=None product1.save() current_brand_id=-None pre_brand_id==1 and pre_category.brands.remove(1) should done.

        if current_category and current_brand_id != pre_brand_id:          # but what should happen if we only edit brand or even edit brand & edit category? it comes here with eny problem raising
            current_category.brands.add(current_brand_id) if current_brand_id else None
            current_category.brands.remove(pre_brand_id) if not Product.objects.filter(category=current_category, brand=pre_brand_id).exists() else None

    def filter_attributes_changed(sender, **kwargs):
        if kwargs['instance'].__class__.__name__ == 'Product':          # here access when use normal relation. like prouct1 = Product.objects.filter(id=1)  product1.filter_attributes_set.add(filter_attribute1, filter_attribute2)
            product, filterattribute_ids = kwargs['instance'], kwargs['pk_set']     # kwargs['pk_set'] is like {2,3} type 'Set'
            remove_filters_ids, filters_ids = [], list(Filter_Attribute.objects.filter(id__in=filterattribute_ids).values_list('filterr_id', flat=True))
            if filters_ids:             # if you add dublicate filter_attribute, this will be blank list
                if kwargs['action'] == 'post_add':
                    product.category.filters.add(*filters_ids)
                elif kwargs['action'] == 'post_remove':
                    for filter_id in filters_ids:
                        if not Product.objects.filter(filter_attributes__filterr_id=filter_id, category_id=product.category_id).exists():
                            remove_filters_ids.append(filter_id)
                        product.category.filters.remove(*remove_filters_ids)
                else:
                    pass

        elif kwargs['instance'].__class__.__name__ == 'Filter_Attribute':      # here access when use reverse relation. example: filter_attribute1 = Filter_Attribute.objects.filter(id=1)  filter_attribute1.product_set.add(product_1, product_2)
            filterattribute, product_ids = kwargs['instance'], kwargs['pk_set']
            remove_category_ids, id_categoryid_list = [], Product.objects.filter(id__in=product_ids).values_list('id', 'category_id')
            if kwargs['action'] == 'post_add':
                Category_Filters.objects.bulk_create([Category_Filters(category_id=id_categoryid[1], filter_id=filterattribute.filterr_id) for id_categoryid in id_categoryid_list])
            elif kwargs['action'] == 'post_remove':
                for id_categoryid in id_categoryid_list:
                    if not Product.objects.filter(filter_attributes=filterattribute.id, category=id_categoryid).exists():
                        remove_category_ids.append(id_categoryid[1])
                    Category_Filters.objects.filter(category_id__in=remove_category_ids, filter_id=filterattribute.filterr_id).delete()
            else:
                pass

        else:
            raise '`category.filters` is not provided.'

    m2m_changed.connect(filter_attributes_changed, sender=Product.filter_attributes.through)
