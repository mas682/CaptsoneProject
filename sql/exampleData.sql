--Jonathan Zhang
--CS 1980
--Test file for sql tables, functions
INSERT INTO users VALUES(1,'abc@123.com',123,NULL,true);
INSERT INTO USERS VALUES(2,'abc@123.com',123,NULL,true);
INSERT INTO USERS VALUES(3,'abc@123.com',123,NULL,false);
INSERT INTO USERS VALUES(4,'abc@123.com',123,NULL,false);

CALL addApplicant('abc@123.com'::varchar,'1234');
CALL addprovider('abcd@123.com'::varchar,'123');

INSERT INTO tags VALUES(1, 'CS');
INSERT INTO tags VALUES(2, 'HIST');
INSERT INTO tags VALUES(3, 'ECON');
INSERT INTO tags VALUES(4, 'BIO');

SELECT * FROM addTag('MATH'::varchar);
SELECT * FROM addTag('CS'::varchar);

INSERT INTO projects VALUES(1, 'CS Capstone','A cs capstone.');
INSERT INTO projects VALUES(1, 'CS Capstone 2','A second cs capstone.');
INSERT INTO projects VALUES(4, 'Hist Capstone','A history capstone.');

SELECT * FROM viewProjects(1);
SELECT * FROM viewProjects(2);

SELECT * FROM applicantTag(1,1);
SELECT * FROM applicantTag(1,3);

SELECT * FROM projectTag(1,1,'CS Capstone');
SELECT * FROM projectTag(1,1,'CS Capstone');
SELECT * FROM projectTag(1,3,'CS Capstone');

SELECT * FROM viewApplicantTags(3);

SELECT * FROM viewProjectTags(1, 'CS Capstone');

SELECT * FROM searchProjects('CS');

SELECT* FROM searchProjects(1);