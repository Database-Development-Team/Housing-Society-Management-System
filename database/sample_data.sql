
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

-- =====================================
-- SAMPLE DATA: VISITOR
-- =====================================

-- Visitor 1: Completed visit

INSERT INTO VISITOR
(
    VISITOR_ID,
    VISITOR_NAME,
    CNIC_NUMBER,
    VEHICLE_REGISTRATION,
    ENTRY_TIME,
    EXIT_TIME,
    PURPOSE_OF_VISIT,
    HOUSE_ID
)
VALUES
(
    1,
    'BILAL AHMED',
    '3520212345675',
    'LEC-9876',
    SYSDATE - (2/24),
    SYSDATE - (1/24),
    'PERSONAL VISIT',
    1
);


-- Visitor 2: Currently inside society

INSERT INTO VISITOR
(
    VISITOR_ID,
    VISITOR_NAME,
    CNIC_NUMBER,
    VEHICLE_REGISTRATION,
    ENTRY_TIME,
    PURPOSE_OF_VISIT,
    HOUSE_ID
)
VALUES
(
    2,
    'USMAN KHAN',
    '3520212345676',
    NULL,
    SYSDATE,
    'FAMILY VISIT',
    1
);

COMMIT;


-- =====================================
-- SAMPLE DATA: MAINTENANCE_BILL
-- =====================================

-- BILL 1: CURRENT MONTH, UNPAID

INSERT INTO MAINTENANCE_BILL
(
    BILL_ID,
    BILLING_MONTH,
    TOTAL_AMOUNT,
    DUE_DATE,
    PAYMENT_STATUS,
    HOUSE_ID,
    EMPLOYEE_ID
)
VALUES
(
    1,
    TRUNC(SYSDATE, 'MM'),
    5000,
    TRUNC(SYSDATE, 'MM') + 15,
    'UNPAID',
    1,
    1
);


-- BILL 2: PREVIOUS MONTH, PAID

INSERT INTO MAINTENANCE_BILL
(
    BILL_ID,
    BILLING_MONTH,
    TOTAL_AMOUNT,
    DUE_DATE,
    PAYMENT_STATUS,
    PAYMENT_DATE,
    PAYMENT_METHOD,
    HOUSE_ID,
    EMPLOYEE_ID
)
VALUES
(
    2,
    ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -1),
    5000,
    ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -1) + 15,
    'PAID',
    ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -1) + 10,
    'CASH',
    1,
    1
);

COMMIT;

-- =====================================
-- SAMPLE DATA: COMPLAINT
-- =====================================

-- COMPLAINT 1: OPEN COMPLAINT

INSERT INTO COMPLAINT
(
    COMPLAINT_ID,
    COMPLAINT_CATEGORY,
    ISSUE_DESCRIPTION,
    DATE_REPORTED,
    COMPLAINT_STATUS,
    HOUSE_ID
)
VALUES
(
    1,
    'WATER SUPPLY',
    'LOW WATER PRESSURE IN THE HOUSE',
    SYSDATE,
    'OPEN',
    1
);


-- COMPLAINT 2: RESOLVED COMPLAINT

INSERT INTO COMPLAINT
(
    COMPLAINT_ID,
    COMPLAINT_CATEGORY,
    ISSUE_DESCRIPTION,
    DATE_REPORTED,
    DATE_RESOLVED,
    COMPLAINT_STATUS,
    HOUSE_ID
)
VALUES
(
    2,
    'ELECTRICITY',
    'STREETLIGHT NOT WORKING NEAR HOUSE',
    TRUNC(SYSDATE) - 10,
    TRUNC(SYSDATE) - 8,
    'RESOLVED',
    1
);

COMMIT;

-- ADDITIONAL SAMPLE EMPLOYEE

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
    2,
    'HASSAN RAZA',
    'MAINTENANCE TECHNICIAN',
    '09:00 - 17:00',
    50000,
    '03009876543',
    '3520212345677'
);


-- =====================================
-- SAMPLE DATA: COMPLAINT_ASSIGNMENT
-- =====================================

-- COMPLAINT 1 ASSIGNED TO EMPLOYEE 1

INSERT INTO COMPLAINT_ASSIGNMENT
(
    COMPLAINT_ID,
    EMPLOYEE_ID,
    ASSIGNMENT_DATE,
    ASSIGNMENT_STATUS
)
VALUES
(
    1,
    1,
    SYSDATE,
    'ASSIGNED'
);


-- COMPLAINT 1 ASSIGNED TO EMPLOYEE 2

INSERT INTO COMPLAINT_ASSIGNMENT
(
    COMPLAINT_ID,
    EMPLOYEE_ID,
    ASSIGNMENT_DATE,
    ASSIGNMENT_STATUS
)
VALUES
(
    1,
    2,
    SYSDATE,
    'ASSIGNED'
);


-- COMPLAINT 2 HANDLED BY EMPLOYEE 1

INSERT INTO COMPLAINT_ASSIGNMENT
(
    COMPLAINT_ID,
    EMPLOYEE_ID,
    ASSIGNMENT_DATE,
    ASSIGNMENT_STATUS
)
VALUES
(
    2,
    1,
    TRUNC(SYSDATE) - 9,
    'COMPLETED'
);

COMMIT;


-- =====================================
-- SAMPLE DATA: BOOKING
-- =====================================

-- BOOKING 1: COMMUNITY HALL, PENDING
-- TWO DAYS FROM TODAY, 10 AM TO 12 PM

INSERT INTO BOOKING
(
    BOOKING_ID,
    EVENT_TIME_START,
    EVENT_TIME_END,
    TOTAL_CALCULATED_FEE,
    PAYMENT_STATUS,
    BOOKING_STATUS,
    FACILITY_ID,
    HOUSE_ID
)
VALUES
(
    1,
    TRUNC(SYSDATE) + 2 + (10/24),
    TRUNC(SYSDATE) + 2 + (12/24),
    15000,
    'UNPAID',
    'PENDING',
    1,
    1
);


-- BOOKING 2: GYMNASIUM, APPROVED
-- THREE DAYS FROM TODAY, 4 PM TO 5 PM

INSERT INTO BOOKING
(
    BOOKING_ID,
    EVENT_TIME_START,
    EVENT_TIME_END,
    TOTAL_CALCULATED_FEE,
    PAYMENT_STATUS,
    BOOKING_STATUS,
    FACILITY_ID,
    HOUSE_ID
)
VALUES
(
    2,
    TRUNC(SYSDATE) + 3 + (16/24),
    TRUNC(SYSDATE) + 3 + (17/24),
    1000,
    'PAID',
    'APPROVED',
    2,
    1
);

COMMIT;
