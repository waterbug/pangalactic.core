# NOTES ON 2nd PARAMETER REFACTOR

## STEPS

DONE = [+]
[+] 1.  Add ParameterContext objects to reference data for:
[+]   - "prescriptive" contexts:
[+]     + NTE: Not To Exceed (max. allowed value)
[+]     + Margin: (NTE - MEV) / NTE
[+]   - "descriptive" contexts:
[+]     + Average
[+]     + CBE (Current Best Estimate
[+]     + Contingency:  % tolerance for CBE (represents uncertainty)
[+]     + MEV (Maximum Estimated Value) = CBE * (1 + Contingency)
[+]     + Nominal
[+]     + Peak
[+]     + Quiescent
[+]     + RMS
[+] 3.  Fix PgxnObject to display only base ("variable") parameters
[+] 3.  New functions:  `get_parameter_context_oid(pcid)`,
        `get_state_oid(sid)`
[+] 4.  Fix Contexts:  need to specify variables a generating fn supports
        (e.g., "get_assembly_parameter" works for m, P, R_D)
[+] 5.  Fix Dashboards:
[ ] 6.  Fix Reqts Wizard to use parameters / prescriptive contexts
[ ] 7.  ADD MORE TESTS!!!!


## General notes on the new paradigm

* New parameters are named as:  variable [context]
  ... where the "context" is used to define a "family" of parameters related to
  the base "variable"

* the new ParameterDefinition class:
  - only defines "base" parameters (a.k.a. "variables")
  - DOES NOT HAVE the following properties of the old ParameterDefinition:
    + `base_parameters`
    + `generating_function`
      NOTE: `base_parameters` (arguments) will now be defined by the
      'generating_function' associated with a ParameterContext -- therefore
      unnecessary in the parameter data structures.
    + `computed` 
  ... these attributes are defined by a ParameterContext, which may specify how
  a parameter's value in that context is derived (computed from other
  parameters and/or standard quantities)

* "Mode"
  - "Mode" is considered a synonym of "State"
  - "Mode" is an ActivityType
  - used in the MDL "Modes Table", which specifies the values of a parameter,
    such as Power, for various operational states of a system, such as a
    Spacecraft.

* ParameterContext object (parameter 'context' attribute)
  - properties local to ParameterContext are:
    + `context_type` (str) ['prescriptive'|'descriptive']
    + `context_dimensions`
    + `context_datatype` (str) name of a datatype
      contextual parameters may have different datatype than their variable --
      like 'Contingency' (percent)
    + `computed` (bool)
  - NOT NEEDED: `generating_function` -- each context will have a unique
    generating function, which will be looked up in `GEN_FNS`, a dictionary in
    the parametrics module that maps Context ids to generating functions
  - combines with (variable + state) to define parameters related to the
    (variable + state) in different contexts
  - "prescriptive" contexts:
    + NTE: Not To Exceed (max. allowed value)
    + Margin: (NTE - MEV) / NTE
  - "descriptive" contexts:
    + CBE (Current Best Estimate
    + Contingency:  % tolerance for CBE (represents uncertainty)
    + MEV (Maximum Estimated Value) = CBE * (1 + Contingency)

* Parameter instance (dictionary data structure):

    [id] : {
            "variable":,
            "state":,
            "context",
            "context_type",
            "computed":,
            "description":"",
            "dimensions":"",
            "mod_datetime":,
            "name":[name],
            "range_datatype":,
            "value":[value],
            "units":[units]
            }

  ... in which:
  - id:           a string derived as:
                  PD.id + '_' + state.id + '_' + context.id
  - name:         a string derived as:
                  PD.name + ' (' + state.name + ')' + ' [' + context.name + ']'
  - variable:     set as the 'id' of the base Parameter Definition
  - state:        set as the 'id' of a State instance
  - context:      set as the 'id' of a Context instance
  - context_type: set as the 'context_type' of the Context, if any
                  ("prescriptive" or "descriptive")
  - computed:     a boolean, set from the Context instance
  - description:  derived from the PD, State, and Context descriptions
  - dimensions:   set from the Context instance
  - mod_datetime":  mod datetime of the parameter instance
  - range_datatype:  set from the Context instance
  - value:        value of the paramter
  - units:        display units (settable by user or prefs)

