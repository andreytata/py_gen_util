#### py_gen_util

Dark Jedy book "Simplest Way To Cook Python"

<b>Generate code using Generation GAP pattern.</b>

<i>Use our simplest glTF2.0 file reader (recipe 06)
Scene graph converter (recipe 07).
Add some set of classes for create custom code generators.</i>

:camel:

Create some base class, possible pure virtual
```cpp
class GGapBase : protected QOpenGLFunctions
{
public:
    virtual ~GGapBase(){}
    virtual void A() = 0;
    virtual void B() = 0;
}
```
And create some applicatin, depended generated files
static std::list<GGapBase*> generated_list;

```cpp
#include "classes_generated_by_codegenerator.txt"

std::list<GGapBase*>& context() {
#include "context_generated_by_codegenerator.txt" 
}
void main() {
    // fixed code do something with context
    for( auto gen : context() ) { gen->A(); }
    // ...
    for( auto gen : context() ) { gen->B(); }
    // ...
}
```
Python generator create set of generated classes use data files edited by 3D artists or UI designers, as data source.
also generate context where register instances of generated
classes.  
```cpp
class Generated01 : public GGapBase
{
public:
    void A() { /*for example some concrete init code*/ }
    void B() { /*for example some concrete drawing code*/ }
}
```
So, after data source changed, script execute generator before execute source compiler.