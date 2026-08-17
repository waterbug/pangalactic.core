# NOTES ON PAN GALACTIC ONTOLOGY

### Mods

* 2026-08-16 (schema version 3.5.0)
  - Added `Axis2Placement3D` and `ContextDependentShapeRepresentation`, both
    `Identifiable` subclasses, which record where a component sits within its
    assembly.  See "Component placement" below.

* 2018-03-21
  - Classes that were `Identifiable` subclasses, now `Modelable` subclasses:
    [Acu, ParameterRelation, PortType, ProductRequirement,
    ProductTypeParameterDefinition, ProjectSystemUsage, Relation,
    Representation]

  - Actor was `Identifiable` subclass, now `ManagedObject` subclass

### Scope

* Engineering and scientific objects and data about them


### Products, Models, etc.

* Product

  - A Product can have 0 or more Models.  The Product entity can be thought of
    as a "collection point" for Parameters that are shared among the Product's
    Discipline-specific Models -- one of the purposes of the Product is to
    synchronize the Parameters that are shared among its Models.  In that
    sense, a Product object is effectively treated as a "Master Model" of
    sorts.
  - A Product object's `has_models` property points to its Discipline-specific
    Models

* Model

  - The Model object's `of_thing` property points to the Product (or whatever)
    it models
  - A Model can have 1 or more Representations (e.g., PDF, XMI [SysML], PNG,
    STEP[1], etc.)
  - The Model property `frame_of_reference` specifies the context of the Model,
    e.g.:
    + Block [SysML: a Block in a diagram]
    + IBD [SysML: an Internal Block Diagram of the Product]
    + MCAD
    + ECAD
  - `model_definition_context` [Discipline]:  the Discipline in the context of
    which a model was created, e.g. "Space Mission", "Attitude Control", etc.
    (maps to STEP[1] "product_definition.frame_of_reference.application" -- see
    description in ontology).
  - `type_of_model` [ModelType]:  e.g., "Block" (as would occur in a SysML
    block diagram -> SysML BDD), "Internal Block" (Block containing internal
    structure -> SysML "IBD").

* Discipline

  - a competency area (e.g. an "engineering discipline")
  - purposes:
    + to filter Parameter Definitions, Products, and Models, and Templates
    + to allocate create/edit permissions that are shared among users in a
      collaborative context who have been assigned roles related to the
      Discipline.

  - definition:

    A named subject matter area (e.g. a specific engineering discipline,
    such as Avionics or Flight Dynamics, or a scientific discipline, such as
    Solid State Physics, or possibly specific, such as Surface Physics).  The
    intent of defining Disciplines in the context of a collaborative modeling
    activity is to define the roles and points of view of the participants and
    their models.  Disciplines are distinguished from Modeling Domains by being
    more granular, customized, and potentially enterprise-specific.

* ProductType

  - definition:  A category or classification of a product.
  - each Product instance is required to be assigned a ProductType as the value
    of its `product_type` property.
  - purposes:
    + to filter Products in the Product library (as a convenience)
    + to specify the type of Product intended to be placed in a Template
      component position (the components positions in a Template are
      instances of `Acu` that point to a "TBD" object and have a
      `product_type_hint` property that specifies a ProductType).

* DisciplineProductType

* ModelFamily

  - definition:

    A Model Family is intended to characterize a family of Model Types.  Some
    Model Families are standardized, such as SysML, but a Model Family may also
    refer to a collection of custom or enterprise-specific Model Types.
    Examples:  The SysML Model Family owns the model types of "Block", "Internal
    Block", "Parametric", etc.; a "Mechanical Engineering" Model Family might
    own the Model Type "Mechanical CAD", etc.

  - intent is to be used as a "tag" for Model Types (and, indirectly, for
    Models by their "type_of_model", which is a Model Type that has a Model
    Family) so they can be easily filtered in a library selection list or
    dialog

  - can be either "standard" (e.g. SysML) or custom, enterprise-specific
    (e.g. owned by MDL)

    -> provides values used for:
       ModelType.model_type_family

