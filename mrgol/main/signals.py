from main.models import Product, Root_Filters, Filter_Attribute
from django.db.models.signals import m2m_changed
from django.db.models import Count


class FillRootfilters_brands:
    pre_root = None
    pre_brand_id = None

    def root_brand_changed(current_product):            # this method used in product.save(). with this we can identify product.root is changed in last product saving or not.
        current_root, pre_root, remove_filters_id = current_product.root, FillRootfilters_brands.pre_root, []
        current_brand_id, pre_brand_id = current_product.brand_id, FillRootfilters_brands.pre_brand_id
        filters_id = list(current_product.filter_attributes.values_list('filterr_id', flat=True))
        if current_root and current_root != pre_root:       # Add Phase, should come to this condition: 1- if we add root1 to product1.root for first time like: p1=Product.objects.create(name='p1', filter_attributes=1) p1.root=root1 p1.save() current_root=root1 pre_root=None (note in first product's creation like: p1=Product.objects.create(name='p1', filter_attributes=1, root=1) here filters_id==None and filling root done by 'filter_attributes_changed'  2- if we edit product1.root like: product.root = root2 product.save(), current_root=root2 and pre_root=root1    should not come to this condition: 1- if we delete product1.root=root1, here current_root=None and pre_root=root1  2- if we edit eny fields of product1  except .root, like edit product.name ... current_root==pre_root
            current_root.filters.add(*filters_id)           # if we change product.root and remove a filter_attribute of product in same time, here add that filter_attribute.filterr to product and after .save(), remove it again. (product.filter_attributes.remove(..) or product.filter_attributes.add(..) calls after product.save() so filter_attributes_changed calls after .save() to remove that filter.
            current_root.brands.add(current_brand_id)
        if pre_root and current_root.id != pre_root.id:     # Remove Phase, should came to this condition: 1- if we edit product1.root like: product.root = root2 product.save(), current_root=root2 and pre_root=root1  2- if we delete product1.root, here current_root=None and pre_root=root1
            for filter_id in filters_id:
                if not Product.objects.filter(filter_attributes__filterr_id=filter_id, root=pre_root).exists():
                    remove_filters_id.append(filter_id)
            pre_root.filters.remove(*remove_filters_id)
            if not Product.objects.filter(root=pre_root, brand=pre_brand_id).exists():
                pre_root.brands.remove(pre_brand_id)       # this support all type of brand saving like: 1- if we have edited root and add brand for the first time like product1.brand=brand1 product1.save() pre_brand_id=None and pre_root.brands.remove(None) don't run and dont cause eny problem  2- if we have edited root and edit brand too, current_brand_id==2 pre_brand_id==1 and pre_root.brands.remove(1) should do  3- if wehave edited root and delete brand like product1_.brand=None product1.save() current_brand_id=-None pre_brand_id==1 and pre_root.brands.remove(1) should done.

        else:          # but what should happen if we only edit brand without changing root? we should cover it too.
            if current_brand_id != pre_brand_id:
                current_root.brands.add(current_brand_id) if current_brand_id else None
                current_root.brands.remove(pre_brand_id) if not Product.objects.filter(root=current_root, brand=pre_brand_id).exists() else None

    def filter_attributes_changed(sender, **kwargs):
        if kwargs['instance'].__class__.__name__ == 'Product':          # here access when use normal relation. like prouct1 = Product.objects.filter(id=1)  product1.filter_attributes_set.add(filter_attribute1, filter_attribute2)
            product, filterattribute_ids = kwargs['instance'], kwargs['pk_set']     # kwargs['pk_set'] is like {2,3} type 'Set'
            remove_filters_ids, filters_ids = [], list(Filter_Attribute.objects.filter(id__in=filterattribute_ids).values_list('filterr_id', flat=True))
            if filters_ids:             # if you add dublicate filter_attribute, this will be blank list
                if kwargs['action'] == 'post_add':
                    product.root.filters.add(*filters_ids)
                elif kwargs['action'] == 'post_remove':
                    for filter_id in filters_ids:
                        if not Product.objects.filter(filter_attributes__filterr_id=filter_id, root_id=product.root_id).exists():
                            remove_filters_ids.append(filter_id)
                        product.root.filters.remove(*remove_filters_ids)
                else:
                    pass

        elif kwargs['instance'].__class__.__name__ == 'Filter_Attribute':      # here access when use reverse relation. example: filter_attribute1 = Filter_Attribute.objects.filter(id=1)  filter_attribute1.product_set.add(product_1, product_2)
            filterattribute, product_ids = kwargs['instance'], kwargs['pk_set']
            remove_root_ids, id_rootid_list = [], Product.objects.filter(id__in=product_ids).values_list('id', 'root_id')
            if kwargs['action'] == 'post_add':
                Root_Filters.objects.bulk_create([Root_Filters(root_id=id_rootid[1], filter_id=filterattribute.filterr_id) for id_rootid in id_rootid_list])
            elif kwargs['action'] == 'post_remove':
                for id_rootid in id_rootid_list:
                    if not Product.objects.filter(filter_attributes=filterattribute.id, root=id_rootid).exists():
                        remove_root_ids.append(id_rootid[1])
                    Root_Filters.objects.filter(root_id__in=remove_root_ids, filter_id=filterattribute.filterr_id).delete()
            else:
                pass

        else:
            raise '`root.filters` is not provided.'

    m2m_changed.connect(filter_attributes_changed, sender=Product.filter_attributes.through)
