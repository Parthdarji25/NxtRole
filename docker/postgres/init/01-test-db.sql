-- Creates a second database used only by automated tests, so tests never touch your development data.
-- Postgres runs this once, when its data volume is created for the first time.
CREATE DATABASE nxtrole_test;
