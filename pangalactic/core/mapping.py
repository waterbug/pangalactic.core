"""
Functions for data conversion between releases.

Note that not all schema modifications require data conversion functions; in
some cases, the serialization/db-drop-create/deserialization process will
suffice.

Examples of schema mods that do not require a conversion function include:

* Adding or renaming an unpopulated class or attribute
* Removing an attribute (populated or not)

Examples of schema mods that require a conversion function include:

* Renaming a populated class or attribute
* Removing a populated class
* Adding an attribute with a non-null default value

`schema_mods`:  a list of the releases that include schema modifications

`schema_maps`: a dictionary that maps release numbers to the data conversion
               functions they require
"""
# NOTES:

# version 3.0.0:
#   * mods:
#     - Removed class "ActCompRel" (many-to-many relationship between Activity
#       and parent "composite" Activity instances) because Activities are not
#       really "components" and are not reusable (that would be "Procedure",
#       which might in the future be a useful class but is not relevant now) --
#       an Activity object is by nature a one-time occurrence and may or may
#       not be a "sub-activity" of another Activity.

# version 3.0.0:
#   * mods:
#     - Flow now has attrs "start_port_context" and "end_port_context", which
#       are the Acus of the products that have the ports -- this is important
#       since Flows only exist in the context of the assembly that contains the
#       product usages
#     - Activity was subclass of Modelable; now subclass of ManagedObject
#       (reason: Activity needed "owner" attribute)
#       + was subclass of Modelable; now subclass of ManagedObject
#       + removed attribute "activity_of" (referenced Product)
#       + added attributes
#         * "of_function":  references Acu (of which this is Activity)
#           inverse: "function_activities" (of Acu)
#         * "of_system":  references ProjectSystemUsage
#           inverse: "system_activities" (of PSU)
#     - new class: ActivityControl (subclass of ManagedObject)
#       + attribute: "antecedent" (Activity immediately preceding the control)
#     - new class: Merge (subclass of ActivityControl)
#       (rejoins activity sequence after a Decision branch)
#     - new class: Decision (subclass of ActivityControl)
#       (branches an activity sequence)
#       + attribute: "condition" (boolean-valued Relation)
#       + attribute: "next_activity" (next Activity if condition is true)
#       + attribute: "alternative_activity" (next Activity if condition is
#         false)

# version 2.0.0:
#   * mods:
#     - Activity was subclass of DigitalProduct; now subclass of Modelable
#     - Activity previously used Acu to create "composite activities";
#       now uses a new class, ActCompRel (Activity Composition Relationship)
#     - Requirement:
#       simplify the "shall statement" form by removing:
#           req_shall_phrase   (included in req_predicate)
#           req_min_max_phrase (included in req_predicate)
#           req_epilog         (unnecessary)
#       define req_subject, req_predicate, (new attr) req_object as:
#           req_subject = allocated_to_[system|function].reference_designator
#                         + parameter.dimensions**
#                  ** reqt.computable_form.correlates_parameter.dimensions
#           req_predicate = "shall be" + constraint phrase (e.g. "less than")
#           req_object = [value / range / tolerances] + req_units
#   * reasons:
#     - Activity changes address a sqlalchemy warning
#     - Requirement changes address needed simplifications and potential
#       representation of Requirement objects as semantic "triples"

# version 1.5.0:
#   * mods:
#     - Actor was subclass of ManagedObject; now subclass of Identifiable
#     - Organization was subclass of Actor;  now subclass of Modelable
#   * reason:
#     These changes fix a sqlalchemy warning about the multiple fk rels between
#     the 'actor_', 'managed_object_', and 'organization_' tables, which is now
#     eliminated.  As a result of these mods, Actor and Person objects do not
#     have a 'creator' or 'modifier' attribute, but that is not a problem
#     because they will always be created by a global admin.

from copy import deepcopy

schema_mods = ['1.0.4', '1.5.0', '2.0', '3.0', '3.1.0']

schema_version = '3.2.0'


def to_x_x_x(sos):
    """
    Convert serialized data to x.x.x schema.

    Args:
        sos (list):  serialized objects to be transformed
    """
    for so in sos:
        # transform
        pass
    return sos


def to_2_0_0(sos):
    """
    Convert any serialized Acu objects that reference Activity instances to
    serialized ActCompRel objects.  Requirement, Relation, and
    ParameterRelation objects can be retained as is, since deserialization will
    ignore the deprecated attributes.

    Args:
        sos (list):  serialized objects to be transformed
    """
    by_oids = {so.get('oid') : so for so in sos}
    new_sos = []
    for so in sos:
        if (so.get('_cname') == 'Acu' and
            so.get('assembly') in by_oids and
            by_oids[so.get('assembly')].get('_cname') in ['Activity',
            'Mission']):
            new_so = deepcopy(so)
            new_so['_cname'] = 'ActCompRel'
            new_so['composite_activity'] = new_so['assembly']
            new_so['sub_activity'] = new_so['component']
            new_so['sub_activity_role'] = new_so['reference_designator']
            del new_so['assembly']
            del new_so['component']
            new_sos.append(new_so)
        else:
            new_sos.append(so)
    return new_sos

# `schema_maps` dictionary maps versions to conversion functions
schema_maps = {'2.0.0': to_2_0_0}

