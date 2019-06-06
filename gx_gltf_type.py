#!/usr/bin/env python
# coding: utf-8

"""GLTF Definitions (schema: http://json-schema.org/draft-04/schema)"""

import inspect, pdb

from pprint import pprint

class Schema(object):
    refs = {          'accessor.schema.json' : 'GxAccessor'
           ,         'animation.schema.json' : 'GxAnimation' 
           ,        'bufferView.schema.json' : 'GxBufferView'
           ,            'buffer.schema.json' : 'GxBuffer'
           ,            'camera.schema.json' : 'GxCamera'
           ,             'image.schema.json' : 'GxImage'
           ,          'material.schema.json' : 'GxMaterial'
           ,              'mesh.schema.json' : 'GxMesh'
           ,              'node.schema.json' : 'GxNode'
           ,           'sampler.schema.json' : 'GxSampler'
           ,             'scene.schema.json' : 'GxScene'
           ,              'skin.schema.json' : 'GxSkin'
           ,           'texture.schema.json' : 'GxTexture'
           , 'animation.channel.schema.json' : 'GxAnimationChannel'
           , 'animation.sampler.schema.json' : 'GxAnimationSampler'
           ,    'mesh.primitive.schema.json' : 'GxMeshPrimitive'
           ,            'glTFid.schema.json' : 'GLTF_ID'
    }
    
    schema = {
        
    }
    
    deps = {  # when produced c++ class, some members can have complex type definition
        
    }
    
    @staticmethod
    def any_of(src):
        if list == type(src):
            enum = []
            enum_type = 'UNDEFINED'
            for d in src:
                if 'enum' in d:
                    enum.append(d['enum'][0])
                elif 'type' in d:
                    enum_type = d['type']
                    if 'integer' == enum_type:
                        enum_type = 'int'
                else:
                    enum_type = "<ERROR>"+repr(d)
            return [ enum_type, enum ]
        return repr(item)
    
    @classmethod                         # use decorator to define method bounded with class object, (not class instance)
    def get_schema(cls):                 # and collect type info for each class property from class.schema JSON-like info
        if not hasattr(cls, 'meta'):
            meta = dict()  # __class_name = cls.__name__ )
            prop = cls.schema['properties']
            prop = sorted([ (i, prop[i]) for i in prop ])
            for p, defs in prop:
                if 'type' in defs:
                    if   'integer' == defs['type']: meta[p] = {'type': 'int'}
                    elif  'string' == defs['type']: meta[p] = {'type': 'QString'}
                    elif 'boolean' == defs['type']: meta[p] = {'type': 'bool'}
                    elif   'array' == defs['type']:
                        item_type = defs['items']['type'] if defs['items'].has_key('type') else defs['items']
                        if dict == type(item_type):
                            item_type = Schema.refs[item_type['$ref']]
                        meta[p] = {'type': ('GxArray', 'int', item_type)}
                    elif 'object' == defs['type']:  meta[p] = {'type': defs['type']}
                    else:                           meta[p] = {'type': 'GxDict'}
                elif 'allOf' in defs:               meta[p] = {'type': ('int','allOf')}
                elif 'anyOf' in defs:               meta[p] = {'type': (cls.any_of(defs['anyOf']),'anyOf')}
                else:
                    if 'extensions' == p:           continue
                    elif   'extras' == p:           continue
                    elif     'name' == p:           meta[p] = {'type': 'QString'}
                    else:                           meta[p] = {'type': defs }
            setattr(cls,'meta',meta)
        return cls.meta


class Image(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Image",
        "type": "object",
        "description": "Image data used to create a texture. Image can be referenced by URI or `bufferView` index. `mimeType` is required in the latter case.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "uri": {
                "type": "string",
                "description": "The uri of the image.",
                "format": "uriref",
                "gltf_detailedDescription": "The uri of the image.  Relative paths are relative to the .gltf file.  Instead of referencing an external file, the uri can also be a data-uri.  The image format must be jpg or png.",
                "gltf_uriType": "image"
            },
            "mimeType": {
                "anyOf": [
                    {
                        "enum": [ "image/jpeg" ]
                    },
                    {
                        "enum": [ "image/png" ]
                    },
                    {
                        "type": "string"
                    }
                ],
                "description": "The image's MIME type. Required if `bufferView` is defined."
            },
            "bufferView": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the bufferView that contains the image. Use this instead of the image's uri property."
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "dependencies": {
            "bufferView": [ "mimeType" ]
        },
        "oneOf": [
            { "required": [ "uri" ] },
            { "required": [ "bufferView" ] }
        ]        
    }


