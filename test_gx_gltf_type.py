import gx_gltf_type

def xtest_class(cls, head='  '):
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
                item_type = defs['items']['type'] if 'type' in defs['items'] else defs['items']
                if dict == type(item_type):
                    item_type = gx_gltf_type.Schema.refs[item_type['$ref']]
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

def test_Accessor():
    xtest_class(gx_gltf_type.Accessor)

def test_Buffer():
    xtest_class(gx_gltf_type.Buffer)

def test_BufferView():
    xtest_class(gx_gltf_type.BufferView)

def test_Animation():
    xtest_class(gx_gltf_type.Animation)

def test_Mesh():
    xtest_class(gx_gltf_type.Mesh)

def test_MeshPrimitive():
    xtest_class(gx_gltf_type.MeshPrimitive)

def test_Node():
    xtest_class(gx_gltf_type.Node)

def test_Material():
    xtest_class(gx_gltf_type.Material)

def test_Texture():
    xtest_class(gx_gltf_type.Texture)

def test_Sampler():
    xtest_class(gx_gltf_type.Sampler)

def test_Gltf():
    xtest_class(gx_gltf_type.Gltf)

def test_Scene():
    xtest_class(gx_gltf_type.Scene)

def test_Skin():
    xtest_class(gx_gltf_type.Skin)

def test_Image():
    xtest_class(gx_gltf_type.Image)
