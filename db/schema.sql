CREATE TABLE Departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(255)
);
ALTER TABLE Departments ADD CONSTRAINT unique_department UNIQUE (department_name);


CREATE TABLE Schools (
    school_id INT PRIMARY KEY,
    school_name VARCHAR(255)
);


CREATE TABLE Instructors (
    instructor_id SERIAL PRIMARY KEY,
    instructor_name VARCHAR(255),
    department_id INT,
    school_id INT,
    quality DECIMAL(3, 2),
    total_ratings INT,
    retake_percent INT NULL,
    difficulty DECIMAL(3, 2),
    FOREIGN KEY (department_id) REFERENCES Departments(department_id),
    FOREIGN KEY (school_id) REFERENCES Schools(school_id)
);