class Skin(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Skin",
        "type": "object",
        "description": "Joints and matrices defining a skin.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "inverseBindMatrices": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the accessor containing the floating-point 4x4 inverse-bind matrices.  The default is that each matrix is a 4x4 identity matrix, which implies that inverse-bind matrices were pre-applied."
            },
            "skeleton": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the node used as a skeleton root.",
                "gltf_detailedDescription": "The index of the node used as a skeleton root. The node must be the closest common root of the joints hierarchy or a direct or indirect parent node of the closest common root."
            },
            "joints": {
                "type": "array",
                "description": "Indices of skeleton nodes, used as joints in this skin.",
                "items": {
                    "$ref": "glTFid.schema.json"
                },
                "uniqueItems": True,
                "minItems": 1,
                "gltf_detailedDescription": "Indices of skeleton nodes, used as joints in this skin.  The array length must be the same as the `count` property of the `inverseBindMatrices` accessor (when defined)."
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "joints" ]
}


class Scene(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Scene",
        "type": "object",
        "description": "The root nodes of a scene.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "nodes": {
                "type": "array",
                "description": "The indices of each root node.",
                "items": {
                    "$ref": "glTFid.schema.json"
                },
                "uniqueItems": True,
                "minItems": 1
            },
            "name": { },
            "extensions": { },
            "extras": { }
        }
    }


