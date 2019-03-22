# Notes on Parameters

## General

  -----------------------------------------------------------------------------
  ** CAVEAT **
  ParameterDefinition is a special class and its definition in the "pgef"
  ontology is strongly coupled to the code!  One specific to remember is that
  the `id` attribute of a ParameterDefinition must be unique in the
  ParameterDefinition namespace, and it also serves as the `id` for any
  parameters that are created from that ParameterDefinition.  (The `id` of the
  created parameter is only unique within its parent object's namespace.)
  -----------------------------------------------------------------------------
  - In Pangalactic, parameters can only be assigned to instances of "Modelable"
    and its subclasses
    + this cannot be enforced by normal python class management, since
      parameters are not python attributes
    + it is enforced at the application level, e.g. by PgxnObject
  - Special case: 'oid' attribute for ParameterDefinition
    + a ParameterDefinition's oid is **always**:
        'pgef:ParameterDefinition.[id]'
    + using the 'pgef:' namespace prefix here allows for other
      namespaces of parameters, but that is not supported (yet)
  - a parameter can be thought of as an "instantiation" of a
    ParameterDefinition (in other words, the ParameterDefinition can be
    regarded as a kind of template for parameters)
  - NOTE:  all parameter metadata are READ-ONLY except `computed` **
    + ** there are not yet any application functions that can define the
      `generating_function` for a parameter whose `computed` value is set to
      True at runtime
    + the parameter's `value` is only writable if `computed` is False)
  - FUTURE PLAN:  a parameter can be "specified", "computed", "correlated"
    + specified:  "fixed" (within the context)
    + computed:  generated from an opaque function (`generating_function`) or
      derived from other properties within the context (e.g. volume = l*w*h,
      mass = density*vol, etc.)
    + correlated:  related to other properties by some mathematical model
      (equation) [a la Modelica)

## Parameter "Families" and Identifier Structure
  - When creating a new 'Parameter Instance', the ParameterDefinition is used
    as a template from which metadata is copied into the Parameter Instance's
    data structure in the `parameterz` dictionary (see below), in the format:

    [id] : {
            "base_parameters":,
            "computed":,
            "description":"",
            "dimensions":"",
            "generating_function":,
            "mod_datetime":,
            "name":[name],
            "range_datatype":,
            "units":[units],
            "value":[value]
            }

  - Identifier structure
    + first segment is `variable_name` (e.g. 'P' for electrical power)
    + second segment (subscript) is "state" (id of related State object)
      * generic states:  'Average', 'Peak', 'Quiescent', etc.
      * custom states:  'Safe Hold', 'Slew', 'Data Transmit', etc.
    + third segment (parens) is "context" (id of ParameterContext object)
      * descriptive:  'CBE', 'MEV', 'Contingency'
      * prescriptive: 'NTE', 'target', 'upper_tol', 'lower_tol', etc.
    + there is no 4th segment!

  - Filtering parameters via context:
    + "specification" contexts: no suffix, "CBE", "total", ...
      used in component or subsystem specifications
    + "systems" contexts: "ctgcy", "NTE", "MEV", ...
      used in managing requirements and evolving system designs

  - so they can be used in perf. requirements and in ConOps
    + Use parametric diagram to specify formula (Relation) for reqt.



## Internal Storage Format

  - parameter values are stored as pure floating point numbers that are
    interpreted as quantities in mks base units

## Parameter Cache: `parameterz`

  - getting and setting cached parameter values

    + all parameters are stored in the `p.node.parametrics.parameterz`
      module-level dictionary
    + `get_pval(orb, obj, parameter_id, allow_nan=False)`
    + `set_pval(orb, obj, parameter_id, val, local=True)`
      (when setting a value received from a remote source, use `local=False`)
    + `value` must be of the correct datatype, as specified by
      `range_datatype`
    + sets the parameter's `mod_datetime`
    + ... dispatches `modified parameter` signal
    + which, if online, publishes `set_parameter` message to instantly update
      remote instances of the object/parameter

  - refreshing the cache (recomputing computed parameters)
    + `orb.recompute_parms()`
      uses: `compute_pval(orb, obj, parameter_id)`
      ... which returns:
      [1] computed == True:  computed value
      [2] computed == False: cached value
      NOTE:  compute_pval() takes a keyword arg `allow_nan` (default: False)
      -- if True and the value could not be computed, the Numpy `NaN` datatype
      (numpy.nan) will be returned

  - cache life-cycle

    + `parameterz` is read from parameters.json at start-up;
    + `parameterz` is recomputed whenever a parameter value is saved;
    + `parameterz` is written to parameters.json at shutdown.


## Future Parameter Performance and Scalability Considerations

The average size of the representation of parameters (a python dictionary with
10 keys) is around 2K to 3K each.

Bear in mind that each object and its parameters are represented only once --
even if an object is used in several assemblies, its usages still point to the
same object so the total memory space of its parameters remains constant.
Therefore, only the number of objects in the library determines the required
memory for parameters -- assembly usages have no impact.

Memory impact could be greatly optimized by a more compact representation --
e.g. using just an "id", "value", "unit" tuple would reduce the size to around
100 bytes per parameter.

The main reason for using dictionaries, which are optimized for speed but not
memory consumption, is that they are very flexible -- fields can be easily
added or removed or have their structures change if necessary.  A more
optimized but rigid structure will be considered when the current system is
mature and even more performance and space efficiency are needed.

Both size and performance can be optimized further by ...

* using Lightning Memory-Mapped Database (LMDB) -- choices:
    - lmdb (0.9.22 in conda pkgs/main) -- only on Linux and Windows (?)
    - py-lmdb -- ctypes-based binding, only for Python 3 (cross-platform)
* using PyTables / HDF5 storage
* writing a parameter-handling module using Cython (which generates a C extension
module from python code).


## ParameterDefinition Objects

  - oid, id, etc. (Identifiable)
  - datatype
  - dimensions (e.g. mass, distance, power, etc.)
  - [other stuff? e.g. `same_as`, pointing to synonyms ...]
  - future:  symbol [mathematical symbol -- unicode(?)]

    ->  ParameterDefinitions do *NOT* have namespaces -- the intent is to
        "force" parameter names to be unique, and parameters to be reusable
        across domains, models, templates, etc.  E.g., there should be only one
        way to define a "mass" parameter, etc.  NOTE:  this really goes to one
        of the core PGEF goals -- to make parameters traceable across the
        various types of models of a product.

  - DisciplineParameterDefinition
    -> m2m relationship between Discipline and ParameterDefinition
    i.e., "Parameter (Definitions) used in this Discipline" --
    this relationship is basically a convenience thing.

----------------------------------------------------------------------------------

## Parameter Definition Editor / Wizard

  - identifier
    + compare to existing identifiers to ensure uniqueness
    + compare to existing PDs by dimensions to ensure it is not a synomym

  - selection lists (configurable)
    + datatypes  (float, integer, string, boolean, etc.)
    + dimensions (these become 'units' in a Parameter)

## GUI for Parameters

OpenModelica's OMEdit GUI has a "Parameters" widget that contains tabbed
panels with (possibly customizable) titles.  For example:

Mechanical "Body Cylinder" model has:
  - General (Headings: Component [Name], Class, Parameters, Initialization,
             + possibly class-specific topic)
  - Initialization (Headings: Initialization, Parameters ... hm, cryptic)
  - Animation (animation-related properties)
  - Advanced (Heading:  Parameters)
  - Modifiers ("Add new modifiers" [free form])

Electrical "Transformer" model has:
  - General
  - Nominal Resistances and inductances
  - Modifiers ("Add new modifiers" [free form])

Simple models (e.g. Electrical Resistor might just have:
  - General
  - Modifiers ("Add new modifiers" [free form])

----------------------------------------------------------------------------------

## Computer Science-y Stuff

* Ontological Properties vs. Parameters

  - Properties are "inherited" -- i.e. from Classes to sub-Classes
    Parameters are assigned to / referenced by instances, NOT inherited

  - Properties are maps from a Class to a datatype or object type;
    Parameters are not restricted to a Class or domain

  - Parameters are intended to be specifically selected as meaningful in the
    context of a Model -- they are not Properties of the Model (in the
    ontological sense) but rather the "INTERFACE" of the Model

  - Parameters are intended to have flexible semantics, which depend on the
    model's context:
    + free or fixed variables (simulation context)
    + specified values (specification context)
    + measured values (test or evaluation context)

* Problems addressed/avoided by Parameter architecture:
  - Need ontology/db structures to be standardized asap,
    but engineers need freedom and flexibility to create
    + Product types (ProductType)
    + Templates
  - Need to avoid:
    + ontology/db structures "exploding" with classes/properties/columns
    + versioning and standardization nightmares
  - Additional undesirables:
    + single-inheritance tree and associated constraints
    + multiple-inheritance complexity

