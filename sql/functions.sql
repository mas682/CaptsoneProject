--Jonathan Zhang
--CS 1980
--Matchmaker Application

-- ##better security measures


--Add new applicant
CREATE OR REPLACE PROCEDURE addApplicant(new_email VARCHAR(20),new_password VARCHAR(20))
AS $$
  DECLARE
    smallest int;
  BEGIN
    SELECT max(uid) FROM users INTO smallest;
    INSERT INTO users VALUES (smallest+1,new_email,new_password,null,false);
  END;
$$ LANGUAGE plpgsql;

--Add new provider
CREATE OR REPLACE PROCEDURE addProvider(new_email VARCHAR(20),new_password VARCHAR(20))
AS $$
  DECLARE
    smallest int;
  BEGIN
    SELECT max(uid) FROM users INTO smallest;
    INSERT INTO users VALUES (smallest+1,new_email,new_password,null,true);
  END;
$$ LANGUAGE plpgsql;

--View all projects from a provider
CREATE OR REPLACE FUNCTION viewProjects(provider int) RETURNS SETOF projects AS $$
BEGIN
  RETURN QUERY
  SELECT * FROM projects WHERE projects.uid=provider;
END;
$$ LANGUAGE plpgsql;

--Adds a tag
CREATE OR REPLACE FUNCTION addTag(newTag VARCHAR(20))RETURNS boolean AS $$
DECLARE
    smallest int;
    checkTag int;
BEGIN
  SELECT INTO checkTag count(*) FROM Tags where name=newTag;
  IF(checkTag > 0) --check if doesn't already exist
    THEN
      RETURN FALSE;
  end if;
  SELECT max(tid) FROM Tags INTO smallest;
  INSERT INTO tags VALUES(smallest+1,newTag);
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

--Add tag to applicant
CREATE OR REPLACE FUNCTION applicantTag(theTag int, applicant int) RETURNS boolean AS $$
DECLARE
    checkApp int;
BEGIN
  SELECT count(*) INTO checkApp FROM ApplicantsTags where tid=theTag AND uid=applicant;
  IF(checkApp>0) --check if doesn't already exist
    THEN
      RETURN FALSE;
  end if;
  IF((SELECT isProvider FROM users WHERE users.uid=applicant) = TRUE) --not an applicant
    THEN
      RETURN FALSE;
    END IF;
  INSERT INTO ApplicantsTags VALUES(applicant,theTag);
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

--Add tag to project
CREATE OR REPLACE FUNCTION projectTag(theTag int, provider int, project varchar(20)) RETURNS boolean AS $$
DECLARE
    checkProj int;
BEGIN
  SELECT INTO checkProj count(*) FROM ProjectTags where p_name=project AND tid=theTag;
  IF(checkProj>0) --check if doesn't already exist
    THEN
      RETURN FALSE;
  end if;
  IF((SELECT isProvider FROM users WHERE users.uid=provider) = FALSE) --not a provider
    THEN
      RETURN FALSE;
    END IF;
  INSERT INTO ProjectTags VALUES(provider, project,theTag);
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

--View all tags associated with an applicant
CREATE OR REPLACE FUNCTION viewApplicantTags(applicant int) RETURNS TABLE(tagID int, tagDescr varchar(20)) AS $$
BEGIN
  DROP TABLE IF EXISTS combineTags;
  CREATE  TABLE combineTags AS
      SELECT * FROM tags NATURAL JOIN applicantsTags;
  RETURN QUERY
  SELECT ct.tid, ct.name FROM combineTags ct WHERE ct.uid = applicant;
END;
$$ LANGUAGE plpgsql;

--View all tags associated with a project
CREATE OR REPLACE FUNCTION viewProjectTags(provider int, projectName varchar(20)) RETURNS TABLE(tagID int, tagDescr varchar(20)) AS $$
BEGIN
  DROP TABLE IF EXISTS combineTags;
  CREATE  TABLE combineTags AS
      SELECT * FROM tags NATURAL JOIN projectTags;
  RETURN QUERY
  SELECT ct.tid, ct.name FROM combineTags ct WHERE ct.uid = provider AND ct.p_name=projectName;
END;
$$ LANGUAGE plpgsql;

--Search for projects that have or don't have a tag
CREATE OR REPLACE FUNCTION searchProjects(tag varchar(20),type boolean) RETURNS TABLE(uid int, p_name varchar(20),description varchar(5000))  AS $$
BEGIN
  DROP TABLE IF EXISTS combineTags;
  DROP TABLE IF EXISTS combineProjects;
  CREATE  TABLE combineTags AS
      SELECT * FROM tags NATURAL JOIN projectTags;
  CREATE TABLE combineProjects AS
      SELECT * FROM combineTags NATURAL JOIN projects;
  IF(type) --want this tag
    THEN
    RETURN QUERY
      SELECT cp.uid, cp.p_name, cp.description FROM combineProjects cp WHERE cp.name=tag;
  END IF;
  RETURN QUERY --don't want this tag
    SELECT cp.uid, cp.p_name, cp.description FROM combineProjects cp WHERE cp.name!=tag;
END;
$$ LANGUAGE plpgsql;

--Update rating for a user's tag
CREATE OR REPLACE PROCEDURE updateRating(userID int, tag int, rate int) AS $$
BEGIN
  UPDATE ApplicantsTags SET rating=rate WHERE uid=userID AND tid=tag;
END;
$$ LANGUAGE plpgsql;

--Update discard count for a tag
CREATE OR REPLACE PROCEDURE updateDiscardCount(tag int, change boolean) AS $$
DECLARE
  curCount int;
BEGIN
  SELECT discards into curCount FROM Tags WHERE tid=tag;
  IF(change) --increase discard count(not good tag)
    THEN
      UPDATE Tags SET discards=curCount+1 WHERE tid=tag;
  END IF;
  IF(!change AND curCount>0) --decrease discard (good tag)
    THEN
    UPDATE Tags SET discards=curCount-1 WHERE tid=tag;
  END IF;
END;
$$ LANGUAGE plpgsql;

--Get projects that best correspond with user tags
--Note: can probably use other functions to do this
/*
CREATE OR REPLACE FUNCTION searchProjects(applicantID int) RETURNS TABLE(uid int, p_name varchar(20), description varchar(5000)) AS $$
DECLARE
  userTags int;
BEGIN
  DROP TABLE IF EXISTS theTags;
  DROP TABLE IF EXISTS combineTags;
  DROP TABLE IF EXISTS countTags;
  --get user tags
  CREATE TABLE theTags AS
    SELECT * FROM applicantsTags at WHERE at.uid=applicantID;
  --get projects tags that match user tags
  CREATE TABLE combineTags AS
    SELECT * FROM theTags NATURAL JOIN ProjectTags;
  CREATE TABLE countTags AS
    SELECT COUNT(DISTINCT ct.p_name) FROM combineTags ct;
  RETURN QUERY
    SELECT * FROM projects ct;
END;
$$ LANGUAGE plpgsql;
*/