class Gltf(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "glTF",
        "type": "object",
        "description": "The root object for a glTF asset.",
        "allOf": [ { "$ref": "glTFProperty.schema.json" } ],
        "properties": {
            # "extensionsUsed": {
            #     "type": "array",
            #     "description": "Names of glTF extensions used somewhere in this asset.",
            #     "items": {
            #         "type": "string"
            #     },
            #     "uniqueItems": True,
            #     "minItems": 1
            # },
            # "extensionsRequired": {
            #     "type": "array",
            #     "description": "Names of glTF extensions required to properly load this asset.",
            #     "items": {
            #         "type": "string"
            #     },
            #     "uniqueItems": True,
            #     "minItems": 1
            # },
            "accessors": {
                "type": "array",
                "description": "An array of accessors.",
                "items": {
                    "$ref": "accessor.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of accessors.  An accessor is a typed view into a bufferView."
            },
            "animations": {
                "type": "array",
                "description": "An array of keyframe animations.",
                "items": {
                    "$ref": "animation.schema.json"
                },
                "minItems": 1
            },
            "asset": {
                "allOf": [ { "$ref": "asset.schema.json" } ],
                "description": "Metadata about the glTF asset."
            },
            "buffers": {
                "type": "array",
                "description": "An array of buffers.",
                "items": {
                    "$ref": "buffer.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of buffers.  A buffer points to binary geometry, animation, or skins."
            },
            "bufferViews": {
                "type": "array",
                "description": "An array of bufferViews.",
                "items": {
                    "$ref": "bufferView.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of bufferViews.  A bufferView is a view into a buffer generally representing a subset of the buffer."
            },
            "cameras": {
                "type": "array",
                "description": "An array of cameras.",
                "items": {
                    "$ref": "camera.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of cameras.  A camera defines a projection matrix."
            },
            "images": {
                "type": "array",
                "description": "An array of images.",
                "items": {
                    "$ref": "image.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of images.  An image defines data used to create a texture."
            },
            "materials": {
                "type": "array",
                "description": "An array of materials.",
                "items": {
                    "$ref": "material.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of materials.  A material defines the appearance of a primitive."
            },
            "meshes": {
                "type": "array",
                "description": "An array of meshes.",
                "items": {
                    "$ref": "mesh.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of meshes.  A mesh is a set of primitives to be rendered."
            },
            "nodes": {
                "type": "array",
                "description": "An array of nodes.",
                "items": {
                    "$ref": "node.schema.json"
                },
                "minItems": 1
            },
            "samplers": {
                "type": "array",
                "description": "An array of samplers.",
                "items": {
                    "$ref": "sampler.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of samplers.  A sampler contains properties for texture filtering and wrapping modes."
            },
            "scene": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the default scene."
            },
            "scenes": {
                "type": "array",
                "description": "An array of scenes.",
                "items": {
                    "$ref": "scene.schema.json"
                },
                "minItems": 1
            },
            "skins": {
                "type": "array",
                "description": "An array of skins.",
                "items": {
                    "$ref": "skin.schema.json"
                },
                "minItems": 1,
                "gltf_detailedDescription": "An array of skins.  A skin is defined by joints and matrices."
            },
            "textures": {
                "type": "array",
                "description": "An array of textures.",
                "items": {
                    "$ref": "texture.schema.json"
                },
                "minItems": 1
            },
            "extensions": { },
            "extras": { }
        },
        "dependencies": {
            "scene": [ "scenes" ]
        },
        "required": [ "asset" ]
    }


class Sampler(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Sampler",
        "type": "object",
        "description": "Texture sampler properties for filtering and wrapping modes.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "magFilter": {
                "description": "Magnification filter.",
                "gltf_detailedDescription": "Magnification filter.  Valid values correspond to WebGL enums: `9728` (NEAREST) and `9729` (LINEAR).",
                "gltf_webgl": "`texParameterf()` with pname equal to TEXTURE_MAG_FILTER",
                "anyOf": [
                    {
                        "enum": [ 9728 ],
                        "description": "NEAREST",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9729 ],
                        "description": "LINEAR",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "minFilter": {
                "description": "Minification filter.",
                "gltf_detailedDescription": "Minification filter.  All valid values correspond to WebGL enums.",
                "gltf_webgl": "`texParameterf()` with pname equal to TEXTURE_MIN_FILTER",
                "anyOf": [
                    {
                        "enum": [ 9728 ],
                        "description": "NEAREST",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9729 ],
                        "description": "LINEAR",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9984 ],
                        "description": "NEAREST_MIPMAP_NEAREST",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9985 ],
                        "description": "LINEAR_MIPMAP_NEAREST",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9986 ],
                        "description": "NEAREST_MIPMAP_LINEAR",
                        "type": "integer"
                    },
                    {
                        "enum": [ 9987 ],
                        "description": "LINEAR_MIPMAP_LINEAR",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "wrapS": {
                "description": "s wrapping mode.",
                "default": 10497,
                "gltf_detailedDescription": "S (U) wrapping mode.  All valid values correspond to WebGL enums.",
                "gltf_webgl": "`texParameterf()` with pname equal to TEXTURE_WRAP_S",
                "anyOf": [
                    {
                        "enum": [ 33071 ],
                        "description": "CLAMP_TO_EDGE",
                        "type": "integer"
                    },
                    {
                        "enum": [ 33648 ],
                        "description": "MIRRORED_REPEAT",
                        "type": "integer"
                    },
                    {
                        "enum": [ 10497 ],
                        "description": "REPEAT",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "wrapT": {
                "description": "t wrapping mode.",
                "default": 10497,
                "gltf_detailedDescription": "T (V) wrapping mode.  All valid values correspond to WebGL enums.",
                "gltf_webgl": "`texParameterf()` with pname equal to TEXTURE_WRAP_T",
                "anyOf": [
                    {
                        "enum": [ 33071 ],
                        "description": "CLAMP_TO_EDGE",
                        "type": "integer"
                    },
                    {
                        "enum": [ 33648 ],
                        "description": "MIRRORED_REPEAT",
                        "type": "integer"
                    },
                    {
                        "enum": [ 10497 ],
                        "description": "REPEAT",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "gltf_webgl": "`texParameterf()`"
    }


class Texture(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Texture",
        "type": "object",
        "description": "A texture and its sampler.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "sampler": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the sampler used by this texture. When undefined, a sampler with repeat wrapping and auto filtering should be used."
            },
            "source": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the image used by this texture. When undefined, it is expected that an extension or other mechanism will supply an alternate texture source, otherwise behavior is undefined."
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "gltf_webgl": "`createTexture()`, `deleteTexture()`, `bindTexture()`, `texImage2D()`, and `texParameterf()`"
    }


class Material(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Material",
        "type": "object",
        "description": "The material appearance of a primitive.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "name": { },
            "extensions": { },
            "extras": { },
            "pbrMetallicRoughness": {
                "allOf": [ { "$ref": "material.pbrMetallicRoughness.schema.json" } ],
                "description": "A set of parameter values that are used to define the metallic-roughness material model from Physically-Based Rendering (PBR) methodology. When not specified, all the default values of `pbrMetallicRoughness` apply."
            },
            "normalTexture": {
                "allOf": [ { "$ref": "material.normalTextureInfo.schema.json" } ],
                "description": "The normal map texture.",
                "gltf_detailedDescription": "A tangent space normal map. The texture contains RGB components in linear space. Each texel represents the XYZ components of a normal vector in tangent space. Red [0 to 255] maps to X [-1 to 1]. Green [0 to 255] maps to Y [-1 to 1]. Blue [128 to 255] maps to Z [1/255 to 1]. The normal vectors use OpenGL conventions where +X is right and +Y is up. +Z points toward the viewer. In GLSL, this vector would be unpacked like so: `float3 normalVector = tex2D(<sampled normal map texture value>, texCoord) * 2 - 1`. Client implementations should normalize the normal vectors before using them in lighting equations."
            },
            "occlusionTexture": {
                "allOf": [ { "$ref": "material.occlusionTextureInfo.schema.json" } ],
                "description": "The occlusion map texture.",
                "gltf_detailedDescription": "The occlusion map texture. The occlusion values are sampled from the R channel. Higher values indicate areas that should receive full indirect lighting and lower values indicate no indirect lighting. These values are linear. If other channels are present (GBA), they are ignored for occlusion calculations."
            },
            "emissiveTexture": {
                "allOf": [ { "$ref": "textureInfo.schema.json" } ],
                "description": "The emissive map texture.",
                "gltf_detailedDescription": "The emissive map controls the color and intensity of the light being emitted by the material. This texture contains RGB components in sRGB color space. If a fourth component (A) is present, it is ignored."
            },
            "emissiveFactor": {
                "type": "array",
                "items": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "minItems": 3,
                "maxItems": 3,
                "default": [ 0.0, 0.0, 0.0 ],
                "description": "The emissive color of the material.",
                "gltf_detailedDescription": "The RGB components of the emissive color of the material. These values are linear. If an emissiveTexture is specified, this value is multiplied with the texel values."
            },
            "alphaMode": {
                "default": "OPAQUE",
                "description": "The alpha rendering mode of the material.",
                "gltf_detailedDescription": "The material's alpha rendering mode enumeration specifying the interpretation of the alpha value of the main factor and texture.",
                "anyOf": [
                    {
                        "enum": [ "OPAQUE" ],
                        "description": "The alpha value is ignored and the rendered output is fully opaque."
                    },
                    {
                        "enum": [ "MASK" ],
                        "description": "The rendered output is either fully opaque or fully transparent depending on the alpha value and the specified alpha cutoff value."
                    },
                    {
                        "enum": [ "BLEND" ],
                        "description": "The alpha value is used to composite the source and destination areas. The rendered output is combined with the background using the normal painting operation (i.e. the Porter and Duff over operator)."
                    },
                    {
                        "type": "string"
                    }
                ]
            },
            "alphaCutoff": {
                "type": "number",
                "minimum": 0.0,
                "default": 0.5,
                "description": "The alpha cutoff value of the material.",
                "gltf_detailedDescription": "Specifies the cutoff threshold when in `MASK` mode. If the alpha value is greater than or equal to this value then it is rendered as fully opaque, otherwise, it is rendered as fully transparent. A value greater than 1.0 will render the entire material as fully transparent. This value is ignored for other modes."
            },
            "doubleSided": {
                "type": "boolean",
                "default": False,
                "description": "Specifies whether the material is double sided.",
                "gltf_detailedDescription": "Specifies whether the material is double sided. When this value is false, back-face culling is enabled. When this value is true, back-face culling is disabled and double sided lighting is enabled. The back-face must have its normals reversed before the lighting equation is evaluated."
            }
        },
         "dependencies" : {
            "alphaCutoff" : ["alphaMode"]
        }
    }


class Node(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Node",
        "type": "object",
        "description": "A node in the node hierarchy.  When the node contains `skin`, all `mesh.primitives` must contain `JOINTS_0` and `WEIGHTS_0` attributes.  A node can have either a `matrix` or any combination of `translation`/`rotation`/`scale` (TRS) properties. TRS properties are converted to matrices and postmultiplied in the `T * R * S` order to compose the transformation matrix; first the scale is applied to the vertices, then the rotation, and then the translation. If none are provided, the transform is the identity. When a node is targeted for animation (referenced by an animation.channel.target), only TRS properties may be present; `matrix` will not be present.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "camera": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the camera referenced by this node."
            },
            "children": {
                "type": "array",
                "description": "The indices of this node's children.",
                "items": {
                    "$ref": "glTFid.schema.json"
                },
                "uniqueItems": True,
                "minItems": 1
            },
            "skin": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the skin referenced by this node.",
                "gltf_detailedDescription": "The index of the skin referenced by this node. When a skin is referenced by a node within a scene, all joints used by the skin must belong to the same scene."
            },
            "matrix": {
                "type": "array",
                "description": "A floating-point 4x4 transformation matrix stored in column-major order.",
                "items": {
                    "type": "number"
                },
                "minItems": 16,
                "maxItems": 16,
                "default": [ 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0 ],
                "gltf_detailedDescription": "A floating-point 4x4 transformation matrix stored in column-major order.",
                "gltf_webgl": "`uniformMatrix4fv()` with the transpose parameter equal to false"
            },
            "mesh": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the mesh in this node."
            },
            "rotation": {
                "type": "array",
                "description": "The node's unit quaternion rotation in the order (x, y, z, w), where w is the scalar.",
                "items": {
                    "type": "number",
                    "minimum": -1.0,
                    "maximum": 1.0
                },
                "minItems": 4,
                "maxItems": 4,
                "default": [ 0.0, 0.0, 0.0, 1.0 ]
            },
            "scale": {
                "type": "array",
                "description": "The node's non-uniform scale, given as the scaling factors along the x, y, and z axes.",
                "items": {
                    "type": "number"
                },
                "minItems": 3,
                "maxItems": 3,
                "default": [ 1.0, 1.0, 1.0 ]
            },
            "translation": {
                "type": "array",
                "description": "The node's translation along the x, y, and z axes.",
                "items": {
                    "type": "number"
                },
                "minItems": 3,
                "maxItems": 3,
                "default": [ 0.0, 0.0, 0.0 ]
            },
            "weights": {
                "type": "array",
                "description": "The weights of the instantiated Morph Target. Number of elements must match number of Morph Targets of used mesh.",
                "minItems": 1,
                "items": {
                    "type": "number"
                }
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "dependencies": {
            "weights": [ "mesh" ],
            "skin": [ "mesh" ]
        },
        "not": {
            "anyOf": [
                { "required": [ "matrix", "translation" ] },
                { "required": [ "matrix", "rotation" ] },
                { "required": [ "matrix", "scale" ] }
            ]
        }
        
    }


class MeshPrimitive(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Mesh Primitive",
        "type": "object",
        "description": "Geometry to be rendered with the given material.",
        "allOf": [ { "$ref": "glTFProperty.schema.json" } ],
        "properties": {
            "attributes": {
                "type": "object",
                "description": "A dictionary object, where each key corresponds to mesh attribute semantic and each value is the index of the accessor containing attribute's data.",
                "minProperties": 1,
                "additionalProperties": {
                    "$ref": "glTFid.schema.json"
                }
            },
            "indices": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the accessor that contains the indices.",
                "gltf_detailedDescription": "The index of the accessor that contains mesh indices.  When this is not defined, the primitives should be rendered without indices using `drawArrays()`.  When defined, the accessor must contain indices: the `bufferView` referenced by the accessor should have a `target` equal to 34963 (ELEMENT_ARRAY_BUFFER); `componentType` must be 5121 (UNSIGNED_BYTE), 5123 (UNSIGNED_SHORT) or 5125 (UNSIGNED_INT), the latter may require enabling additional hardware support; `type` must be `\"SCALAR\"`. For triangle primitives, the front face has a counter-clockwise (CCW) winding order. Values of the index accessor must not include the maximum value for the given component type, which triggers primitive restart in several graphics APIs and would require client implementations to rebuild the index buffer. Primitive restart values are disallowed and all index values must refer to actual vertices. As a result, the index accessor's values must not exceed the following maxima: BYTE `< 255`, UNSIGNED_SHORT `< 65535`, UNSIGNED_INT `< 4294967295`."
            },
            "material": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the material to apply to this primitive when rendering."
            },
            "mode": {
                "description": "The type of primitives to render.",
                "default": 4,
                "gltf_detailedDescription": "The type of primitives to render. All valid values correspond to WebGL enums.",
                "anyOf": [
                    {
                        "enum": [ 0 ],
                        "description": "POINTS",
                        "type": "integer"
                    },
                    {
                        "enum": [ 1 ],
                        "description": "LINES",
                        "type": "integer"
                    },
                    {
                        "enum": [ 2 ],
                        "description": "LINE_LOOP",
                        "type": "integer"
                    },
                    {
                        "enum": [ 3 ],
                        "description": "LINE_STRIP",
                        "type": "integer"
                    },
                    {
                        "enum": [ 4 ],
                        "description": "TRIANGLES",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5 ],
                        "description": "TRIANGLE_STRIP",
                        "type": "integer"
                    },
                    {
                        "enum": [ 6 ],
                        "description": "TRIANGLE_FAN",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "targets": {
                "type": "array",
                "description": "An array of Morph Targets, each  Morph Target is a dictionary mapping attributes (only `POSITION`, `NORMAL`, and `TANGENT` supported) to their deviations in the Morph Target.",
                "items": {
                    "type": "object",
                    "minProperties": 1,
                    "additionalProperties": {
                        "$ref": "glTFid.schema.json"
                    },
                    "description": "A dictionary object specifying attributes displacements in a Morph Target, where each key corresponds to one of the three supported attribute semantic (`POSITION`, `NORMAL`, or `TANGENT`) and each value is the index of the accessor containing the attribute displacements' data."
                },
                "minItems": 1
            },
            "extensions": { },
            "extras": { }
        },
        "gltf_webgl": "`drawElements()` and `drawArrays()`",
        "required": [ "attributes" ]
    }


class Mesh(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Mesh",
        "type": "object",
        "description": "A set of primitives to be rendered.  A node can contain one mesh.  A node's transform places the mesh in the scene.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "primitives": {
                "type": "array",
                "description": "An array of primitives, each defining geometry to be rendered with a material.",
                "items": {
                    "$ref": "mesh.primitive.schema.json"
                },
                "minItems": 1
            },
            "weights": {
                "type": "array",
                "description": "Array of weights to be applied to the Morph Targets.",
                "items": {
                    "type": "number"
                },
                "minItems": 1
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "primitives" ]
    }


class Animation(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Animation",
        "type": "object",
        "description": "A keyframe animation.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "channels": {
                "type": "array",
                "description": "An array of channels, each of which targets an animation's sampler at a node's property. Different channels of the same animation can't have equal targets.",
                "items": {
                    "$ref": "animation.channel.schema.json"
                },
                "minItems": 1
            },
            "samplers": {
                "type": "array",
                "description": "An array of samplers that combines input and output accessors with an interpolation algorithm to define a keyframe graph (but not its target).",
                "items": {
                    "$ref": "animation.sampler.schema.json"
                },
                "minItems": 1
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "channels", "samplers" ]
    }


class Buffer(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Buffer",
        "type": "object",
        "description": "A buffer points to binary geometry, animation, or skins.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "uri": {
                "type": "string",
                "description": "The uri of the buffer.",
                "format": "uriref",
                "gltf_detailedDescription": "The uri of the buffer.  Relative paths are relative to the .gltf file.  Instead of referencing an external file, the uri can also be a data-uri.",
                "gltf_uriType": "application"
            },
            "byteLength": {
                "type": "integer",
                "description": "The length of the buffer in bytes.",
                "minimum": 1
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "byteLength" ]
    }


class BufferView(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Buffer View",
        "type": "object",
        "description": "A view into a buffer generally representing a subset of the buffer.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "buffer": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the buffer."
            },
            "byteOffset": {
                "type": "integer",
                "description": "The offset into the buffer in bytes.",
                "minimum": 0,
                "default": 0
            },
            "byteLength": {
                "type": "integer",
                "description": "The total byte length of the buffer view.",
                "minimum": 1
            },
            "byteStride": {
                "type": "integer",
                "description": "The stride, in bytes.",
                "minimum": 4,
                "maximum": 252,
                "multipleOf": 4,
                "gltf_detailedDescription": "The stride, in bytes, between vertex attributes.  When this is not defined, data is tightly packed. When two or more accessors use the same bufferView, this field must be defined.",
                "gltf_webgl": "`vertexAttribPointer()` stride parameter"
            },
            "target": {
                "description": "The target that the GPU buffer should be bound to.",
                "gltf_webgl": "`bindBuffer()`",
                "anyOf": [
                    {
                        "enum": [ 34962 ],
                        "description": "ARRAY_BUFFER",
                        "type": "integer"
                    },
                    {
                        "enum": [ 34963 ],
                        "description": "ELEMENT_ARRAY_BUFFER",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "buffer", "byteLength" ]
        
    }

class Camera(Schema):
    schema = {
        "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Camera",
        "type": "object",
        "description": "A camera's projection.  A node can reference a camera to apply a transform to place the camera in the scene.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "orthographic": {
                "allOf": [ { "$ref": "camera.orthographic.schema.json" } ],
                "description": "An orthographic camera containing properties to create an orthographic projection matrix."
            },
            "perspective": {
                "allOf": [ { "$ref": "camera.perspective.schema.json" } ],
                "description": "A perspective camera containing properties to create a perspective projection matrix."
            },
            "type": {
                "description": "Specifies if the camera uses a perspective or orthographic projection.",
                "gltf_detailedDescription": "Specifies if the camera uses a perspective or orthographic projection.  Based on this, either the camera's `perspective` or `orthographic` property will be defined.",
                "anyOf": [
                    {
                        "enum": [ "perspective" ]
                    },
                    {
                        "enum": [ "orthographic" ]
                    },
                    {
                        "type": "string"
                    }
                ]
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "required": [ "type" ],
        "not": {
            "required": [ "perspective", "orthographic" ]
        }
    }
    
class Accessor(Schema):
    schema = {
    "$schema": "http://json-schema.org/draft-04/schema",
        "title": "Accessor",
        "type": "object",
        "description": "A typed view into a bufferView.  A bufferView contains raw binary data.  An accessor provides a typed view into a bufferView or a subset of a bufferView similar to how WebGL's `vertexAttribPointer()` defines an attribute in a buffer.",
        "allOf": [ { "$ref": "glTFChildOfRootProperty.schema.json" } ],
        "properties": {
            "bufferView": {
                "allOf": [ { "$ref": "glTFid.schema.json" } ],
                "description": "The index of the bufferView.",
                "gltf_detailedDescription": "The index of the bufferView. When not defined, accessor must be initialized with zeros; `sparse` property or extensions could override zeros with actual values."
            },
            "byteOffset": {
                "type": "integer",
                "description": "The offset relative to the start of the bufferView in bytes.",
                "minimum": 0,
                "default": 0,
                "gltf_detailedDescription": "The offset relative to the start of the bufferView in bytes.  This must be a multiple of the size of the component datatype.",
                "gltf_webgl": "`vertexAttribPointer()` offset parameter"
            },
            "componentType": {
                "description": "The datatype of components in the attribute.",
                "gltf_detailedDescription": "The datatype of components in the attribute.  All valid values correspond to WebGL enums.  The corresponding typed arrays are `Int8Array`, `Uint8Array`, `Int16Array`, `Uint16Array`, `Uint32Array`, and `Float32Array`, respectively.  5125 (UNSIGNED_INT) is only allowed when the accessor contains indices, i.e., the accessor is only referenced by `primitive.indices`.",
                "gltf_webgl": "`vertexAttribPointer()` type parameter",
                "anyOf": [
                    {
                        "enum": [ 5120 ],
                        "description": "BYTE",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5121 ],
                        "description": "UNSIGNED_BYTE",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5122 ],
                        "description": "SHORT",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5123 ],
                        "description": "UNSIGNED_SHORT",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5125 ],
                        "description": "UNSIGNED_INT",
                        "type": "integer"
                    },
                    {
                        "enum": [ 5126 ],
                        "description": "FLOAT",
                        "type": "integer"
                    },
                    {
                        "type": "integer"
                    }
                ]
            },
            "normalized": {
                "type": "boolean",
                "description": "Specifies whether integer data values should be normalized.",
                "default": False,
                "gltf_detailedDescription": "Specifies whether integer data values should be normalized (`true`) to [0, 1] (for unsigned types) or [-1, 1] (for signed types), or converted directly (`false`) when they are accessed. This property is defined only for accessors that contain vertex attributes or animation output data.",
                "gltf_webgl": "`vertexAttribPointer()` normalized parameter"
            },
            "count": {
                "type": "integer",
                "description": "The number of attributes referenced by this accessor.",
                "minimum": 1,
                "gltf_detailedDescription": "The number of attributes referenced by this accessor, not to be confused with the number of bytes or number of components."
            },
            "type": {
                "description": "Specifies if the attribute is a scalar, vector, or matrix.",
                "anyOf": [
                    {
                        "enum": [ "SCALAR" ]
                    },
                    {
                        "enum": [ "VEC2" ]
                    },
                    {
                        "enum": [ "VEC3" ]
                    },
                    {
                        "enum": [ "VEC4" ]
                    },
                    {
                        "enum": [ "MAT2" ]
                    },
                    {
                        "enum": [ "MAT3" ]
                    },
                    {
                        "enum": [ "MAT4" ]
                    },
                    {
                        "type": "string"
                    }
                ]
            },
            "max": {
                "type": "array",
                "description": "Maximum value of each component in this attribute.",
                "items": {
                    "type": "number"
                },
                "minItems": 1,
                "maxItems": 16,
                "gltf_detailedDescription": "Maximum value of each component in this attribute.  Array elements must be treated as having the same data type as accessor's `componentType`. Both min and max arrays have the same length.  The length is determined by the value of the type property; it can be 1, 2, 3, 4, 9, or 16.\n\n`normalized` property has no effect on array values: they always correspond to the actual values stored in the buffer. When accessor is sparse, this property must contain max values of accessor data with sparse substitution applied."
            },
            "min": {
                "type": "array",
                "description": "Minimum value of each component in this attribute.",
                "items": {
                    "type": "number"
                },
                "minItems": 1,
                "maxItems": 16,
                "gltf_detailedDescription": "Minimum value of each component in this attribute.  Array elements must be treated as having the same data type as accessor's `componentType`. Both min and max arrays have the same length.  The length is determined by the value of the type property; it can be 1, 2, 3, 4, 9, or 16.\n\n`normalized` property has no effect on array values: they always correspond to the actual values stored in the buffer. When accessor is sparse, this property must contain min values of accessor data with sparse substitution applied."
            },
            "sparse": {
                "allOf": [ { "$ref": "accessor.sparse.schema.json" } ],
                "description": "Sparse storage of attributes that deviate from their initialization value."
            },
            "name": { },
            "extensions": { },
            "extras": { }
        },
        "dependencies": {
            "byteOffset": [ "bufferView" ]
        },
        "required": [ "componentType", "count", "type" ]
    }


def get_schema_based_list(vars_dict):
    res = list()
    names = vars_dict.keys()
    for n in names:
        o = vars_dict[n]
        if inspect.isclass(o) and issubclass(o, Schema):
            if o == Schema:
                continue
            res.append(o)
    return sorted(res)


if __name__ == '__main__':
     
    # OLD DEPRECATED CODE
    def anyOf(src):
        if list == type(src):
            enum = []
            enum_type = 'UNDEFINED'
            for d in src:
                if 'enum' in d:
                    enum.append(d['enum'][0])
                elif 'type' in d:
                    enum_type = d['type']
                    if 'integer' == enum_type:
                        enum_type = 'int'
                else:
                    enum_type = "<ERROR>"+repr(d)
            return { enum_type: enum }
        return repr(item)
    
    def print_info(cls, head='  '):
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
                print('%sdict(%20s = %s)' % (shead, p, {'gx_type': anyOf(defs['anyOf'])}))
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

    # OLD TESTS
    #print_info(Accessor)
    #print_info(Buffer)
    #print_info(BufferView)
    #print_info(Animation)
    #print_info(Mesh)
    #print_info(MeshPrimitive)
    #print_info(Node)
    #print_info(Material)
    #print_info(Texture)
    #print_info(Sampler)
    #print_info(Gltf)
    #print_info(Scene)
    #print_info(Skin)
    #print_info(Image)
    
    from pprint import pprint
    
    tested = get_schema_based_list(locals())
    
    for schema_based_class in tested:
        schema_based_class.get_schema()

    for cls in tested:
        print("\n====%s===================" % cls.__name__)
        cls.get_schema()
        cls_class_list = {}
        pprint(cls.meta)
        print("\n\nclass Gx%s: public QObject" % cls.__name__)
        print("{")
        print("   Q_OBJECT")
        print("public:")
        for name in sorted(cls.meta.keys()):
            if 'sparse' == name:
                continue
            typedef = cls.meta[name]['type']
            if str == type(typedef):
                # print(" // Simple type '%s:%s'" % (typedef, name))
                print("  %-20sm_%s;" % (typedef, name))
            elif tuple == type(typedef):
                # print(" // Complex type '%s:%s'" % (typedef, name))
                if len(typedef) == 2:  
                    if list == type(typedef[0]):  # case => (['int',[...]], 'anyOf')
                        print("  %-20sm_%s;" % ( typedef[0][0] , name ) )
                    else:                         # case => ('int', 'anyOf')
                        print("  %-20sm_%s;" % ( typedef[0] , name ) )
                if len(typedef) == 3:
                    # print hasattr(cls, cls.meta[p]['type'][0])
                    print " /*%s,%s*/" % (typedef, name)
            elif dict == type(typedef):
                print " // Dict type '%s:%s'" % (typedef, name)
                # print hasattr(cls, cls.meta[p]['type'][0])
            else:
                print " // UNSUPPORTED type '%s : %s'" % (type(typedef), name)
        print("};\n")
