CREATE DATABASE CHAT;
USE CHAT;
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    password VARCHAR(50)
    );

CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    text VARCHAR(100),
    CONSTRAINT `fk_user_id`
        FOREIGN KEY(user_id) REFERENCES users(id)
        ON DELETE CASCADE
    );

CREATE TABLE private_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sender_id INT,
    target_id INT,
    text VARCHAR(100),
    CONSTRAINT `fk_private_sender_id`
        FOREIGN KEY(sender_id) REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT `fk_private_target_id`
        FOREIGN KEY(target_id) REFERENCES users(id)
        ON DELETE CASCADE
    );
