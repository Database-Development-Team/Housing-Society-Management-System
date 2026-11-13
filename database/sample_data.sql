
-- ==============================================
-- HOUSING SOCIETY MANAGEMENT SYSTEM (HSMS)
-- SAMPLE DATA SCRIPT
-- DATABASE: ORACLE 11G XE
-- SCHEMA: HSMS_APP
-- ==============================================


-- =====================================
-- TABLE 1: OWNER
-- =====================================

INSERT INTO OWNER
(
    OWNER_ID,
    FIRST_NAME,
    LAST_NAME,
    CNIC_NUMBER,
    MOBILE_NUMBER,
    EMAIL_ADDRESS
)
VALUES
(
    1,
    'AHMED',
    'KHAN',
    '3520212345674',
    '03001234567',
    'ahmed@example.com'
);


-- =====================================
-- TABLE 2: TENANT
-- =====================================

INSERT INTO TENANT
(
    TENANT_ID,
    FULL_NAME,
    CNIC_NUMBER,
    CONTACT_NUMBER,
    FAMILY_MEMBERS_COUNT
)
VALUES
(
    1,
    'AHMED ALI',
    '3520212345671',
    '03001234567',
    4
);


-- =====================================
-- TABLE 3: EMPLOYEE
-- =====================================

INSERT INTO EMPLOYEE
(
    EMPLOYEE_ID,
    EMP_FULL_NAME,
    JOB_ROLE,
    SHIFT_TIMING,
    MONTHLY_SALARY,
    CONTACT_NUMBER,
    CNIC_NUMBER
)
VALUES
(
    1,
    'MUHAMMAD ALI',
    'SECURITY GUARD',
    '08:00 - 16:00',
    45000,
    '03001234567',
    '3520212345672'
);


-- =====================================
-- TABLE 4: FACILITY
-- =====================================

INSERT INTO FACILITY
(
    FACILITY_ID,
    FACILITY_NAME,
    LOCATION_BLOCK,
    MAX_CAPACITY,
    OPERATIONAL_HOURS,
    BOOKING_FEE,
    MAINTENANCE_SCHEDULE
)
VALUES
(
    1,
    'COMMUNITY HALL',
    'BLOCK A',
    200,
    '09:00 - 23:00',
    15000,
    'EVERY MONDAY'
);


INSERT INTO FACILITY
(
    FACILITY_ID,
    FACILITY_NAME,
    LOCATION_BLOCK,
    MAX_CAPACITY,
    OPERATIONAL_HOURS,
    BOOKING_FEE,
    MAINTENANCE_SCHEDULE
)
VALUES
(
    2,
    'GYMNASIUM',
    'BLOCK B',
    50,
    '06:00 - 22:00',
    1000,
    'EVERY SUNDAY'
);


-- =====================================
-- TABLE 5: HOUSE
-- =====================================

INSERT INTO HOUSE
(
    HOUSE_ID,
    HOUSE_NO,
    STREET_NUMBER,
    BLOCK_NAME,
    SIZE_IN_MARLA,
    CONSTRUCTION_STATUS,
    OCCUPANCY_STATUS,
    OWNER_ID
)
VALUES
(
    1,
    '101',
    '5',
    'BLOCK A',
    10,
    'COMPLETED',
    'VACANT',
    1
);


-- =====================================
-- TABLE 6: LEASE
-- =====================================

INSERT INTO LEASE
(
    LEASE_ID,
    HOUSE_ID,
    TENANT_ID,
    LEASE_START_DATE,
    LEASE_END_DATE,
    RENT_AMOUNT,
    POLICE_VERIFICATION_STATUS,
    LEASE_STATUS
)
VALUES
(
    1,
    1,
    1,
    TRUNC(SYSDATE),
    ADD_MONTHS(TRUNC(SYSDATE), 12) - 1,
    35000,
    'PENDING',
    'PENDING'
);


-- =====================================
-- SAVE ALL INSERTED RECORDS
-- =====================================

COMMIT;

-- =====================================
-- SAMPLE DATA: RESIDENT
-- =====================================

INSERT INTO RESIDENT
(
    RESIDENT_ID,
    FULL_NAME,
    CNIC_NUMBER,
    CONTACT_NUMBER,
    RELATION_TYPE,
    MOVE_IN_DATE,
    HOUSE_ID,
    OWNER_ID
)
VALUES
(
    1,
    'AHMED KHAN',
    '3520212345674',
    '03001234567',
    'OWNER',
    TRUNC(SYSDATE),
    1,
    1
);

-- HOUSE 1 IS NOW OWNER-OCCUPIED

UPDATE HOUSE
SET OCCUPANCY_STATUS = 'OWNER-OCCUPIED'
WHERE HOUSE_ID = 1;

COMMIT;

-- =====================================
-- SAMPLE DATA: VEHICLE
-- =====================================

INSERT INTO VEHICLE
(
    VEHICLE_ID,
    LICENSE_PLATE_NO,
    VEHICLE_MAKE,
    VEHICLE_MODEL,
    VEHICLE_COLOR,
    PARKING_STICKER_NO,
    STICKER_EXPIRY_DATE,
    RESIDENT_ID
)
VALUES
(
    1,
    'LEA-1234',
    'TOYOTA',
    'COROLLA',
    'WHITE',
    'HSMS-001',
    ADD_MONTHS(TRUNC(SYSDATE), 12),
    1
);

INSERT INTO VEHICLE
(
    VEHICLE_ID,
    LICENSE_PLATE_NO,
    VEHICLE_MAKE,
    VEHICLE_MODEL,
    VEHICLE_COLOR,
    PARKING_STICKER_NO,
    STICKER_EXPIRY_DATE,
    RESIDENT_ID
)
VALUES
(
    2,
    'LEB-5678',
    'HONDA',
    'CIVIC',
    'BLACK',
    NULL,
    NULL,
    1
);

COMMIT;
