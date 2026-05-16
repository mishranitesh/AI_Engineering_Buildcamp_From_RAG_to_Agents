import os
import urllib.request

import duckdb

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
PARQUET_FILE = "yellow_tripdata_2024-01.parquet"

con = duckdb.connect("taxi.db")


def setup_database():
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(PARQUET_FILE):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, PARQUET_FILE)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM '{PARQUET_FILE}'
    """)
    count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Loaded {count} rows")
    return count

class SQLTools:

    def get_schema(self) -> str:
        """Return schema for trips table."""
        result = con.execute("DESCRIBE trips").fetchall()

        lines = []
        for row in result:
            lines.append(f"{row[0]} - {row[1]}")

        return "\n".join(lines)

    def run_sql(self, query: str) -> str:
        """Execute SQL query and return results."""
        result = con.execute(query)

        columns = [desc[0] for desc in result.description]
        rows = result.fetchmany(50)

        output = []

        output.append(" | ".join(columns))
        output.append("-" * 50)

        for row in rows:
            output.append(" | ".join(str(x) for x in row))

        return "\n".join(output)
    
if __name__ == "__main__":
    count = setup_database()
    print(count)
