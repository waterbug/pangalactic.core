# -*- coding: utf-8 -*-
"""
The objects that carry a file, and the bytes that make them mean anything.

A `Model` and its `RepresentationFile` used to be created only by
`vger.add_update_model()`, which made attaching a file to a product an rpc --
and therefore impossible offline, even though every other object an import
creates is built locally and synced later.  Nothing about the two objects
requires the server:  the only thing that looked server-side was the vault
file name, and that is `orb.get_vault_fname()`, a derivation from the
RepresentationFile's own oid and user file name that both ends already have.

So they are built here instead, by whichever side needs them, and the client
builds them whether it is connected or not.

**The invariant this module exists to keep:  a RepresentationFile reaches the
repository only together with its bytes.**  A file object without its file is
not a degraded version of the thing, it is a lie -- it says a file is
available and every reader of it is wrong.  So the bytes are copied into the
local vault the moment the object is created, which makes them recoverable
from the object alone (`vault_path()`), and the push of the object is
sequenced behind the push of the bytes.  No separate queue of pending uploads
is needed:  the local vault *is* the record of what has bytes, and
`vger.missing_vault_files()` is the record of what the repository still
lacks.

See NOTES_ON_STEP_IMPORT.md section 3c.
"""
import hashlib
import mimetypes
import os
import shutil
from uuid import uuid4

from pangalactic.core import orb, state
from pangalactic.core.placements import new_thing
from pangalactic.core.utils.datetimes import dtstamp

# how much of a file to hash at a time -- files here are CAD assemblies and
# can be large, so they are not read whole to be checksummed
HASH_CHUNK = 2 ** 20

# the ModelType a CAD file is a representation of, for a component file whose
# caller did not say.  Named here as well as in step_dialogs because this
# module may not import from pangalactic.node.
MCAD_MODEL_TYPE = 'pgefobjects:ModelType.MCAD'


def file_checksum(fpath):
    """
    The sha-256 of a file's contents, which is what `DigitalFile.checksum` is
    defined to hold.

    Args:
        fpath (str):  path to the file

    Returns:
        str:  the hex digest, or '' if the file cannot be read.  '' means
        "cannot compare", never "differs":  callers treat an absent checksum
        as no evidence either way, since warning about a file we could not
        read would only train the user to click through the warning.
    """
    h = hashlib.sha256()
    try:
        with open(fpath, 'rb') as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK), b''):
                h.update(chunk)
    except OSError:
        return ''
    return h.hexdigest()


def new_model_with_file(mtype_oid, fpath, parms, NOW=None):
    """
    Create a Model of something and the RepresentationFile that holds its
    file, locally.

    A transcription of what `vger.add_update_model()` does, with three
    differences, all of them corrections rather than variations:

    * the RepresentationFile gets a `creator`.  The rpc sets one on a
      component file but not on the main one, so every RepresentationFile the
      repository holds from that path is in nobody's `created_objects` and
      could never be synced by `sync_user_created_objs_to_repo()`.
    * `file_size` is stored as the int the column is declared as, rather than
      the str the signal carries.
    * `checksum` is populated.  Nothing ever set it, though `DigitalFile`
      has declared it as "a sha-256 hash generated from the file contents"
      all along -- and the STEP importer's changed-file check already looks
      for it.

    Args:
        mtype_oid (str):  oid of the ModelType
        fpath (str):  path to the file on this machine
        parms (dict):  as carried by the "add update model" signal -- 'file
            name', 'file size', 'mime_type', 'name', 'description',
            'of_thing_oid', 'owner_oid', 'project_oid'

    Keyword Args:
        NOW (datetime):  timestamp for the new objects

    Returns:
        tuple:  (Model, RepresentationFile), or (None, None) if the thing
        being modelled or the owner cannot be resolved -- the two conditions
        the rpc refused on, refused here for the same reasons and reported
        the same way, by a log line and an empty result.
    """
    NOW = NOW or dtstamp()
    fname = parms.get('file name') or os.path.basename(fpath)
    thing = orb.get(parms.get('of_thing_oid', ''))
    if thing is None:
        orb.log.error('  - new_model_with_file: no "of_thing" object.')
        return (None, None)
    owner = (orb.get(parms.get('owner_oid') or '')
             or orb.get(parms.get('project_oid') or ''))
    if owner is None:
        orb.log.error('  - new_model_with_file: no owner and no project.')
        return (None, None)
    m_name = parms.get('name', '') or '.'.join(fname.split('.')[:-1])
    # the same id form the rpc used, so a locally created model is
    # indistinguishable from one the repository made
    m_id = m_name.replace(' ', '_').lower() + '-' + str(uuid4().int)[:6]
    model = new_thing('Model', NOW=NOW,
                      id=m_id, name=m_name,
                      description=parms.get('description', '') or '',
                      of_thing=thing,
                      type_of_model=orb.get(mtype_oid),
                      owner=owner,
                      # public follows the thing modelled:  a model of a
                      # public library product is as public as the product
                      public=bool(getattr(thing, 'public', False)))
    rep_file = new_thing('RepresentationFile', NOW=NOW,
                         id=m_id + '_file', name=m_name + ' file',
                         of_object=model,
                         user_file_name=fname,
                         file_size=file_size_of(fpath, parms),
                         mime_type=parms.get('mime_type', '') or '',
                         checksum=file_checksum(fpath))
    # the url cannot be set in the call above:  it is derived from the oid,
    # which new_thing() assigns
    rep_file.url = os.path.join('vault://', orb.get_vault_fname(rep_file))
    return (model, rep_file)


