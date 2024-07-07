import pandas as pd
import psycopg2
import argparse
import logging
from prettytable import PrettyTable
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_database_info(conn, dbname):
    info = {}
    try:
        with conn.cursor() as cursor:
            # Database size
            cursor.execute(f"SELECT pg_database_size('{dbname}') as size;")
            size = cursor.fetchone()[0]
            info["Size"] = size
            logging.info(f"Retrieved size for database: {dbname}")

            # Table count
            cursor.execute(
                f"""
                SELECT count(*)
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
            )
            table_count = cursor.fetchone()[0]
            info["TableCount"] = table_count
            logging.info(f"Retrieved table count for database: {dbname}")

            # Row count
            cursor.execute(
                f"""
                SELECT sum(n_live_tup)
                FROM pg_stat_user_tables;
            """
            )
            row_count = cursor.fetchone()[0]
            info["RowCount"] = row_count
            logging.info(f"Retrieved row count for database: {dbname}")

            # Schemas
            cursor.execute(
                f"""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT LIKE 'pg_%' AND schema_name <> 'information_schema';
            """
            )
            schemas = [row[0] for row in cursor.fetchall()]
            info["Schemas"] = schemas
            logging.info(f"Retrieved schemas for database: {dbname}")

            # Tables
            schema_tables = {}
            for schema in schemas:
                cursor.execute(
                    f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}';
                """
                )
                tables = [row[0] for row in cursor.fetchall()]
                schema_tables[schema] = tables

            info["Tables"] = schema_tables
            logging.info(f"Retrieved tables for database: {dbname}")

            # Routines
            schema_routines = {}
            for schema in schemas:
                cursor.execute(
                    f"""
                    SELECT routine_name, routine_type
                    FROM information_schema.routines
                    WHERE specific_schema = '{schema}';
                """
                )
                routines = cursor.fetchall()
                schema_routines[schema] = routines

            info["Routines"] = schema_routines
            logging.info(f"Retrieved routines for database: {dbname}")

            # PostgreSQL version
            cursor.execute("SELECT version();")
            postgres_version = cursor.fetchone()[0]
            info["PostgresVersion"] = postgres_version
            logging.info(f"Retrieved PostgreSQL version for database: {dbname}")

            # Extensions versions
            cursor.execute(
                """
                SELECT extname, extversion
                FROM pg_extension;
            """
            )
            extensions = cursor.fetchall()
            info["Extensions"] = extensions
            logging.info(f"Retrieved extensions for database: {dbname}")

    except psycopg2.errors.InsufficientPrivilege:
        logging.warning(f"Insufficient privileges for database: {dbname}")
        return None

    return info


