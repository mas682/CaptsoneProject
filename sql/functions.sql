--Jonathan Zhang
--CS 1980
--Matchmaker Application

-- ## TODO: Survey responses, better security measures


--Add new applicant
CREATE OR REPLACE PROCEDURE addApplicant(new_email VARCHAR[20],new_password VARCHAR[20])
AS $$
  DECLARE
    smallest int;
  BEGIN
    SELECT max(aid) FROM applicants INTO smallest;
    INSERT INTO applicants VALUES (smallest+1,new_email,new_password,null);
  END;
$$ LANGUAGE plpgsql;

--Add new provider
CREATE OR REPLACE PROCEDURE addProvider(new_email VARCHAR[20],new_password VARCHAR[20])
AS $$
  DECLARE
    smallest int;
  BEGIN
    SELECT max(pid) FROM providers INTO smallest;
    INSERT INTO providers VALUES (smallest+1,new_email,new_password,null);
  END;
$$ LANGUAGE plpgsql;

--View all projects from a provider
CREATE OR REPLACE FUNCTION viewProjects(pid int) RETURNS SETOF projects AS $$
BEGIN
  RETURN QUERY
  SELECT * FROM projects WHERE projects.pid=pid;
END;
$$ LANGUAGE plpgsql;

--Adds a tag
CREATE OR REPLACE FUNCTION addTag(newTag VARCHAR[20])RETURNS boolean AS $$
DECLARE
    smallest int;
BEGIN
  IF(SELECT count(*) FROM Tags where name=newTag>0) --check if doesn't already exist
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
BEGIN
  IF(SELECT count(*) FROM ApplicantsTags where tid=theTag and aid=applicant>0) --check if doesn't already exist
    THEN
      RETURN FALSE;
  end if;
  INSERT INTO ApplicantsTags VALUES(applicant,theTag);
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

--Add tag to project
CREATE OR REPLACE FUNCTION projectTag(theTag int, provider int, project varchar[20]) RETURNS boolean AS $$
BEGIN
  IF(SELECT count(*) FROM ProjectTags where tid=theTag and p_name=project>0) --check if doesn't already exist
    THEN
      RETURN FALSE;
  end if;
  INSERT INTO ProjectTags VALUES(provider, p_name,theTag);
  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;