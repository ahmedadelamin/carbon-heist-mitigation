-- ==============================================================================
-- NYC Energy & CO2 Relational Schema
-- Standard SQL Data Definition Language (DDL)
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 0. Create and Use Database
-- ------------------------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS NYC_Carbon_Heist;
USE NYC_Carbon_Heist;

-- ------------------------------------------------------------------------------
-- 1. Lookups (Dimensions)
-- ------------------------------------------------------------------------------

CREATE TABLE CITIES (
    city_id INT PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE BOROUGHS (
    borough_id INT PRIMARY KEY,
    borough_name VARCHAR(100) NOT NULL UNIQUE,
    city_id INT NOT NULL,
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE RESTRICT
);

CREATE TABLE PROPERTY_TYPES (
    property_type_id INT PRIMARY KEY,
    property_type_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE CONSTRUCTION_STATUSES (
    construction_status_id INT PRIMARY KEY,
    status_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE METERING_AREAS (
    metering_area_id INT PRIMARY KEY,
    metering_area_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE FUEL_TYPES (
    fuel_type_id INT PRIMARY KEY,
    fuel_type_name VARCHAR(100) NOT NULL UNIQUE,
    unit VARCHAR(50) NOT NULL
);

CREATE TABLE ALERT_TYPES (
    alert_type_id INT PRIMARY KEY,
    alert_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE PARENT_PROPERTIES (
    parent_property_id VARCHAR(50) PRIMARY KEY,
    parent_property_name VARCHAR(255) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Core Tables
-- ------------------------------------------------------------------------------

CREATE TABLE PROPERTIES (
    property_id VARCHAR(50) PRIMARY KEY,
    property_name VARCHAR(255) NOT NULL,
    year_built INT CHECK (year_built >= 1600),
    decade_built INT,
    building_age INT CHECK (building_age >= 0),
    occupancy_percent DECIMAL(5, 2) CHECK (occupancy_percent BETWEEN 0 AND 100),
    gfa_buildings_parking_ft2 DECIMAL(15, 2) CHECK (gfa_buildings_parking_ft2 >= 0),
    gfa_buildings_ft2 DECIMAL(15, 2) CHECK (gfa_buildings_ft2 >= 0),
    parent_property_id VARCHAR(50),
    city_id INT NOT NULL,
    borough_id INT NOT NULL,
    property_type_id INT NOT NULL,
    construction_status_id INT NOT NULL,
    FOREIGN KEY (parent_property_id) REFERENCES PARENT_PROPERTIES(parent_property_id) ON DELETE SET NULL,
    FOREIGN KEY (city_id) REFERENCES CITIES(city_id) ON DELETE RESTRICT,
    FOREIGN KEY (borough_id) REFERENCES BOROUGHS(borough_id) ON DELETE RESTRICT,
    FOREIGN KEY (property_type_id) REFERENCES PROPERTY_TYPES(property_type_id) ON DELETE RESTRICT,
    FOREIGN KEY (construction_status_id) REFERENCES CONSTRUCTION_STATUSES(construction_status_id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------------------------
-- 3. Metrics & Usage (Fact Tables)
-- ------------------------------------------------------------------------------

CREATE TABLE PROPERTY_METERING (
    property_metering_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL,
    energy_metering_area_id INT NOT NULL,
    water_metering_area_id INT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE,
    FOREIGN KEY (energy_metering_area_id) REFERENCES METERING_AREAS(metering_area_id) ON DELETE RESTRICT,
    FOREIGN KEY (water_metering_area_id) REFERENCES METERING_AREAS(metering_area_id) ON DELETE RESTRICT
);

CREATE TABLE ENERGY_METRICS (
    energy_metric_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL UNIQUE,
    energy_star_score DECIMAL(5, 2) CHECK (energy_star_score BETWEEN 1 AND 100),
    national_median_energy_star_score DECIMAL(5, 2),
    target_energy_star_score DECIMAL(5, 2),
    site_eui_kbtu_ft2 DECIMAL(15, 2) CHECK (site_eui_kbtu_ft2 >= 0),
    site_energy_use_kbtu DECIMAL(20, 2) CHECK (site_energy_use_kbtu >= 0),
    source_eui_kbtu_ft2 DECIMAL(15, 2) CHECK (source_eui_kbtu_ft2 >= 0),
    source_energy_use_kbtu DECIMAL(20, 2) CHECK (source_energy_use_kbtu >= 0),
    green_power_kwh DECIMAL(20, 2) CHECK (green_power_kwh >= 0),
    egrid_output_emissions_rate_kgco2e_mbtu DECIMAL(15, 2),
    percent_electricity_green_power DECIMAL(5, 2) CHECK (percent_electricity_green_power BETWEEN 0 AND 100),
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE
);

CREATE TABLE EMISSION_METRICS (
    emission_metric_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL UNIQUE,
    avoided_emissions_metric_tons_co2e DECIMAL(15, 2),
    total_ghg_emissions_metric_tons_co2e DECIMAL(15, 2),
    total_ghg_emissions_intensity_kgco2e_ft2 DECIMAL(15, 2),
    net_emissions_metric_tons_co2e DECIMAL(15, 2),
    national_median_total_ghg_emissions_metric_tons_co2e DECIMAL(15, 2),
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE
);

CREATE TABLE LL97_PENALTIES (
    penalty_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL UNIQUE,
    base_ll97_penalty DECIMAL(20, 2) CHECK (base_ll97_penalty >= 0),
    base_penalty_per_ft2 DECIMAL(15, 2) CHECK (base_penalty_per_ft2 >= 0),
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE
);

CREATE TABLE PROPERTY_FUEL_USAGE (
    fuel_usage_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL,
    fuel_type_id INT NOT NULL,
    usage_kbtu DECIMAL(20, 2) CHECK (usage_kbtu >= 0),
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE,
    FOREIGN KEY (fuel_type_id) REFERENCES FUEL_TYPES(fuel_type_id) ON DELETE RESTRICT
);

CREATE TABLE PROPERTY_ALERTS (
    property_alert_id INT PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL,
    alert_type_id INT NOT NULL,
    alert_status VARCHAR(100) NOT NULL,
    FOREIGN KEY (property_id) REFERENCES PROPERTIES(property_id) ON DELETE CASCADE,
    FOREIGN KEY (alert_type_id) REFERENCES ALERT_TYPES(alert_type_id) ON DELETE RESTRICT
);
