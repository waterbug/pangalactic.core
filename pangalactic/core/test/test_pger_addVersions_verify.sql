/* This is a database command to verify that the new test version for the "Flux
   Capacitor" has been added and all its attributes set properly.

   usage:

   psql pgerdb < test_pger_addVersions_verify.sql
*/
select _oid, _base_id, _id, _name, _iteration, _version, _is_head from _part where _name = 'Flux Capacitor';

