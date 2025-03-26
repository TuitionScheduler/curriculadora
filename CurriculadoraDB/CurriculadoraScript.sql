DROP TABLE IF EXISTS Course;

DROP TABLE IF EXISTS Degree;

CREATE TABLE Course (
    course_id INTEGER PRIMARY KEY,
    course_code TEXT NOT NULL
);

CREATE TABLE Degree (
    degree_id INTEGER PRIMARY KEY,
    degree_title TEXT NOT NULL
);

INSERT INTO Course (course_code) VALUES ('DUMM3101');

INSERT INTO Degree (degree_title) VALUES ('Dummy');

-- SELECT course_code FROM Course;
-- SELECT degree_title FROM Degree;