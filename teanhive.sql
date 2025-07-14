-- =================================================================
-- Tea N Hive - Database Schema
-- Version: 1.0
-- Author: Your Development Partner
-- Database: PostgreSQL
-- =================================================================

-- To ensure the script is re-runnable, we drop tables in reverse order of creation
-- due to foreign key constraints.
DROP TABLE IF EXISTS "short_likes" CASCADE;
DROP TABLE IF EXISTS "short_comments" CASCADE;
DROP TABLE IF EXISTS "shorts" CASCADE;
DROP TABLE IF EXISTS "post_likes" CASCADE;
DROP TABLE IF EXISTS "post_comments" CASCADE;
DROP TABLE IF EXISTS "posts" CASCADE;
DROP TABLE IF EXISTS "course_listings" CASCADE;
DROP TABLE IF EXISTS "trades" CASCADE;
DROP TABLE IF EXISTS "performance_reports" CASCADE;
DROP TABLE IF EXISTS "user_certifications" CASCADE;
DROP TABLE IF EXISTS "user_challenges" CASCADE;
DROP TABLE IF EXISTS "challenges" CASCADE;
DROP TABLE IF EXISTS "certifications" CASCADE;
DROP TABLE IF EXISTS "profiles" CASCADE;
DROP TABLE IF EXISTS "users" CASCADE;


-- =============================================
-- SECTION 1: Cœur du Système (Core System)
-- =============================================

-- Table: users
-- Stores the core authentication information for each user.
CREATE TABLE "users" (
    "user_id" SERIAL PRIMARY KEY,
    "email" VARCHAR(255) UNIQUE NOT NULL,
    "password_hash" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_login" TIMESTAMPTZ
);

-- Table: profiles
-- Stores the public-facing profile information for each user.
-- Linked one-to-one with the users table.
CREATE TABLE "profiles" (
    "profile_id" SERIAL PRIMARY KEY,
    "user_id" INT UNIQUE NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "username" VARCHAR(50) UNIQUE NOT NULL,
    "first_name" VARCHAR(100),
    "last_name" VARCHAR(100),
    "gender" VARCHAR(50),
    "avatar_url" VARCHAR(255),
    "bio" TEXT,
    "trading_style" VARCHAR(100),
    "social_links" JSONB
);

-- Table: certifications
-- A static table defining all possible certifications/badges a user can earn.
CREATE TABLE "certifications" (
    "certification_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) UNIQUE NOT NULL,
    "description" TEXT,
    "badge_url" VARCHAR(255) NOT NULL
);

-- Table: challenges
-- A static table defining all available challenges.
CREATE TABLE "challenges" (
    "challenge_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "rules" JSONB NOT NULL, -- e.g., {"profitTarget": 0.10, "maxDailyDrawdown": 0.05}
    "duration_days" INT NOT NULL,
    "reward_certification_id" INT NOT NULL REFERENCES "certifications"("certification_id")
);

-- Table: user_challenges
-- This is a crucial linking table. Each row represents a single attempt by a user to complete a challenge.
CREATE TABLE "user_challenges" (
    "user_challenge_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "challenge_id" INT NOT NULL REFERENCES "challenges"("challenge_id"),
    "mt_account_id" VARCHAR(100) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'IN_PROGRESS', -- e.g., IN_PROGRESS, PASSED, FAILED
    "start_date" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "end_date" TIMESTAMPTZ
);

-- Table: trades
-- Stores every single trade made within a user's challenge account. Potentially a very large table.
CREATE TABLE "trades" (
    "trade_id" BIGSERIAL PRIMARY KEY, -- BIGSERIAL for very large number of trades
    "user_challenge_id" INT NOT NULL REFERENCES "user_challenges"("user_challenge_id") ON DELETE CASCADE,
    "symbol" VARCHAR(20) NOT NULL,
    "type" VARCHAR(10) NOT NULL, -- e.g., 'BUY', 'SELL'
    "volume" DOUBLE PRECISION NOT NULL,
    "open_price" DECIMAL(18, 8) NOT NULL,
    "close_price" DECIMAL(18, 8),
    "open_time" TIMESTAMPTZ NOT NULL,
    "close_time" TIMESTAMPTZ,
    "profit" DECIMAL(18, 4)
);