def new_component_file(referencing, fpath, parms, of_thing=None,
                       mtype_oid='', NOW=None):
    """
    Create the RepresentationFile for a file that another file references,
    locally.

    A CAD assembly may be exported as a *set*:  the assembly file names its
    subassembly and part files and cannot be read without them.  Each of
    those needs an object of its own, or only the file the user chose reaches
    the repository and the assembly renders as a few components and a lot of
    nothing.

    A transcription of `vger.add_component_file()`, which it replaces, with
    the same three rules:

    * **the file joins a Model rather than always getting one.**  Given the
      product it models -- a STEP file in an export set says which:
      `main_body_back_prt.stp` *is* the model of MAIN_BODY_BACK -- it gets a
      Model of that product, which is what lets a subassembly be opened on
      its own.  Without it, it joins the referencing file's Model:  it is not
      a model of anything in its own right.
    * **`component_file_of` records which file needs which**, so the set can
      be staged under the names the references use.
    * **it is idempotent.**  A file already recorded under this name for this
      referencing file is returned rather than duplicated -- an import can
      legitimately be repeated, and a part shared by two subassemblies is
      named by both of them in the same set.

    Args:
        referencing (RepresentationFile):  the file that names this one
        fpath (str):  path to the referenced file on this machine
        parms (dict):  'file name', 'file size', 'mime_type'

    Keyword Args:
        of_thing (Product):  the product this file is the model of, if it is
            known
        mtype_oid (str):  ModelType for a Model made for `of_thing`
        NOW (datetime):  timestamp for the new objects

    Returns:
        tuple:  (Model or None, RepresentationFile or None).  The Model is
        not None only when one was created for `of_thing`;  joining an
        existing Model creates nothing to report.  Both are None if the
        referencing file belongs to no Model, which is the one condition
        there is nothing sensible to do about.
    """
    NOW = NOW or dtstamp()
    model = getattr(referencing, 'of_object', None)
    if model is None:
        orb.log.error('  - new_component_file: the referencing file belongs '
                      'to no model.')
        return (None, None)
    fname = parms.get('file name') or os.path.basename(fpath)
    if not fname:
        orb.log.error('  - new_component_file: no file name.')
        return (None, None)
    for existing in (referencing.component_files or []):
        if existing.user_file_name == fname:
            orb.log.debug(f'  - "{fname}" already recorded.')
            return (None, existing)
    base = '.'.join(fname.split('.')[:-1]) or fname
    new_model = None
    if of_thing is not None:
        new_model = new_thing('Model', NOW=NOW,
                              id=base.replace(' ', '_').lower() + '-'
                                 + str(uuid4().int)[:6],
                              name=base,
                              description=f'STEP model of {of_thing.id}',
                              of_thing=of_thing,
                              type_of_model=(orb.get(mtype_oid) if mtype_oid
                                             else orb.get(MCAD_MODEL_TYPE)),
                              # the owner is the referencing model's:  a file
                              # of an export set belongs where the set does
                              owner=getattr(model, 'owner', None),
                              public=bool(getattr(of_thing, 'public', False)))
        model = new_model
    rep_file = new_thing('RepresentationFile', NOW=NOW,
                         id=base.replace(' ', '_').lower() + '-'
                            + str(uuid4().int)[:6] + '_file',
                         name=base + ' file',
                         of_object=model,
                         component_file_of=referencing,
                         user_file_name=fname,
                         file_size=file_size_of(fpath, parms),
                         mime_type=parms.get('mime_type', '') or '',
                         checksum=file_checksum(fpath))
    rep_file.url = os.path.join('vault://', orb.get_vault_fname(rep_file))
    return (new_model, rep_file)


