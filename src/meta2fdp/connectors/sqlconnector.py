"""Example SQL connector implementation for connecting to a mssql database and retrieving metadata related to datasets and catalogs. This is a basic implementation and can be extended with additional functionality as needed."""

from pymssql import connect
from meta2fdp.config.connector.sqlconnector import SQLConnectorConfig


class SQLConnector:
    def __init__(self, config: SQLConnectorConfig):
        self.config = config

    def connect_to_sql(self):
        """Connect to a mssql database and build an interface for it.
        Database should exists in network

        :return: mssql interface
        :rtype: Cursor object.

        """
        conn = connect(
            server=self.config.environmentprovider.get_info("SQL_SERVER"),
            user=self.config.environmentprovider.get_info("SQL_USERNAME"),
            password=self.config.keyringprovider.get_info(
                service_name=self.config.environmentprovider.get_info(
                    "SQL_KEYRING_SERVICE"
                ),
                username=self.config.environmentprovider.get_info("SQL_USERNAME"),
            ),
            database=self.config.environmentprovider.get_info("SQL_DATABASE_NAME"),
            tds_version=self.config.tds_version,
        )
        cursor = conn.cursor(as_dict=True)
        return cursor

    def dataset_sql_query(self, cursor, dataset_id):
        """SQL dataset query generator that should result in
            the metadata related to the dataset with dataset_id

        :param cursor: connection to a mssql database
        :type cursor: Cursor object
        :param dataset_id: dataset SQL index
        :type dataset_id: str
        :return: output of mssql database
        :rtype: Cursor object

        """

        def dataset_sql_query_constructor(table_name, dataset_id) -> str:
            dataset_query = (
                "select * from "
                + str(table_name)
                + " where identifier = '"
                + str(dataset_id)
                + "';"
            )
            return dataset_query

        table_name = self.config.dataset_id
        dataset_query = dataset_sql_query_constructor(table_name, dataset_id)
        cursor.execute(dataset_query)
        return cursor

    def catalog_sql_query(self, cursor):
        """SQL catalog query generator that should result in
         the metadata related to the catalog or database

        :param cursor: connection to a mssql database
        :type cursor: Cursor object
        :return: output of mssql database
        :rtype: Cursor object

        """

        def catalog_sql_query_constructor(table_name) -> str:
            catalog_query = "select * from " + str(table_name) + ";"
            return catalog_query

        catalog_query = catalog_sql_query_constructor(self.config.catalog_id)
        cursor.execute(catalog_query)
        return cursor
