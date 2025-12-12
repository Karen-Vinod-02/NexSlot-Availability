CREATE DATABASE IF NOT EXISTS classroom_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE classroom_system;

CREATE TABLE users (
  username VARCHAR(100) PRIMARY KEY,
  password_hash VARCHAR(128) NOT NULL,
  role ENUM('Admin','Faculty','Student') NOT NULL,
  name VARCHAR(255),
  department VARCHAR(255),
  year VARCHAR(50),
  division VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classrooms (
  id VARCHAR(32) PRIMARY KEY,
  room_number VARCHAR(50) NOT NULL,
  capacity INT NOT NULL,
  has_smartboard BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
  id VARCHAR(32) PRIMARY KEY,
  booking_key VARCHAR(255) UNIQUE NOT NULL,
  classroom_id VARCHAR(32) NOT NULL,
  faculty_id VARCHAR(100),
  date DATE NOT NULL,
  slot VARCHAR(50) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  faculty_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Confirmed',
  is_guest_lecture BOOLEAN NOT NULL DEFAULT FALSE,
  lecture_title VARCHAR(255),
  department VARCHAR(255),
  year VARCHAR(50),
  division VARCHAR(50),
  semester VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE
);

CREATE TABLE feedback (
  id VARCHAR(32) PRIMARY KEY,
  booking_id VARCHAR(32) NOT NULL,
  student_id VARCHAR(100) NOT NULL,
  rating TINYINT NOT NULL,
  comments TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

CREATE TABLE config (
  id INT PRIMARY KEY DEFAULT 1,
  class_slots TEXT,
  classroom_limit INT DEFAULT 100,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO config (id, class_slots, classroom_limit)
VALUES (1, '["8:00 - 9:30","9:40 - 11:10","11:20 - 12:50","1:30 - 3:00","3:10 - 4:40"]', 100);
