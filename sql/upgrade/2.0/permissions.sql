/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

\set ON_ERROR_STOP 1

alter default privileges for role processor grant all on tables to breakpad_rw;
alter default privileges for role processor grant all on sequences to breakpad_rw;

alter default privileges for role monitor grant all on tables to breakpad_rw;
alter default privileges for role monitor grant all on sequences to breakpad_rw;

grant insert,update,delete,select on all tables in schema public to breakpad_rw;
grant usage,select,update on all sequences in schema public to breakpad_rw;


