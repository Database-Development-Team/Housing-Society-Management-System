
-- ====================================================
-- HOUSING SOCIETY MANAGEMENT SYSTEM (HSMS)
-- DATABASE QUERIES
-- DATABASE: ORACLE 11G XE
-- SCHEMA: HSMS_APP
-- ====================================================


-- ====================================================
-- SECTION 1: DATABASE AND SCHEMA VERIFICATION
-- ====================================================

-- Query 1: Check the currently connected database user

SELECT USER FROM DUAL;


-- Query 2: Display all tables in the current schema

SELECT TABLE_NAME
FROM USER_TABLES
ORDER BY TABLE_NAME;


-- Query 3: Verify whether OWNER table exists

SELECT TABLE_NAME
FROM USER_TABLES
WHERE TABLE_NAME = 'OWNER';


-- Query 4: Display OWNER table columns and datatypes

SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'OWNER'
ORDER BY COLUMN_ID;


-- Query 5: Display OWNER table constraints

SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
FROM USER_CONSTRAINTS
WHERE TABLE_NAME = 'OWNER';


-- Query 6: Verify OWNER columns after removing IS_RESIDENT

SELECT COLUMN_NAME, DATA_TYPE
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'OWNER'
ORDER BY COLUMN_ID;



-- ====================================================
-- SECTION 2: OWNER TABLE
-- ====================================================

-- Query 7: Display all owners

SELECT *
FROM OWNER;


-- Query 8: Display owner IDs and names

SELECT
    OWNER_ID,
    FIRST_NAME,
    LAST_NAME
FROM OWNER;



-- ====================================================
-- SECTION 3: TENANT TABLE
-- ====================================================

-- Query 9: Display all tenants

SELECT *
FROM TENANT;


-- Query 10: Display tenant IDs and names

SELECT
    TENANT_ID,
    FULL_NAME
FROM TENANT;



-- ====================================================
-- SECTION 4: EMPLOYEE TABLE
-- ====================================================

-- Query 11: Display all employees

SELECT *
FROM EMPLOYEE;


-- Query 12: Display employee details

SELECT
    EMPLOYEE_ID,
    EMP_FULL_NAME,
    JOB_ROLE,
    MONTHLY_SALARY,
    STATUS
FROM EMPLOYEE;



-- ====================================================
-- SECTION 5: FACILITY TABLE
-- ====================================================

-- Query 13: Display all facilities

SELECT *
FROM FACILITY;


-- Query 14: Display facility information

SELECT
    FACILITY_ID,
    FACILITY_NAME,
    LOCATION_BLOCK,
    MAX_CAPACITY,
    BOOKING_FEE,
    OPERATIONAL_STATUS
FROM FACILITY
ORDER BY FACILITY_ID;



-- ====================================================
-- SECTION 6: HOUSE TABLE
-- ====================================================

-- Query 15: Display all houses

SELECT *
FROM HOUSE;


-- Query 16: Display house IDs and house numbers

SELECT
    HOUSE_ID,
    HOUSE_NO
FROM HOUSE;


-- Query 17: Check whether House ID 1 exists

SELECT
    HOUSE_ID,
    HOUSE_NO
FROM HOUSE
WHERE HOUSE_ID = 1;


-- Query 18: Display houses with their owners

SELECT
    H.HOUSE_ID,
    H.HOUSE_NO,
    H.BLOCK_NAME,
    H.SIZE_IN_MARLA,
    H.OCCUPANCY_STATUS,
    O.FIRST_NAME || ' ' || O.LAST_NAME
        AS OWNER_NAME
FROM HOUSE H
JOIN OWNER O
    ON H.OWNER_ID = O.OWNER_ID;



-- ====================================================
-- SECTION 7: LEASE TABLE
-- ====================================================

-- Query 19: Display all leases

SELECT *
FROM LEASE;


-- Query 20: Display lease information with
-- house details and tenant names

SELECT
    L.LEASE_ID,
    H.HOUSE_NO,
    H.BLOCK_NAME,
    T.FULL_NAME AS TENANT_NAME,
    L.RENT_AMOUNT,
    L.LEASE_START_DATE,
    L.LEASE_END_DATE,
    L.LEASE_STATUS
FROM LEASE L
JOIN HOUSE H
    ON L.HOUSE_ID = H.HOUSE_ID
JOIN TENANT T
    ON L.TENANT_ID = T.TENANT_ID;



-- ====================================================
-- SECTION 8: RESIDENT TABLE
-- ====================================================

-- Query 21: Display all residents

SELECT *
FROM RESIDENT;


-- Query 22: Display resident IDs, names and houses

SELECT
    RESIDENT_ID,
    FULL_NAME,
    HOUSE_ID
FROM RESIDENT;


-- Query 23: Display residents with house
-- information and owner details

SELECT
    R.RESIDENT_ID,
    R.FULL_NAME AS RESIDENT_NAME,
    R.RELATION_TYPE,
    H.HOUSE_NO,
    H.BLOCK_NAME,
    O.FIRST_NAME || ' ' || O.LAST_NAME
        AS OWNER_NAME,
    R.MOVE_IN_DATE,
    H.OCCUPANCY_STATUS
FROM RESIDENT R
JOIN HOUSE H
    ON R.HOUSE_ID = H.HOUSE_ID
LEFT JOIN OWNER O
    ON R.OWNER_ID = O.OWNER_ID;



-- ====================================================
-- SECTION 9: VEHICLE TABLE
-- ====================================================

-- Query 24: Display all registered vehicles

SELECT *
FROM VEHICLE;


-- Query 25: Display vehicles with their
-- registered residents and house details
-- Updated relationship: VEHICLE -> RESIDENT -> HOUSE

SELECT
    V.VEHICLE_ID,
    V.LICENSE_PLATE_NO,
    V.VEHICLE_MAKE,
    V.VEHICLE_MODEL,
    R.FULL_NAME AS RESIDENT_NAME,
    H.HOUSE_NO,
    H.BLOCK_NAME
FROM VEHICLE V
JOIN RESIDENT R
    ON V.RESIDENT_ID = R.RESIDENT_ID
JOIN HOUSE H
    ON R.HOUSE_ID = H.HOUSE_ID
ORDER BY V.VEHICLE_ID;



-- ====================================================
-- SECTION 10: DATABASE RECORD COUNT
-- ====================================================

-- Query 26: Count records in every created table

SELECT 'OWNER' AS TABLE_NAME,
       COUNT(*) AS TOTAL
FROM OWNER

UNION ALL

SELECT 'TENANT', COUNT(*)
FROM TENANT

UNION ALL

SELECT 'EMPLOYEE', COUNT(*)
FROM EMPLOYEE

UNION ALL

SELECT 'FACILITY', COUNT(*)
FROM FACILITY

UNION ALL

SELECT 'HOUSE', COUNT(*)
FROM HOUSE

UNION ALL

SELECT 'LEASE', COUNT(*)
FROM LEASE

UNION ALL

SELECT 'RESIDENT', COUNT(*)
FROM RESIDENT

UNION ALL

SELECT 'VEHICLE', COUNT(*)
FROM VEHICLE;
