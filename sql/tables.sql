--Jonathan Zhang
--CS 1980
--Matchmaker Application

-- ## TODO: Survey responses, better security measures

--Tags
CREATE TABLE Tags
(
  TID int,
  name varchar(50),
  discards int,
  CONSTRAINT PK_Tags PRIMARY KEY(TID)
);
--Applicants and Providers in same table
CREATE TABLE Users
(
  UID int,
  email varchar(30),
  password varchar(30),
  major varchar(20),
  isProvider boolean,
  CONSTRAINT PK_Applicants PRIMARY KEY(UID)
);
--Classes taken for applicants
CREATE TABLE ApplicantsClasses
(
  UID int,
  class varchar(50),
  CONSTRAINT PK_AppClass PRIMARY KEY(UID, class),
  CONSTRAINT FK_AppClass FOREIGN KEY(UID) REFERENCES Users(UID)
);
--Tags associated with applicant:
CREATE TABLE ApplicantsTags
(
  UID int,
  TID int,
  rating int,
  CONSTRAINT PK_AppTags PRIMARY KEY (UID, TID),
  CONSTRAINT FK_AppTags_App FOREIGN KEY(UID) REFERENCES Users(UID),
  CONSTRAINT FK_AppTags_Tag FOREIGN KEY(TID) REFERENCES Tags(TID)
);
--Projects
CREATE TABLE Projects
(
  UID int,
  p_name varchar(50),
  description varchar(5000),
  CONSTRAINT PK_Projects PRIMARY KEY(UID, p_name),
  CONSTRAINT FK_Projects FOREIGN KEY(UID) REFERENCES Users(UID)
);
--Tags associated with projects
CREATE TABLE ProjectTags
(
  UID int,
  p_name varchar(50),
  TID int,
  CONSTRAINT PK_ProjectTags PRIMARY KEY(UID, p_name, TID),
  CONSTRAINT FK_ProjectTags_Proj FOREIGN KEY(UID, p_name) REFERENCES Projects(UID, p_name),
  CONSTRAINT FK_ProjectTags_Tags FOREIGN KEY(TID) REFERENCES Tags(TID)
);