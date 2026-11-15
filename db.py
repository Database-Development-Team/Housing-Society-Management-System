
import os

import oracledb
from dotenv import load_dotenv

# Read our private database configuration
load_dotenv()

# Enable Thick mode for Oracle 11g XE
oracledb.init_oracle_client(
    lib_dir=os.environ["ORACLE_CLIENT_LIB_DIR"]
)


def get_connection():
    dsn = oracledb.makedsn(
        os.environ["DB_HOST"],
        int(os.environ["DB_PORT"]),
        sid=os.environ["DB_SID"]
    )

    return oracledb.connect(
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dsn=dsn
    )
