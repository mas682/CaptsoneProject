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
END
$$ LANGUAGE plpgsql;