def list_databases(host, port, user, password, dbname, sort_by, output_file):
    db_list = []

    try:
        logging.info("Connecting to the main database...")
        with psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        ) as conn:
            logging.info(
                "Connected to the main database. Retrieving list of databases..."
            )
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT datname FROM pg_database WHERE datistemplate = false;"
                )
                databases = cursor.fetchall()

                for db in databases:
                    dbname = db[0]
                    logging.info(f"Processing database: {dbname}")
                    try:
                        with psycopg2.connect(
                            host=host,
                            port=port,
                            user=user,
                            password=password,
                            dbname=dbname,
                        ) as db_conn:
                            db_info = get_database_info(db_conn, dbname)
                            if db_info is not None:
                                db_info["Database"] = dbname
                                db_list.append(db_info)
                    except psycopg2.Error as e:
                        logging.error(f"Error connecting to database {dbname}: {e}")

            # Add the database name as the first column
            for db_info in db_list:
                db_info.update(
                    (k, [dbname] + v if isinstance(v, list) else v)
                    for k, v in db_info.items()
                )

            df = pd.DataFrame(db_list)

            if sort_by == "alphabet":
                logging.info("Sorting databases alphabetically")
                df.sort_values(by="Database", inplace=True)
            elif sort_by == "size":
                logging.info("Sorting databases by size")
                df.sort_values(by="Size", inplace=True, ascending=False)
            elif sort_by == "tables":
                logging.info("Sorting databases by table count")
                df.sort_values(by="TableCount", inplace=True, ascending=False)
            elif sort_by == "rows":
                logging.info("Sorting databases by row count")
                df.sort_values(by="RowCount", inplace=True, ascending=False)

            # Enhance output with better formatting
            pd.set_option("display.float_format", lambda x: "%.2f" % x)

            summary_table = PrettyTable()
            summary_table.field_names = [
                "Database",
                "Size (MB)",
                "Table Count",
                "Row Count",
            ]
            summary_table.align["Database"] = "l"
            summary_table.align["Size (MB)"] = "l"
            summary_table.align["Table Count"] = "l"
            summary_table.align["Row Count"] = "l"
            for index, row in df.iterrows():
                summary_table.add_row(
                    [
                        row["Database"],
                        f"{row['Size'] / (1024**2):.2f}",
                        row["TableCount"],
                        row["RowCount"],
                    ]
                )

            output_summary = "\nSummary of Databases:\n" + summary_table.get_string()
            print(output_summary)

            detailed_output = []

            # Detailed information
            for db_info in db_list:
                db_summary = f"\n{'='*60}\n"
                db_summary += f"Database: {db_info['Database']}\n"
                db_summary += f"{'-'*60}\n"
                db_summary += f"Size: {db_info['Size'] / (1024**2):.2f} MB\n"
                db_summary += f"Table Count: {db_info['TableCount']}\n"
                db_summary += f"Row Count: {db_info['RowCount']}\n"
                db_summary += f"Schemas: {', '.join(db_info['Schemas'])}\n"
                db_summary += f"PostgreSQL Version: {db_info['PostgresVersion']}\n"

                table = PrettyTable()
                table.field_names = ["Database", "Schema", "Table"]
                table.align["Database"] = "l"
                table.align["Schema"] = "l"
                table.align["Table"] = "l"
                for schema, tables in db_info["Tables"].items():
                    for table_name in tables:
                        table.add_row([db_info["Database"], schema, table_name])
                db_summary += table.get_string()

                routine_table = PrettyTable()
                routine_table.field_names = [
                    "Database",
                    "Schema",
                    "Routine Type",
                    "Routine Name",
                ]
                routine_table.align["Database"] = "l"
                routine_table.align["Schema"] = "l"
                routine_table.align["Routine Type"] = "l"
                routine_table.align["Routine Name"] = "l"
                for schema, routines in db_info["Routines"].items():
                    for routine_name, routine_type in routines:
                        routine_table.add_row(
                            [db_info["Database"], schema, routine_type, routine_name]
                        )
                db_summary += "\n" + routine_table.get_string()

                extensions_table = PrettyTable()
                extensions_table.field_names = ["Extension Name", "Version"]
                extensions_table.align["Extension Name"] = "l"
                extensions_table.align["Version"] = "l"
                for ext in db_info["Extensions"]:
                    # Print ext to see what it contains
                    # logging.info(f"Extension content: {ext}")
                    if isinstance(ext, tuple):
                        extname, extversion = ext[:2]
                        extensions_table.add_row([extname, extversion])
                    else:
                        extensions_table.add_row([ext, "N/A"])
                db_summary += "\n" + extensions_table.get_string()

                db_summary += f"\n{'='*60}"
                detailed_output.append(db_summary)

            full_output = output_summary + "\n" + "\n".join(detailed_output)

            # Determine the output file path
            if not output_file or not os.path.isdir(os.path.dirname(output_file)):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"db_summary_{timestamp}.txt"

            # Save to file
            with open(output_file, "w") as f:
                f.write(full_output)

            logging.info(f"Output saved to file: {output_file}")
            print(f"Output saved to file: {os.path.abspath(output_file)}")

            # Display content saved in the file
            with open(output_file, "r") as f:
                file_content = f.read()
                print("\nFile Content:\n")
                print(file_content)

    except psycopg2.Error as e:
        logging.error(f"Error connecting to the main database: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List PostgreSQL databases")
    parser.add_argument("--db_host", required=True, help="Database host")
    parser.add_argument("--db_port", required=True, help="Database port")
    parser.add_argument("--db_user", required=True, help="Database user")
    parser.add_argument("--db_password", required=True, help="Database password")
    parser.add_argument("--db_name", required=True, help="Database name")
    parser.add_argument(
        "--sort_by",
        choices=["alphabet", "size", "tables", "rows"],
        default="alphabet",
        help="Sort databases by criteria",
    )
    parser.add_argument("--output_file", help="Output file path")

    args = parser.parse_args()

    logging.info("Starting database listing script")
    list_databases(
        args.db_host,
        args.db_port,
        args.db_user,
        args.db_password,
        args.db_name,
        args.sort_by,
        args.output_file,
    )
    logging.info("Database listing completed")
