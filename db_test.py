
import os

import oracledb
from dotenv import load_dotenv

# Load database settings from .env
load_dotenv()

# Enable Thick mode for Oracle 11g
oracledb.init_oracle_client(
    lib_dir=os.environ["ORACLE_CLIENT_LIB_DIR"]
)

# Build connection address
dsn = oracledb.makedsn(
    os.environ["DB_HOST"],
    int(os.environ["DB_PORT"]),
    sid=os.environ["DB_SID"]
)

# Connect to Oracle
try:
    with oracledb.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dsn=dsn
    ) as connection:

        print("Database connection successful!")
        print("Connected using Thick mode:", not connection.thin)

        with connection.cursor() as cursor:

            cursor.execute("SELECT USER FROM DUAL")
            print("Connected schema:", cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM OWNER")
            print("Total registered owners:", cursor.fetchone()[0])

except oracledb.Error as error:
    print("Oracle connection failed:")
    print(error)
