import unittest

from gx_gltf_type import Schema
from gx_gltf_type import Accessor, Buffer, BufferView, Animation, Mesh, MeshPrimitive
from gx_gltf_type import Node, Material, Texture, Sampler, Gltf, Scene, Skin, Image

def test_class(cls, head='  '):
    print("%sclass Gx%s: public QObject" % ( head,  cls.__name__ ) )
    print("%s{" % (head,) )
    print("%s    Q_OBJECT" % (head,) )
    print("%spublic:" % (head,) )
    
    properties = cls.schema['properties']
    properties = sorted([ (i, properties[i]) for i in properties ])
    shead = head + "  "
    for p, defs in properties:
        if 'type' in defs:
            if 'integer' == defs['type']:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'int'}))
            elif 'string' == defs['type']:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'QString'}))
            elif 'boolean' == defs['type']:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'bool'}))
            elif 'array' == defs['type']:
                item_type = defs['items']['type'] if defs['items'].has_key('type') else defs['items']
                if dict == type(item_type):
                    item_type = Schema.refs[item_type['$ref']]
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'GxMap<int, %s>' % item_type}))
            elif 'object' == defs['type']:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'GxDict'}))
            else:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': defs['type'] }))
            
        elif 'allOf' in defs:
            print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'int' }))
            
        elif 'anyOf' in defs:
            print('%sdict(%20s = %s)' % (shead, p, {'gx_type': cls.any_of(defs['anyOf'])}))
        else:
            if 'extensions' == p:
                continue
            elif 'extras' == p:
                continue
            elif 'name' == p:
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': 'QString'}))
            else:
                print('%sdict(%20s = %s)' % (shead,  p, {'gx_type': defs}))
                
    print("%s}; // Gx%s End." % (head, cls.__name__) )
    print("")
    return True

if __name__=='__main__':
    unittest.main()

    # # OLD DEPRECATED CODE
    # def anyOf(src):
    #     if list == type(src):
    #         enum = []
    #         enum_type = 'UNDEFINED'
    #         for d in src:
    #             if 'enum' in d:
    #                 enum.append(d['enum'][0])
    #             elif 'type' in d:
    #                 enum_type = d['type']
    #                 if 'integer' == enum_type:
    #                     enum_type = 'int'
    #             else:
    #                 enum_type = "<ERROR>"+repr(d)
    #         return { enum_type: enum }
    #     return repr(src)
    

    # OLD TESTS
    test_class(Accessor)
    test_class(Buffer)
    test_class(BufferView)
    test_class(Animation)
    test_class(Mesh)
    test_class(MeshPrimitive)
    test_class(Node)
    test_class(Material)
    test_class(Texture)
    test_class(Sampler)
    test_class(Gltf)
    test_class(Scene)
    test_class(Skin)
    test_class(Image)

    
    # from pprint import pprint
    
    # tested = get_schema_based_list(locals())
    
    # for schema_based_class in tested:
    #     schema_based_class.get_schema()

    # for cls in tested:
    #     print("\n====%s===================" % cls.__name__)
    #     cls.get_schema()
    #     cls_class_list = {}
    #     pprint(cls.meta)
    #     print("\n\nclass Gx%s: public QObject" % cls.__name__)
    #     print("{")
    #     print("   Q_OBJECT")
    #     print("public:")
    #     for name in sorted(cls.meta.keys()):
    #         if 'sparse' == name:
    #             continue
    #         typedef = cls.meta[name]['type']
    #         if str == type(typedef):
    #             # print(" // Simple type '%s:%s'" % (typedef, name))
    #             print("  %-20sm_%s;" % (typedef, name))
    #         elif tuple == type(typedef):
    #             # print(" // Complex type '%s:%s'" % (typedef, name))
    #             if len(typedef) == 2:  
    #                 if list == type(typedef[0]):  # case => (['int',[...]], 'anyOf')
    #                     print("  %-20sm_%s;" % ( typedef[0][0] , name ) )
    #                 else:                         # case => ('int', 'anyOf')
    #                     print("  %-20sm_%s;" % ( typedef[0] , name ) )
    #             if len(typedef) == 3:
    #                 # print hasattr(cls, cls.meta[p]['type'][0])
    #                 print( " /*%s,%s*/" % (typedef, name ))
    #         elif dict == type(typedef):
    #             print(" // Dict type '%s:%s'" % (typedef, name) )
    #             # print hasattr(cls, cls.meta[p]['type'][0])
    #         else:
    #             print(" // UNSUPPORTED type '%s : %s'" % (type(typedef), name) )
    #     print("};\n")
