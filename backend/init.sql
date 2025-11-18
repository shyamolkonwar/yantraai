-- Initialize database for Yantra AI
-- This file will be executed when PostgreSQL container starts

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS yantra_ai;

-- Create extensions for better performance and functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Connect to the yantra_ai database
\c yantra_ai;