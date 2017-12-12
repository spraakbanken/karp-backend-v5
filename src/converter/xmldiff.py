import xml.etree.ElementTree as etree
import re
#import xmltodict  # pip install xmltodict
import collections


# from http://stackoverflow.com/questions/3007330/xml-comparison-in-python
def normalise_dict(d):
    """
    Recursively convert dict-like object (eg OrderedDict) into plain dict.
    Sorts list values.
    """
    out = {}
    for k, v in dict(d).items():
        if hasattr(v, 'items'):
            out[k] = normalise_dict(v)
        elif isinstance(v, list):
            out[k] = []
            newv = []
            sort = True
            for item in v:
                if hasattr(item, 'items'):
                     newv.append(normalise_dict(item))
                     # TODO can we trust that the order kept their orders?
                     sort = False # can't sort list of dicts
                else:
                     newv.append(item)
            if sort:
                out[k] = sorted(newv)
            else:
                out[k] = newv
            #out[k] = sorted(newv, key=lambda k: str(k))
                
            #for item in sorted(v):
            #    if hasattr(item, 'items'):
            #        out[k].append(normalise_dict(item))
            #    else:
            #        out[k].append(item)
        else:
            out[k] = v
    return out


def xml_compare(a, b):
    """
    Compares two XML documents (as string or etree)

    Does not care about element order
    """
    a = open(a).read()
    b = open(b).read()
    dicta = xmltodict.parse(a)
    dictb = xmltodict.parse(b)
   # a = normalise_dict(dicta)
   # b = normalise_dict(dictb)
    return dicta == dictb, dicta, dictb


## from http://stackoverflow.com/questions/1165352/calculate-difference-in-keys-contained-in-two-python-dictionaries
class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect 
    def removed(self):
        return self.set_past - self.intersect 
    def changed(self):
        changed = [(o,self.past_dict[o],self.current_dict[o]) for o in self.intersect if self.past_dict[o] != self.current_dict[o]]
        for o in self.intersect:
            if type(self.past_dict[o])==collections.OrderedDict:
                changed.extend(DictDiffer(normalise_dict(self.past_dict[o]),normalise_dict(self.current_dict[o])).changed())
        return  changed
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


def etree_compare(old,new,spec,obj_n,errors):
    listold = [x for x in list(old) if x.tag!="feat" or x.attrib.get('val','dummy')!='']
    listnew = [x for x in list(new) if x.tag!="feat" or x.attrib.get('val','dummy')!='']
    #if len(listold)!=len(old):
    #    print('diff',[etree.tostring(x) for x in set(old)-set(listold)])
    #if len(listnew)!=len(new):
    #    print('diff',[etree.tostring(x) for x in set(new)-set(listnew)])
    #    #print([etree.tostring(x) for x in listnew])
    #    #print([etree.tostring(x) for x in list(new)])
    if len(listold)!=len(listnew):
    #    print(old.tag,len(listold),len(listnew))
    #    print(len(list(old)),len(list(new)))
        errors.append('%s-%d, %s: unequal length, %d-%d %s\n %s' % (spec,obj_n,old.tag,len(listold),len(listnew),etree.tostring(old),etree.tostring(new)))
    if old.tag.split('}')[-1].strip()!=new.tag.split('}')[-1].strip():
        errors += ['%s-%d, %s: different names, %s-%s' % (spec,obj_n,old.tag,old.tag,new.tag)]
    if len(old.attrib)!=len(new.attrib):
        errors += ['%s-%d, %s: unequal attrib length, %s-%s' % (spec,obj_n,old.tag,old.attrib,new.attrib)]
    for ok,ov in old.attrib.items():
      if ok not in new.attrib:
          errors += ['%s-%d, %s: unequal attrib, %s:%s' % (spec,obj_n,old.tag,ok,ov)]  
      elif ov!=new.attrib.get(ok):
           if re.sub('\s\s*',' ',ov).strip()!=re.sub('\s\s*',' ',new.attrib.get(ok)).strip():
               errors += ['%s-%d, %s: unequal attrib, %s:%s-%s' % (spec,obj_n,old.tag,ok,ov,new.attrib.get(ok))]  
    oldtext = (old.text or '') + (old.tail or '')
    newtext = (new.text or '') + (new.tail or '')
    newtext = re.sub('\s\s*',' ',re.sub('\n',' ',newtext).strip())
    oldtext = re.sub('\s\s*',' ',re.sub('\n',' ',oldtext).strip())
    if oldtext!=newtext:
          errors += ['%s-%d, %s: unequal text, %s-%s' % (spec,obj_n,old.tag,oldtext,newtext)]  
    new_obj = 0
    new_sorted = sortfeats(listnew,old.tag)
    #print('\n\nnew\n',new)
    for n,oldelem in enumerate(sortfeats(listold,old.tag)): 
#        print('old-new')
#        print(etree.tostring(oldelem))
        if len(new_sorted)>n:
            newelem = new_sorted[n]
#            print(etree.tostring(newelem))
            etree_compare(oldelem,newelem,mkspec(old,obj_n,hist=spec),new_obj,errors)
            new_obj = new_obj+1


def mkspec(elem,n,hist=''):
    s = elem.find('Sense')
    if s:
        return '%s_%d' % (elem.find('.//Sense').attrib.get('id') ,n)
    return hist+elem.tag


def sortfeats(elems,tag):
    #if elems and elems[0].tag=="feat":
    #print('\n'.join([x.attrib.get('att',x.tag.split('}')[-1])+x.attrib.get('val',','.join(list(x.attrib.keys()))) for x in elems]))
    #if elems and elems[0].tag=="LexicalEntry":
    #    return elems
    #print('sorted',sorted(elems,key=lambda x: x.attrib.get('att',x.tag.split('}')[-1])+x.attrib.get('val',','.join(sorted(list(x.attrib.keys()))))))
    if tag=='Lexicon':
        return elems
    #xs =  sorted(elems,key=lambda x: x.attrib.get('att',x.tag.split('}')[-1])+x.attrib.get('val',','.join(sorted(list(x.attrib.keys())))))
    #print('sorted',[(x.tag,x.attrib) for x in xs])
    return sorted(elems,key=lambda x: x.attrib.get('att',x.tag.split('}')[-1])+x.attrib.get('val',','.join(sorted(list(','.join(kv) for kv in x.attrib.items())))))
    #else:
    #    return sorted(elems,key=lambda x: x.tag)