* ModelType

  - type of a model
    + e.g.:  Block, Internal Block, MCAD, ECAD, Schematic, etc.
  - intent:  to filter Models
  - each Model has a `type_of_model` (ModelType) attr
  - provides values used for
    + `Model.type_of_model`
    + `ModelTemplate.model_template_type`

* Assembly

  - Assemblies represent "As-Designed" systems (specifications) and their
    components should be interpreted as references to Product specifications
  - Assembly structures are created using `Acu` (Assembly Component Usage)
    relationships

    + `Acu` relates a component (Product) to an assembly (Product) in which it
      occurs
    + `Acu` also has attributes:
      * `reference_designator`:  the role of the component in the assembly
      * `product_type_hint`:     the ProductType of the component
      * `assembly_level`:        the assembly level of the component

  - An "As-Built" Assembly is to be distinguished from an "As-Designed"
    assembly.  The former is composed of ProductInstances, which represent
    physical things -- manufactured instances of a Product [specification].
    [TODO:  a PhysicalAssemblyComponentUsage -- PACU -- is needed for this,
    which will be a relationship between two ProductInstances.]


### Some Specific Class Notes

* Person
  - notes on properties:
    + `oid`:  maps to `nasa:` + NED uupic
    + `id`:  maps to NED auid
    + `id_ns`:  `nasa` for NED records
    + `org`:  maps to NED `org code` (`585.0`, etc. -- may need ns `gsfc`?)
    + `name`: maps to NED `display_name`
    + `mi_or_name`:  -> NED `middle_initials`

* Eee Part (Class: `EEEPart`)
  - Definition from Space Station EEE Parts doc 
    SSP30312, Revision H (author:  NASA/JSC)
    November 22, 1999

    EEE Parts are limited to the following Federal Stock Classes (FSC): 

    Product Types       FSC 
    -------------       ---
    Capacitors       5910 
    Circuit Breakers      5925 
    Connectors      5935 
    Crystals and Crystal Oscillators     5955 
    Diodes       5961 
    Fiber Optic Accessories     6070 
    Fiber Optic Cables      6015 
    Fiber Optic Conductors     6010 
    Fiber Optic Devices      6030 
    Fiber Optic Interconnects     6060 
    Filters       5915 
    Fuses       5920 
    Inductors       5950 
    Hybrids/Multi-Chip Modules (MCMs)    5999 (misc.) 
    Microcircuits      5962 
    Relays       5945 
    Resistors       5905 
    Switches       5930 
    Thermistors      5905 
    Transformers      5950 
    Transistors       5961 
    Wire and Cable      6145

### Component placement

Added at schema version 3.5.0, so that a project assembly can be used as
input to a 42 ACS simulation and, more generally, so that assembly geometry
can be imported from CAD.  Two classes, both `Identifiable` subclasses:

* `Axis2Placement3D` -- the location and orientation of a coordinate frame:
  `location_[xyz]`, `axis_[xyz]` (the direction of the local z axis) and
  `ref_direction_[xyz]` (the direction of the local x axis).  The local y
  axis is implied.  Orientation is held as direction cosines, so **no
  rotation sequence convention is implied** and none has to be agreed.

* `ContextDependentShapeRepresentation` -- `represented_usage` -> `Acu`,
  `placement` -> `Axis2Placement3D`, with inverses `Acu.shape_representations`
  and `Axis2Placement3D.placement_of`.

**Placement belongs to the usage, not to the product.**  A product used at
several places in an assembly has a different placement at each, which is why
this hangs off the `Acu` -- and it is how STEP models it too, by way of the
`next_assembly_usage_occurrence` that the `Acu` corresponds to.  The `Acu`
definition has said as much since long before these classes existed:  a
conceptual product "can be used at multiple locations (distinguished by
reference designator, a property of the Acu)".

#### Mapping to STEP [1]

| PGEF | STEP |
|---|---|
| `Acu` | `next_assembly_usage_occurrence` |
| `ContextDependentShapeRepresentation` | `context_dependent_shape_representation` |
| `Axis2Placement3D` | `axis2_placement_3d` |
| `location_[xyz]` | `axis2_placement_3d.location` (a `cartesian_point`) |
| `axis_[xyz]` | `axis2_placement_3d.axis` (a `direction`) |
| `ref_direction_[xyz]` | `axis2_placement_3d.ref_direction` (a `direction`) |

