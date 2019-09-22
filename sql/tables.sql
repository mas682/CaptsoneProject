--Jonathan Zhang
--CS 1980
--Matchmaker Application

-- ## TODO: Survey responses, better security measures

--Tags
CREATE TABLE Tags
(
  TID int,
  name varchar[20],
  CONSTRAINT PK_Tags PRIMARY KEY(TID)
);
--Applicants
CREATE TABLE Applicants
(
  AID int,
  email varchar[20],
  password varchar[20],
  major varchar[10],
  CONSTRAINT PK_Applicants PRIMARY KEY(AID)
);
--Classes taken for applicants
CREATE TABLE ApplicantsClasses
(
  AID int,
  class varchar[20],
  CONSTRAINT PK_AppClass PRIMARY KEY(AID, class),
  CONSTRAINT FK_AppClass FOREIGN KEY(AID) REFERENCES Applicants(AID)
);
--Tags associated with applicant: from classes/survey
CREATE TABLE ApplicantsTags
(
  AID int,
  TID int,
  CONSTRAINT PK_AppTags PRIMARY KEY (AID, TID),
  CONSTRAINT FK_AppTags_App FOREIGN KEY(AID) REFERENCES Applicants(AID),
  CONSTRAINT FK_AppTags_Tag FOREIGN KEY(TID) REFERENCES Tags(TID)
);
--Providers
CREATE TABLE Providers
(
  PID int,
  email varchar[20],
  password varchar[20],
  description varchar[50],
  CONSTRAINT PK_Providers PRIMARY KEY (PID)
);
--Projects
CREATE TABLE Projects
(
  PID int,
  p_name varchar[20],
  description varchar[50],
  CONSTRAINT PK_Projects PRIMARY KEY(PID, p_name),
  CONSTRAINT FK_Projects FOREIGN KEY(PID) REFERENCES Providers(PID)
);
--Tags associated with projects
CREATE TABLE ProjectTags
(
  PID int,
  p_name varchar[20],
  TID int,
  CONSTRAINT PK_ProjectTags PRIMARY KEY(PID, p_name, TID),
  CONSTRAINT FK_ProjectTags_Proj FOREIGN KEY(PID, p_name) REFERENCES Projects(PID, p_name),
  CONSTRAINT FK_ProjectTags_Tags FOREIGN KEY(TID) REFERENCES Tags(TID)
);