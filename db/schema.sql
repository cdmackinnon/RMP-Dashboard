
CREATE TABLE Departments (
    department_id INT PRIMARY KEY,
    department_name VARCHAR(255)
);


CREATE TABLE Schools (
    school_id INT PRIMARY KEY,
    school_name VARCHAR(255)
);


CREATE TABLE Instructors (
    instructor_id INT PRIMARY KEY,
    instructor_name VARCHAR(255),
    department_id INT,
    school_id INT,
    FOREIGN KEY (department_id) REFERENCES Departments(department_id),
    FOREIGN KEY (school_id) REFERENCES Schools(school_id)
);


CREATE TABLE Ratings (
    rating_id INT PRIMARY KEY,
    instructor_id INT,
    -- Ratings will be of format 0.0, (3,2) leaves overhead room
    quality DECIMAL(3, 2),
    number_of_ratings INT,
    retake_percent INT,
    difficulty DECIMAL(3, 2),
    FOREIGN KEY (instructor_id) REFERENCES Instructors(instructor_id)
);