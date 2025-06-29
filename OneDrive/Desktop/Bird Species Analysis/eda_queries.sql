-- EDA Queries for Bird Species Observation Analysis (PostgreSQL Version)

-- Important: Column names are case-sensitive in PostgreSQL if they were created with mixed-case
-- by pandas.to_sql. Using double quotes around column names ensures they are correctly interpreted.

-- 1. Overall Data Overview
-- Total number of observations
SELECT COUNT(*) AS "TotalObservations" FROM "bird_observations";

-- Number of unique species observed
SELECT COUNT(DISTINCT "Common_Name") AS "UniqueSpeciesCount" FROM "bird_observations";

-- Time range of observations
SELECT MIN("Date") AS "EarliestObservation", MAX("Date") AS "LatestObservation" FROM "bird_observations";

-- 2. Temporal Analysis

-- Observations per year
SELECT
    EXTRACT(YEAR FROM "Date") AS "ObservationYear",
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
WHERE "Date" IS NOT NULL -- Exclude rows where date parsing might have failed
GROUP BY EXTRACT(YEAR FROM "Date")
ORDER BY "ObservationYear";

-- Observations per month (across all years)
SELECT
    EXTRACT(MONTH FROM "Date") AS "MonthNumber",
    TO_CHAR("Date", 'Month') AS "MonthName", -- Example: 'January', 'February'
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
WHERE "Date" IS NOT NULL
GROUP BY EXTRACT(MONTH FROM "Date"), TO_CHAR("Date", 'Month')
ORDER BY "MonthNumber";

-- Observations per hour of day (to see peak activity times)
SELECT
    EXTRACT(HOUR FROM "Start_Time") AS "HourOfDay",
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
GROUP BY EXTRACT(HOUR FROM "Start_Time")
ORDER BY "HourOfDay";


-- 3. Spatial Analysis

-- Unique species count per Location_Type (Forest vs. Grassland)
SELECT
    "Location_Type",
    COUNT(DISTINCT "Scientific_Name") AS "UniqueSpeciesCount",
    COUNT(*) AS "TotalObservations"
FROM "bird_observations"
GROUP BY "Location_Type"
ORDER BY "UniqueSpeciesCount" DESC;

-- Top 10 Admin Units by total observations
-- This query relies on Admin_Unit_Code being correctly parsed from sheets.
SELECT
    "Admin_Unit_Code",
    COUNT(*) AS "TotalObservations"
FROM "bird_observations"
WHERE "Admin_Unit_Code" IS NOT NULL AND "Admin_Unit_Code" != 'Unknown'
GROUP BY "Admin_Unit_Code"
ORDER BY "TotalObservations" DESC
LIMIT 10;

-- Top 10 Sites by unique species count
SELECT
    "Site_Name",
    COUNT(DISTINCT "Scientific_Name") AS "UniqueSpeciesCount"
FROM "bird_observations"
WHERE "Site_Name" IS NOT NULL AND "Site_Name" != 'Unknown'
GROUP BY "Site_Name"
ORDER BY "UniqueSpeciesCount" DESC
LIMIT 10;

-- 4. Species Analysis

-- Top 15 most frequently observed species (Common_Name)
SELECT
    "Common_Name",
    COUNT(*) AS "ObservationCount"
FROM "bird_observations"
WHERE "Common_Name" IS NOT NULL AND "Common_Name" != 'Unknown'
GROUP BY "Common_Name"
ORDER BY "ObservationCount" DESC
LIMIT 15;

-- How species are identified (ID_Method)
SELECT
    "ID_Method",
    COUNT(*) AS "MethodCount"
FROM "bird_observations"
WHERE "ID_Method" IS NOT NULL AND "ID_Method" != 'Unknown'
GROUP BY "ID_Method"
ORDER BY "MethodCount" DESC;

-- Sex ratio of observed birds (overall)
SELECT
    "Sex",
    COUNT(*) AS "Count"
FROM "bird_observations"
WHERE "Sex" IN ('Male', 'Female', 'Undetermined')
GROUP BY "Sex";

-- 5. Environmental Conditions Analysis

-- Average Temperature and Humidity by Location_Type
SELECT
    "Location_Type",
    AVG("Temperature") AS "AverageTemperature",
    AVG("Humidity") AS "AverageHumidity"
FROM "bird_observations"
WHERE "Temperature" IS NOT NULL AND "Humidity" IS NOT NULL
GROUP BY "Location_Type";

-- Observation counts by Sky condition
SELECT
    "Sky",
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
WHERE "Sky" IS NOT NULL AND "Sky" != 'Unknown'
GROUP BY "Sky"
ORDER BY "NumberOfObservations" DESC;

-- Observation counts by Wind condition
SELECT
    "Wind",
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
WHERE "Wind" IS NOT NULL AND "Wind" != 'Unknown'
GROUP BY "Wind"
ORDER BY "NumberOfObservations" DESC;

-- Impact of Disturbance on observations
SELECT
    "Disturbance",
    COUNT(*) AS "NumberOfObservations",
    COUNT(DISTINCT "Scientific_Name") AS "UniqueSpeciesCount"
FROM "bird_observations"
WHERE "Disturbance" IS NOT NULL AND "Disturbance" != 'Unknown" -- Corrected typo: "Unknown"
GROUP BY "Disturbance"
ORDER BY "NumberOfObservations" DESC;

-- 6. Distance and Behavior Analysis

-- Distribution of observation distances
SELECT
    "Distance",
    COUNT(*) AS "NumberOfObservations"
FROM "bird_observations"
WHERE "Distance" IS NOT NULL AND "Distance" != 'Unknown'
GROUP BY "Distance"
ORDER BY
        CASE
            WHEN "Distance" LIKE '<=50%' THEN 1
            WHEN "Distance" LIKE '50-100%' THEN 2
            WHEN "Distance" LIKE '>100%' THEN 3
            ELSE 4
        END;

-- Flyover observations vs. non-flyover
SELECT
    "Flyover_Observed",
    COUNT(*) AS "Count"
FROM "bird_observations"
GROUP BY "Flyover_Observed";

-- 7. Observer Trends

-- Top 5 observers by total observations
SELECT
    "Observer",
    COUNT(*) AS "TotalObservations"
FROM "bird_observations"
WHERE "Observer" IS NOT NULL AND "Observer" != 'Unknown'
GROUP BY "Observer"
ORDER BY "TotalObservations" DESC
LIMIT 5;

-- 8. Conservation Insights

-- Species on PIF Watchlist and their observation count
SELECT
    "Common_Name",
    COUNT(*) AS "ObservationCount"
FROM "bird_observations"
WHERE "PIF_Watchlist_Status" = TRUE
GROUP BY "Common_Name"
ORDER BY "ObservationCount" DESC;

-- Species with Regional Stewardship Status and their observation count
SELECT
    "Common_Name",
    COUNT(*) AS "ObservationCount"
FROM "bird_observations"
WHERE "Regional_Stewardship_Status" = TRUE
GROUP BY "Common_Name"
ORDER BY "ObservationCount" DESC;

-- Combined At-Risk Species (PIF Watchlist OR Regional Stewardship)
SELECT
    "Common_Name",
    "Location_Type",
    COUNT(*) AS "ObservationCount"
FROM "bird_observations"
WHERE "PIF_Watchlist_Status" = TRUE OR "Regional_Stewardship_Status" = TRUE
GROUP BY "Common_Name", "Location_Type"
ORDER BY "ObservationCount" DESC;