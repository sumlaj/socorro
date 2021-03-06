# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import psycopg2

from socorro.external.postgresql.base import PostgreSQLBase
from socorro.external import MissingOrBadArgumentError
from socorro.lib import external_common

import socorro.database.database as db

logger = logging.getLogger("webapi")


class Priorityjobs(PostgreSQLBase):
    """Implement the /priorityjobs service with PostgreSQL.
    """

    def post(self, *args, **kwargs):
        # because this implementation can accept both
        return self.get(*args, **kwargs)

    def get(self, **kwargs):
        """Return a job in the priority queue. """
        filters = [
            ("uuid", None, "str"),
        ]
        params = external_common.parse_arguments(filters, kwargs)

        if not params.uuid:
            raise MissingOrBadArgumentError(
                        "Mandatory parameter 'uuid' is missing or empty")

        sql = """
            /* socorro.external.postgresql.priorityjobs.Priorityjobs.get */
            SELECT uuid FROM priorityjobs WHERE uuid=%(uuid)s
        """

        json_result = {
            "total": 0,
            "hits": []
        }

        try:
            # Creating the connection to the DB
            connection = self.database.connection()
            cur = connection.cursor()
            results = db.execute(cur, sql, params)
        except psycopg2.Error:
            logger.error("Failed retrieving priorityjobs data from PostgreSQL",
                         exc_info=True)
        else:
            for job in results:
                row = dict(zip(("uuid",), job))
                json_result["hits"].append(row)
            json_result["total"] = len(json_result["hits"])
        finally:
            connection.close()

        return json_result

    def create(self, **kwargs):
        """Add a new job to the priority queue if not already in that queue.
        """
        filters = [
            ("uuid", None, "str"),
        ]
        params = external_common.parse_arguments(filters, kwargs)

        if not params.uuid:
            raise MissingOrBadArgumentError(
                        "Mandatory parameter 'uuid' is missing or empty")

        sql = """
            /* socorro.external.postgresql.priorityjobs.Priorityjobs.create */
            INSERT INTO priorityjobs (uuid) VALUES (%(uuid)s)
        """

        sql_exists = """
            /* socorro.external.postgresql.priorityjobs.Priorityjobs.create */
            SELECT 1 FROM priorityjobs WHERE uuid=%(uuid)s
        """

        try:
            connection = self.database.connection()
            cur = connection.cursor()

            # Verifying that the uuid is not already in the queue
            cur.execute(sql_exists, params)
            if cur.rowcount:
                logger.debug('The uuid %s is already in the priorityjobs '
                             'table' % params.uuid)
                return False

            logger.debug('Adding the uuid %s to the priorityjobs table' %
                         params.uuid)
            cur.execute(sql, params)
        except psycopg2.Error:
            logger.error("Failed inserting priorityjobs data into PostgreSQL",
                         exc_info=True)
            connection.rollback()
            return False
        else:
            connection.commit()
            return bool(cur.rowcount)
        finally:
            connection.close()

        return True
