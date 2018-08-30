# NOTES ON PAN GALACTIC ONTOLOGY

### Mods

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

---------------
References:
* [1] STEP: ISO 10303