-- Table: user_certifications
-- The user's permanent record of earned certifications.
CREATE TABLE "user_certifications" (
    "user_certification_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "certification_id" INT NOT NULL REFERENCES "certifications"("certification_id"),
    "issued_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: performance_reports
-- Stores the output of the AI analysis for a completed challenge.
CREATE TABLE "performance_reports" (
    "report_id" SERIAL PRIMARY KEY,
    "user_challenge_id" INT UNIQUE NOT NULL REFERENCES "user_challenges"("user_challenge_id") ON DELETE CASCADE,
    "metrics" JSONB, -- e.g., {"sharpeRatio": 1.5, "winRate": 0.6}
    "behavioral_analysis" JSONB, -- e.g., {"lossAversion": "high", "overconfidence": "medium"}
    "generated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ========================================================
-- SECTION 2: Système Social (Social System)
-- ========================================================

-- Table: posts
-- For classic social media posts (text, images).
CREATE TABLE "posts" (
    "post_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "post_type" VARCHAR(50) NOT NULL, -- 'TEXT', 'IMAGE'
    "text_content" TEXT,
    "media_url" VARCHAR(255),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: post_comments
CREATE TABLE "post_comments" (
    "comment_id" SERIAL PRIMARY KEY,
    "post_id" INT NOT NULL REFERENCES "posts"("post_id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "text_content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: post_likes
CREATE TABLE "post_likes" (
    "like_id" SERIAL PRIMARY KEY,
    "post_id" INT NOT NULL REFERENCES "posts"("post_id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    UNIQUE ("post_id", "user_id") -- Ensures a user can only like a post once
);


-- ========================================================
-- SECTION 3: Système des Shorts (Shorts System)
-- ========================================================

-- Table: shorts
-- A separate table for short-form video content, as requested.
CREATE TABLE "shorts" (
    "short_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "video_url" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: short_comments
CREATE TABLE "short_comments" (
    "comment_id" SERIAL PRIMARY KEY,
    "short_id" INT NOT NULL REFERENCES "shorts"("short_id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    "text_content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: short_likes
CREATE TABLE "short_likes" (
    "like_id" SERIAL PRIMARY KEY,
    "short_id" INT NOT NULL REFERENCES "shorts"("short_id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE,
    UNIQUE ("short_id", "user_id") -- Ensures a user can only like a short once
);


-- ====================================================================
-- SECTION 4: Système de Formation (Simplified Training System)
-- ====================================================================

-- Table: course_listings
-- A simple listing for external courses. No internal lessons or enrollments.
CREATE TABLE "course_listings" (
    "course_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "users"("user_id") ON DELETE CASCADE, -- The instructor
    "title" VARCHAR(255) NOT NULL,
    "description" TEXT,
    "price" DECIMAL(10, 2),
    "currency" VARCHAR(10),
    "external_url" VARCHAR(2048) NOT NULL, -- The link to the course platform
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ========================================================
-- SECTION 5: Indexes for Performance Optimization
-- ========================================================

-- Indexes on foreign keys and frequently queried columns will dramatically
-- speed up read operations as the database grows.

-- Core System Indexes
CREATE INDEX ON "profiles" ("user_id");
CREATE INDEX ON "user_challenges" ("user_id");
CREATE INDEX ON "user_challenges" ("challenge_id");
CREATE INDEX ON "trades" ("user_challenge_id");
CREATE INDEX ON "trades" ("symbol", "open_time");
CREATE INDEX ON "user_certifications" ("user_id");
CREATE INDEX ON "user_certifications" ("certification_id");
CREATE INDEX ON "performance_reports" ("user_challenge_id");

-- Social System Indexes
CREATE INDEX ON "posts" ("user_id");
CREATE INDEX ON "post_comments" ("post_id");
CREATE INDEX ON "post_comments" ("user_id");
CREATE INDEX ON "post_likes" ("post_id", "user_id");

-- Shorts System Indexes
CREATE INDEX ON "shorts" ("user_id");
CREATE INDEX ON "short_comments" ("short_id");
CREATE INDEX ON "short_comments" ("user_id");
CREATE INDEX ON "short_likes" ("short_id", "user_id");

-- Training System Indexes
CREATE INDEX ON "course_listings" ("user_id");

-- Final message
\echo 'Tea N Hive database schema created successfully.'