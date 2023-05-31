-- 테이블 삭제
DROP TABLE "REVIEW" CASCADE CONSTRAINTS;
DROP TABLE "USER_EQUIPS" CASCADE CONSTRAINTS;
DROP TABLE "EQUIP_ENV" CASCADE CONSTRAINTS;
DROP TABLE "EQUIPMENTS" CASCADE CONSTRAINTS;
DROP TABLE "EQUIPMENTS_CATE" CASCADE CONSTRAINTS;
DROP TABLE "USERS" CASCADE CONSTRAINTS;


-- USERS 테이블 생성
CREATE TABLE "USERS" (
    "USER_ID" VARCHAR2(50) NOT NULL,
    "USER_PW" VARCHAR2(255),
    "USER_NAME" VARCHAR2(30),
    "USER_GENDER" CHAR(1),
    "USER_AGE" NUMBER,
    "USER_EMAIL" VARCHAR2(50),
    "CREATION_DATE" DATE DEFAULT SYSDATE,
    CONSTRAINT "PK_USERS" PRIMARY KEY ("USER_ID")
);

-- EQUIPMENTS_CATE 테이블 생성
CREATE TABLE "EQUIPMENTS_CATE" (
    "EQUIP_CATE_NO" NUMBER GENERATED ALWAYS AS IDENTITY,
    "EQUIP_CATE_NM" VARCHAR2(50),
    CONSTRAINT "PK_EQUIP_CATE" PRIMARY KEY ("EQUIP_CATE_NO")
);

-- EQUIPMENTS 테이블 생성
CREATE TABLE "EQUIPMENTS" (
    "EQUIP_NO" NUMBER GENERATED ALWAYS AS IDENTITY,
    "EQUIP_CATE_NO" NUMBER NOT NULL,
    "EQUIP_NM" VARCHAR2(150),
    "EQUIP_PRICE" NUMBER,
    "EQUIP_LINK" VARCHAR2(200),
    "CREATION_DATE" DATE DEFAULT SYSDATE,
    CONSTRAINT "PK_EQUIPMENTS" PRIMARY KEY ("EQUIP_NO"),
    CONSTRAINT "FK_EQUIP_TO_EQUIP_CATE" FOREIGN KEY ("EQUIP_CATE_NO")
        REFERENCES "EQUIPMENTS_CATE" ("EQUIP_CATE_NO")
);
ALTER TABLE EQUIPMENTS ADD CONSTRAINT UQ_EQUIP_NM UNIQUE (EQUIP_NM);

-- EQUIP_ENV 테이블 생성
CREATE TABLE "EQUIP_ENV" (
    "EQUIP_ENV_NO" NUMBER GENERATED ALWAYS AS IDENTITY,
    "USER_ID" VARCHAR2(50) NOT NULL,
    "CREATION_DATE" DATE DEFAULT SYSDATE,
    CONSTRAINT "PK_EQUIP_ENV" PRIMARY KEY ("EQUIP_ENV_NO"),
    CONSTRAINT "FK_USER_TO_EQUIP_ENV" FOREIGN KEY ("USER_ID")
        REFERENCES "USERS" ("USER_ID")
);

-- USER_EQUIPS 테이블 생성
CREATE TABLE "USER_EQUIPS" (
    "USER_EQUIP_NO" NUMBER GENERATED ALWAYS AS IDENTITY,
    "USER_ID" VARCHAR2(50) NOT NULL,
    "EQUIP_NO" NUMBER NOT NULL,
    "EQUIP_ENV_NO" NUMBER NOT NULL,
    "EQUIP_RATING" NUMBER,
    CONSTRAINT "PK_USER_EQUIPS" PRIMARY KEY ("USER_EQUIP_NO"),
    CONSTRAINT "FK_USER_TO_USER_EQUIP" FOREIGN KEY ("USER_ID")
        REFERENCES "USERS" ("USER_ID"),
    CONSTRAINT "FK_EQUIP_TO_USER_EQUIP" FOREIGN KEY ("EQUIP_NO")
        REFERENCES "EQUIPMENTS" ("EQUIP_NO"),
    CONSTRAINT "FK_EQUIP_ENV_TO_USER_EQUIP" FOREIGN KEY ("EQUIP_ENV_NO")
        REFERENCES "EQUIP_ENV" ("EQUIP_ENV_NO")
);

-- REVIEW 테이블 생성
CREATE TABLE "REVIEW" (
    "REVIEW_NO" NUMBER GENERATED ALWAYS AS IDENTITY,
    "EQUIP_ENV_NO" NUMBER NOT NULL,
    "REVIEW_TEXT" VARCHAR2(1000),
    CONSTRAINT "PK_REVIEW" PRIMARY KEY ("REVIEW_NO"),
    CONSTRAINT "FK_EQUIP_ENV_TO_REVIEW" FOREIGN KEY ("EQUIP_ENV_NO")
        REFERENCES "EQUIP_ENV" ("EQUIP_ENV_NO")
);

GRANT SELECT, INSERT, UPDATE, DELETE ON USERS TO DEVENVSHARE;
GRANT SELECT, INSERT, UPDATE, DELETE ON EQUIPMENTS_CATE TO DEVENVSHARE;
GRANT SELECT, INSERT, UPDATE, DELETE ON EQUIPMENTS TO DEVENVSHARE;
GRANT SELECT, INSERT, UPDATE, DELETE ON EQUIP_ENV TO DEVENVSHARE;
GRANT SELECT, INSERT, UPDATE, DELETE ON USER_EQUIPS TO DEVENVSHARE;
GRANT SELECT, INSERT, UPDATE, DELETE ON REVIEW TO DEVENVSHARE;


-- EQUIPMENTS_CATE에 데이터 삽입
INSERT INTO EQUIPMENTS_CATE (EQUIP_CATE_NM) VALUES ('Monitor');
INSERT INTO EQUIPMENTS_CATE (EQUIP_CATE_NM) VALUES ('Keyboard');
INSERT INTO EQUIPMENTS_CATE (EQUIP_CATE_NM) VALUES ('Mouse');
INSERT INTO EQUIPMENTS_CATE (EQUIP_CATE_NM) VALUES ('Desk');
INSERT INTO EQUIPMENTS_CATE (EQUIP_CATE_NM) VALUES ('Chair');

-- EQUIPMENTS_CATE 테이블 내용 조회
SELECT * FROM EQUIPMENTS_CATE;

-- EQUIP_CATE_NO 컬럼 정보 조회
SELECT *
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'EQUIPMENTS_CATE' AND COLUMN_NAME = 'EQUIP_CATE_NO';

SELECT COUNT(*) FROM EQUIPMENTS;
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE, TABLE_NAME, SEARCH_CONDITION
FROM USER_CONSTRAINTS
WHERE TABLE_NAME = 'EQUIPMENTS';