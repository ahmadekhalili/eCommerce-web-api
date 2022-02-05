def circle_roots(root=None, previous_root=None):          #only one of root / previous_root should provide.
    first_root = root                                     #first_root is first "root" we came to circle_roots with it.
    first_root_childs = first_root.root_childs.all()
    roots = []
    
    if root and previous_root:     
        root = previous_root
        ids_list = []
        changed_root = None
        while(True):
            root_childs = [rot for rot in root.root_childs.all()]
            for i in range(len(root_childs)):
                if root_childs[i] == changed_root:
                    root_childs[i] = changed_root
            root.all_childes_id = ','.join(list(dict.fromkeys([s for child in root_childs for s in child.all_childes_id.split(',') if s] + [str(child.id) for child in root_childs]))) if root_childs else ''
            changed_root = root
            roots.append(root)
            root = root.father_root
            if root == first_root:
                break
            
    else:
        root = root
        ids_list = root.all_childes_id.split(',') + [f'{root.id}']
        while(True):
            root = root.father_root
            cleared_ids_list = list(dict.fromkeys(list(filter(None, ids_list))))
            cleared_ids_list.remove(str(root.id))
            root.all_childes_id = ','.join(cleared_ids_list)
            roots.append(root)
            if root in first_root_childs:
                break
         
    return roots


def is_circle(root):
    if root and root.father_root_id:
        if str(root.father_root_id) in root.all_childes_id.split(','):                              #str(root.father_root_id) in root.all_childes_id is worse because supose root.father_root_id=='7' now  '7' in '17,19,20' return return true!!!
            return True
        else:
            return False
    else:
        return False

        
def set_levels_afterthis_all_childes_id(previous_father_queryset, root_queryset, max_limit_value, delete=False):            
    root = root_queryset[0]
    previous_root = previous_father_queryset[0] if previous_father_queryset else None              #if previous_father_queryset, previous_father_queryset[0] raise error.  dont change previous_root variabe name, "recursive effect".
    if root:                        #for example in creating firt root.
        list_childes_id = [root.all_childes_id + f',{root.id}' if root.all_childes_id else f'{root.id}'][0].split(',')
        previous_roots, roots  = [], []
        if previous_root:
            updated_to_1level_root = True if root.level==1 and previous_root.level>1 else False                  #this will true when supose you have a root with level=4, now convert it to level=1, now root.root.father_root is None so we should handle program with this instead "previous_root.id != root.father_root.id"
            if delete or updated_to_1level_root or previous_root.id != root.father_root.id:                  #updated_to_1level_root must be before previous_root.id != root.father_root.id otherwise raise error
                if is_circle(previous_root):
                    previous_roots = circle_roots(root=root, previous_root=previous_root)
                else:
                    upper_root_levels_afterthis, changed_root = root.levels_afterthis, root            
                    while(True):
                        previous_root.all_childes_id = ','.join([s for s in previous_root.all_childes_id.split(',') if s and s not in list_childes_id])
                        if previous_root.levels_afterthis == upper_root_levels_afterthis + 1:
                            childs = previous_root.root_childs.all().values('id', 'levels_afterthis')
                            for child in childs:
                                if child['id'] == changed_root.id:
                                    child['levels_afterthis'] = changed_root.levels_afterthis
                            levels_afterthis_list = sorted([c['levels_afterthis'] for c in childs], reverse=True)
                            biggest_levels_afterthis = levels_afterthis_list[0]+1 if levels_afterthis_list else 0
                            upper_root_levels_afterthis = previous_root.levels_afterthis                                   #why we used previous_root_father_levels_afterthis and upper_root together? and dont remove previous_root_father_levels_afterthis? because in upper_root = previous_root  objects are mutable and upper_root.levels_afterthis will change after changing previous_root.levels_afterthis
                            previous_root.levels_afterthis = biggest_levels_afterthis
                            changed_root = previous_root

                        previous_roots += [previous_root]
                        previous_root = previous_root.father_root                                                                                #note: select_related doesnt lost in recursive and work completly fine(doesnt run additional query)
                        if not previous_root:
                            break    

        
        first_root_id = root.id         
        if root.father_root:                                                                           #if creating a root failed, we have not root and we dont want showing erros of set_levels_afterthis_all_childes_id   (we want show error of model Root)
            if is_circle(root):
                roots = circle_roots(root=root)
                
            else:
                adder = root.levels_afterthis+1
                non_dublicate_childes_id = [s for s in list_childes_id if s not in root.father_root.all_childes_id.split(',')]       #if we dont put non_dublicate_childes_id, in every saving of root objects, all_childes_id of that root will increase repitly with same ids in every saving!!  like this(after several blank saving in admin panel): in '1,3,4,1,3,4,1,3,4,1,3,4,1,3,4,1,3,4,'
                if non_dublicate_childes_id:
                    while(True):
                        child = root
                        root = root.father_root
                        if root:
                            root.all_childes_id = ','.join(list(dict.fromkeys(list(filter(None, root.all_childes_id.split(',') + list_childes_id)))))               #list(dict.fromkeys(L)) remove dublicates of list L  and list(filter(None, ['', '1', '2'])) remove empty str and none from list convert to >> ['1', '2']   note: root.all_childes_id.split(',') if was blank produce [''] that ','.join([''] + ['1', '2']) is like '1,2,' !!
                            if child.levels_afterthis >= root.levels_afterthis:
                                root.levels_afterthis = adder
                                adder += 1
                            roots += [root]                    
                        else:
                            break
        return [previous_roots, roots]
    return [None, None]




def update_product_stock(self, product, saving):         #self is ShopFilterItem obj. this method update stock of product when its ShopFilterItem changes for example supose <shopfilteritem object(2)>.stock -= 2   now <shopfilteritem object(2)>.product.stock should decrease 2 and this method does that for us.
    diff = self.stock - (self.previous_stock or 0)
    if not self.id:                    #creating new ShopFilterItem
        product.stock += self.stock
        if saving:
            product.save()       
    elif diff > 0:
        product.stock += diff
        if saving:
            product.save()
    elif diff < 0:
        product.stock -= diff
        if saving:
            product.save()
    else:
        pass

    if not saving:
        return product























'''
note:deprecated method find_levels_afterthis
def find_levels_afterthis(previous_father_queryset, max_limit_value):  #this method find lelevls_afterthis handy
    prefetch_query = 'root_childs'
    for i in range(max_limit_value-1):
        prefetch_query += '__root_childs'
    root = previous_father_queryset.prefetch_related(prefetch_query)[0]
    x = 0
    for root in root.root_childs.all():
        x = 1 if x<=1 else x                     #when program return from post loops(lop haie badi) to here with upper x value (like 5) we must dont change x value to lower like 1!!!
        for root in root.root_childs.all():
            x = 2 if x<=2 else x
            for root in root.root_childs.all():
                x = 3 if x<=3 else x
                for root in root.root_childs.all():
                    x = 4 if x<=4 else x
                    for root in root.root_childs.all():
                        x = 5 if x<=5 else x
                        for root in root.root_childs.all():
                            x = 6 if x<=6 else x
                            for root in root.root_childs.all():
                                x = 7 if x<=7 else x
                                for root in root.root_childs.all():
                                    x = 8
    return x

'''