Two deliberate simplifications, both recoverable on export:

1. STEP associates the `context_dependent_shape_representation` with the NAUO
   indirectly, through the NAUO's `product_definition_shape`.  PGEF has no
   `product_definition_shape` concept, so `represented_usage` points at the
   `Acu` directly.
2. STEP carries the transform in an `item_defined_transformation`, which has
   two `axis2_placement_3d` items -- `transform_item_1` in the component's own
   representation and `transform_item_2` in the assembly's.  `placement`
   holds the *net* placement of the component in the assembly, i.e. it takes
   `transform_item_1` to be the identity.  This is what pythonocc's
   `XCAFDoc_ShapeTool.GetLocation()` returns for a component occurrence, so
   nothing is lost on import.

Also, STEP makes the location a `cartesian_point` and each direction a
`direction`, all independently identified entities.  Here they are plain
coordinates on the placement, since PGEF has no use for separately identified
points and directions -- and doing otherwise would mean four objects per
placement.

#### What a new class costs

Recorded here because it generalizes.  The registry builds SQLAlchemy classes
and tables from the ontology and calls `Base.metadata.create_all()`, so a new
class needs **no hand-written table or migration**; bumping
`mapping.schema_version` makes each install dump its db, rebuild the classes
from the ontology and reload.  Per `mapping.py`, adding an unpopulated class
needs no conversion function.  But four places do not follow automatically:

* `serializers.DESERIALIZATION_ORDER` -- a class missing from it lands in the
  unordered "other" bucket, so an object can be deserialized before something
  it references.  That is a foreign key violation whose appearance depends on
  dict ordering, i.e. an intermittent failure.
* `access.modifiables` -- objects that are only ever reached through a parent
  object need to be listed, or no user can modify them.
* `access.is_cloaked()` -- anything that falls through its branches is treated
  as **public**.  A placement on a cloaked assembly leaking is a real
  disclosure, so subsidiary classes must delegate to their parent.
* `access.get_owner_id()` -- resolves the project channel that vger publishes
  an object's "new"/"modified" notification on.  A class that resolves to `''`
  is not broken, but it syncs only at the next full sync rather than in real
  time.

The last two both delegate the same way, which is why `get_owner_id()` was
factored out of `vger.save()`, where the owner / PSU / Acu chain had been
inlined twice.

#### Cloning

`clone()` builds an assembly's new `Acu`s attribute by attribute, so shape
representations had to be copied explicitly:
`clone_shape_representations()` does it for both of the blocks that create
`Acu`s -- the `include_specified_components` one and the
`include_components` one -- and the new objects join `new_objs`, so they are
saved and synced with the rest of the clone.

The placement is **copied, not shared**.  A placement is reachable from every
representation that uses it (`placement_of`), so sharing one between an
assembly and its clone would mean that moving a component in the clone moved
it in the original.

Note that in both blocks the loop variable was being shadowed by the new
`Acu` it created, so the source `Acu` was no longer reachable by the end of
the iteration; it is now bound as `src_acu`.

**Coverage caveat:** like the rest of `clone()`, this has a `fastorb` branch
and an `uberorb` branch, and the tests exercise the `uberorb` one.  `clone()`
has no `fastorb` coverage at all -- `test_fastorb.py` does not call it -- so
the `fastorb` branch here is only as good as its following the same pattern
the surrounding `Acu` creation already uses (passing objects rather than oids
to `create_or_update_thing`).  Deliberately left there for now:  `fastorb` is
known to need substantial work of its own, so it is not worth special
attention from this change.

#### Not yet done

* No UI.  These objects are reachable only through an `Acu`, and nothing
  routes one to `PgxnObject` yet.
* Nothing populates them.  The STEP importer is the next piece --
  see `pangalactic.node/NOTES_ON_STEP_IMPORT.md`.

---------------
References:
* [1] STEP: ISO 10303

