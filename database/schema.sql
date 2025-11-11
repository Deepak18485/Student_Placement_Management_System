-- Student Internship & Placement Management System 

-- Create Database
CREATE DATABASE IF NOT EXISTS student_placement_system;
USE student_placement_system;

-- Tables
CREATE TABLE students (
    student_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    branch VARCHAR(50) NOT NULL,
    cgpa DECIMAL(3,2) NOT NULL,
    resume_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    university_roll INT NOT NULL,
    PRIMARY KEY (student_id)
);

CREATE TABLE Skill (
    skill_id INT AUTO_INCREMENT PRIMARY KEY,
    skill_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE StudentSkill (
    student_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (student_id, skill_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skill(skill_id) ON DELETE CASCADE
);

CREATE TABLE PlacementOfficer (
    officer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE JobPosting (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    branch_eligibility VARCHAR(50),
    min_cgpa DECIMAL(3,2) NOT NULL CHECK (min_cgpa >= 0 AND min_cgpa <= 10),
    package_stipend DECIMAL(10,2),
    deadline DATE NOT NULL,
    status ENUM('Open', 'Closed') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (officer_id) REFERENCES PlacementOfficer(officer_id) ON DELETE CASCADE
);

CREATE TABLE JobSkill (
    job_id INT NOT NULL,
    skill_id INT NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES JobPosting(job_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES Skill(skill_id) ON DELETE CASCADE
);

CREATE TABLE Application (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    status ENUM('Applied', 'Shortlisted', 'Selected', 'Rejected') DEFAULT 'Applied',
    applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES JobPosting(job_id) ON DELETE CASCADE,
    UNIQUE (student_id, job_id) -- Prevent duplicate applications
);

CREATE TABLE Notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE
);

