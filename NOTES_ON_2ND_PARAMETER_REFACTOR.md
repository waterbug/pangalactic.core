# NOTES ON 2nd PARAMETER REFACTOR

## STEPS

DONE = +
[+] 1.  Add ParameterContext objects to reference data for:
[+]   - "prescriptive" contexts:
[+]     + NTE: Not To Exceed (max. allowed value)
[+]     + Margin: (NTE - MEV) / NTE
[+]   - "descriptive" contexts:
[+]     + CBE (Current Best Estimate
[+]     + Contingency:  % tolerance for CBE (represents uncertainty)
[+]     + MEV (Maximum Estimated Value) = CBE * (1 + Contingency)
[+] 2.  Add State objects to reference data for:
[+]   - Peak
[+]   - Quiescent
[+]   - Nominal
[+]   - Launch
[ ] 3.  New functions:  `get_context(context_id)`, `get_state(state_id)`

[ ] 4.  ADD MORE TESTS!!!!


## General notes on the new paradigm

* New parameters are named as:  variable (state) [context]
  ... where the "state" and "context" are used to define a "family" of
  parameters related to the base "variable"

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

* State object (state.id is parameter 'state' attribute)
  - is fully general (state machines etc.)
  - a parameter 'state' can be a standard state or custom state
  - standard states include 'Peak', 'Quiescent', 'Nominal', etc.
  - custom states can be defined by ConOps (Activity Diagram) or state machine
    states.
  - State 'oid' is canonical:  pgef:State.[state.id]

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