def file_size_of(fpath, parms=None):
    """
    The file's size in bytes, preferring the file itself to what a caller
    said about it.

    `file_size` is an Integer column and the "add update model" signal
    carries it as a str, which has been reaching the database as a str all
    along;  `vger.download_chunk()` then divides by it to count chunks.

    Args:
        fpath (str):  path to the file

    Keyword Args:
        parms (dict):  the signal's parms, used only if the file cannot be
            measured

    Returns:
        int:  the size, or 0 if it is not known
    """
    try:
        return os.path.getsize(fpath)
    except OSError:
        try:
            return int((parms or {}).get('file size') or 0)
        except (TypeError, ValueError):
            return 0


def new_doc_with_file(fpath, parms, NOW=None):
    """
    Create a Document, the RepresentationFile that holds its file, and the
    DocumentReference that attaches it to something -- locally.

    A transcription of `vger.add_update_doc()`, which it replaces, for the
    reasons in this module's docstring.

    **The DocumentReference is the awkward one, and it is worth knowing why.**
    It is an `Identifiable`, not a `Modelable`, so it has no `creator` -- and
    `sync_user_created_objs_to_repo()` pushes `local_user.created_objects`,
    which is the inverse of `creator`.  It therefore cannot reach the
    repository the way the other two do.

    Making it a `Modelable`, as the placement classes became at schema 3.6.0
    for exactly this reason, **does not work**:  `related_item` points at
    `Modelable`, which would become its own superclass, and sqlalchemy's
    joined table inheritance cannot tell that foreign key from the
    inheritance one.  Verified 2026-08-29, not merely read off the warning in
    `registry.py` -- the orb does not start, with
    `AmbiguousForeignKeysError: Can't determine the inherit condition between
    inherited table 'modelable_' and inheriting table 'document_reference_'`.

    So it travels as a dependent of its Document instead:  the client pushes
    the two together (`push_document_references()`), and
    `access.modifiables` carries `DocumentReference` so that the repository
    will accept one -- it cannot be authorized by creator, having none.

    Args:
        fpath (str):  path to the file on this machine
        parms (dict):  as carried by the "add update doc" signal -- 'file
            name', 'file size', 'name', 'description', 'rel_obj_oid',
            'owner_oid', 'project_oid'

    Keyword Args:
        NOW (datetime):  timestamp for the new objects

    Returns:
        tuple:  (Document, DocumentReference, RepresentationFile), or
        (None, None, None) if the related object or the owner cannot be
        resolved -- the two conditions the rpc refused on.
    """
    NOW = NOW or dtstamp()
    fname = parms.get('file name') or os.path.basename(fpath)
    rel_obj = orb.get(parms.get('rel_obj_oid', ''))
    if rel_obj is None:
        orb.log.error('  - new_doc_with_file: no related object.')
        return (None, None, None)
    owner = (orb.get(parms.get('owner_oid') or '')
             or orb.get(parms.get('project_oid') or ''))
    if owner is None:
        orb.log.error('  - new_doc_with_file: no owner and no project.')
        return (None, None, None)
    doc_name = parms.get('name', '') or '.'.join(fname.split('.')[:-1])
    doc_id = (doc_name.replace(' ', '_').lower() + '-'
              + str(uuid4().int)[:6])
    document = new_thing('Document', NOW=NOW,
                         id=doc_id, name=doc_name,
                         description=parms.get('description', '') or '',
                         owner=owner)
    rep_file = new_thing('RepresentationFile', NOW=NOW,
                         id=doc_id + '_file', name=doc_name + ' file',
                         of_object=document,
                         user_file_name=fname,
                         file_size=file_size_of(fpath, parms),
                         # the doc import dialog collects no mime type and
                         # the rpc set none, so every document file in the
                         # repository has a null one.  The file name is the
                         # only evidence there is;  it is better than nothing
                         # and no worse than null.
                         mime_type=(parms.get('mime_type', '')
                                    or mimetypes.guess_type(fname)[0] or ''),
                         checksum=file_checksum(fpath))
    rep_file.url = os.path.join('vault://', orb.get_vault_fname(rep_file))
    doc_ref = new_thing('DocumentReference', NOW=NOW,
                        id=doc_id + '-ref-' + rel_obj.id,
                        name=doc_name + ' Ref to ' + rel_obj.name,
                        description=(f'Document {doc_name} reference to '
                                     f'{rel_obj.name}'),
                        document=document,
                        related_item=rel_obj)
    return (document, doc_ref, rep_file)


def documents_of_local_user():
    """
    The Documents this user created, with the references that attach them to
    something.

    A DocumentReference has no `creator` of its own (see
    `new_doc_with_file()`), so this is how one is found:  by way of the
    Document it belongs to, which does.

    Returns:
        list of tuple:  (Document, [DocumentReference, ...])
    """
    local_user = orb.get(state.get('local_user_oid') or '')
    if local_user is None:
        return []
    found = []
    for obj in local_user.created_objects:
        if obj.__class__.__name__ != 'Document':
            continue
        refs = orb.search_exact(cname='DocumentReference', document=obj) or []
        if refs:
            found.append((obj, list(refs)))
    return found


def vault_path(rep_file):
    """
    Where this machine keeps (or would keep) the file's bytes.

    Args:
        rep_file (RepresentationFile):  the file object

    Returns:
        str:  the path in the local vault
    """
    return orb.get_vault_fpath(rep_file)


def stage_in_vault(rep_file, fpath):
    """
    Put a file's bytes in the local vault, under the name the object implies.

    Done when the object is created rather than when it is uploaded, so that
    the bytes are recoverable from the object alone and survive the user
    moving, renaming or deleting the file they imported.  Without this an
    offline import would hold a RepresentationFile whose file might be gone
    by the time there is a connection to send it over.

    Args:
        rep_file (RepresentationFile):  the file object
        fpath (str):  path to the file to copy in

    Returns:
        str:  the vault path, or '' if the copy failed (which is logged and
        not raised:  the objects are still worth having, and `is_staged()`
        reports the state honestly afterwards).
    """
    dest = vault_path(rep_file)
    if os.path.abspath(fpath) == os.path.abspath(dest):
        return dest
    try:
        shutil.copy(fpath, dest)
    except OSError as e:
        orb.log.error(f'  - could not stage "{fpath}" in the vault: {e}')
        return ''
    return dest


def is_staged(rep_file):
    """
    Say whether this machine holds the file's bytes, in full.

    Size is checked and not only existence, because an interrupted copy or
    download leaves a short file, and a short file is exactly the thing that
    must not be mistaken for the file.

    Args:
        rep_file (RepresentationFile):  the file object

    Returns:
        bool:  True if the vault holds a file of the expected size
    """
    path = vault_path(rep_file)
    try:
        actual = os.path.getsize(path)
    except OSError:
        return False
    expected = int(getattr(rep_file, 'file_size', 0) or 0)
    # a file whose size was never recorded cannot be checked;  its presence
    # is all there is to go on
    return actual == expected if expected else actual > 0


def staged_files_of_local_user():
    """
    The RepresentationFiles this user created that have bytes here to send.

    This is what stands in for a queue of pending uploads.  A queue would be
    a second record of the same fact, and could disagree with the vault --
    the vault cannot disagree with itself.

    Returns:
        list of RepresentationFile:  in creation order, oldest first, so that
        a file referenced by another is sent before the one that references
        it.
    """
    local_user = orb.get(state.get('local_user_oid') or '')
    if local_user is None:
        return []
    cname = 'RepresentationFile'
    rep_files = [o for o in local_user.created_objects
                 if o.__class__.__name__ == cname and is_staged(o)]
    rep_files.sort(key=lambda o: str(getattr(o, 'create_datetime', '')))
    return rep_files
