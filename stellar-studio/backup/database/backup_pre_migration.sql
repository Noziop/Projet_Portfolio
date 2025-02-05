/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.5.27-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: stellarstudio
-- ------------------------------------------------------
-- Server version	10.5.27-MariaDB-ubu2004

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('c31176e3f9ec');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `observations`
--

DROP TABLE IF EXISTS `observations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `observations` (
  `id` varchar(36) NOT NULL,
  `telescope_id` varchar(36) DEFAULT NULL,
  `target_id` varchar(255) DEFAULT NULL,
  `coordinates_ra` varchar(50) NOT NULL,
  `coordinates_dec` varchar(50) NOT NULL,
  `start_time` datetime NOT NULL,
  `exposure_time` int(11) NOT NULL,
  `instrument` varchar(100) NOT NULL,
  `filters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`filters`)),
  `fits_files` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`fits_files`)),
  `preview_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `telescope_id` (`telescope_id`),
  CONSTRAINT `observations_ibfk_1` FOREIGN KEY (`telescope_id`) REFERENCES `space_telescopes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `observations`
--

LOCK TABLES `observations` WRITE;
/*!40000 ALTER TABLE `observations` DISABLE KEYS */;
/*!40000 ALTER TABLE `observations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `processing_jobs`
--

DROP TABLE IF EXISTS `processing_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `processing_jobs` (
  `id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `telescope_id` varchar(36) NOT NULL,
  `workflow_id` varchar(36) NOT NULL,
  `status` enum('PENDING','PROCESSING','COMPLETED','FAILED') DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `completed_at` datetime DEFAULT NULL,
  `result_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `telescope_id` (`telescope_id`),
  KEY `user_id` (`user_id`),
  KEY `workflow_id` (`workflow_id`),
  CONSTRAINT `processing_jobs_ibfk_1` FOREIGN KEY (`telescope_id`) REFERENCES `space_telescopes` (`id`),
  CONSTRAINT `processing_jobs_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `processing_jobs_ibfk_3` FOREIGN KEY (`workflow_id`) REFERENCES `workflows` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `processing_jobs`
--

LOCK TABLES `processing_jobs` WRITE;
/*!40000 ALTER TABLE `processing_jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `processing_jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `space_telescopes`
--

DROP TABLE IF EXISTS `space_telescopes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `space_telescopes` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `aperture` varchar(50) NOT NULL,
  `focal_length` varchar(50) NOT NULL,
  `location` varchar(255) NOT NULL,
  `instruments` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`instruments`)),
  `api_endpoint` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `space_telescopes`
--

LOCK TABLES `space_telescopes` WRITE;
/*!40000 ALTER TABLE `space_telescopes` DISABLE KEYS */;
INSERT INTO `space_telescopes` VALUES ('HST','Hubble Space Telescope','NASA\'s visible/UV/near-IR telescope','2.4m','57.6m','Low Earth Orbit','\"{\\\"WFC3\\\": \\\"Wide Field Camera 3\\\", \\\"COS\\\": \\\"Cosmic Origins Spectrograph\\\"}\"','/api/v1/telescopes/hst'),('JWST','James Webb Space Telescope','NASA\'s infrared flagship telescope','6.5m','131.4m','L2 Lagrange Point','\"{\\\"NIRCam\\\": \\\"Near Infrared Camera\\\", \\\"MIRI\\\": \\\"Mid-Infrared Instrument\\\"}\"','/api/v1/telescopes/jwst');
/*!40000 ALTER TABLE `space_telescopes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `targets`
--

DROP TABLE IF EXISTS `targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `targets` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `telescope_id` varchar(36) DEFAULT NULL,
  `coordinates_ra` varchar(50) NOT NULL,
  `coordinates_dec` varchar(50) NOT NULL,
  `object_type` varchar(100) NOT NULL,
  `extra_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`extra_data`)),
  `filters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`filters`)),
  `required_drz_files` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`required_drz_files`)),
  `mosaic_config` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`mosaic_config`)),
  PRIMARY KEY (`id`),
  KEY `telescope_id` (`telescope_id`),
  CONSTRAINT `targets_ibfk_1` FOREIGN KEY (`telescope_id`) REFERENCES `space_telescopes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `targets`
--

LOCK TABLES `targets` WRITE;
/*!40000 ALTER TABLE `targets` DISABLE KEYS */;
INSERT INTO `targets` VALUES ('08fa392c-e7be-4b1f-81ad-24dc628ea367','Eagle Nebula','Famous for the Pillars of Creation','HST','18 18 48','-13 49 00','nebula',NULL,'{\"F657N\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 657, \"exposure\": 1200}, \"F673N\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 673, \"exposure\": 1200}, \"F110W\": {\"instrument\": \"WFC3/IR\", \"wavelength\": 1100, \"exposure\": 900}, \"F160W\": {\"instrument\": \"WFC3/IR\", \"wavelength\": 1600, \"exposure\": 900}}','[\"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos1_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos2_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos3_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos4_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos5_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f657n_v1_pos6_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos1_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos2_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos3_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos4_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos5_drz.fits\", \"hlsp_heritage_hst_wfc3-uvis_m16_f673n_v1_pos6_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos1_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos2_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos3_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f110w_v1_pos4_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos1_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos2_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos3_drz.fits\", \"hlsp_heritage_hst_wfc3-ir_m16_f160w_v1_pos4_drz.fits\"]','{\"uvis_panels\": 6, \"ir_panels\": 4, \"overlap\": 15}'),('111fae37-ceb5-4e3a-8d77-5d9a2e7dd736','Phantom Galaxy','Perfect spiral galaxy','JWST','01 36 42','+15 47 01','galaxy',NULL,'{\"F115W\": {\"instrument\": \"NIRCam\", \"wavelength\": 1150, \"exposure\": 944.832}, \"F200W\": {\"instrument\": \"NIRCam\", \"wavelength\": 2000, \"exposure\": 4208.816}, \"F770W\": {\"instrument\": \"MIRI\", \"wavelength\": 7700, \"exposure\": 4440.06}}','[\"jw02727-o001_t001_nircam_clear-f115w_drz.fits\", \"jw02727-o001_t001_nircam_clear-f150w_drz.fits\", \"jw02727-o001_t001_nircam_clear-f187n_drz.fits\", \"jw02727-o001_t001_nircam_clear-f200w_drz.fits\", \"jw02727-o001_t001_nircam_clear-f277w_drz.fits\", \"jw02727-o001_t001_nircam_clear-f335m_drz.fits\", \"jw02727-o001_t001_nircam_clear-f444w_drz.fits\", \"jw02727-o001_t001_miri_f560w_drz.fits\", \"jw02727-o001_t001_miri_f770w_drz.fits\", \"jw02727-o001_t001_miri_f1000w_drz.fits\", \"jw02727-o001_t001_miri_f1130w_drz.fits\", \"jw02727-o001_t001_miri_f2100w_drz.fits\"]','{\"mosaic_type\": \"full\", \"overlap\": 10}'),('12f1107d-40b0-4d21-b6f2-bf7a1e227d9e','Gabriela Mistral Nebula','Colorful nebula','HST','10 37 19','-58 38 00','nebula',NULL,'{\"F550M\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 550, \"exposure\": 654}, \"F658N\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 658, \"exposure\": 1300}, \"F660N\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 660, \"exposure\": 1960}}','[\"j8rh03_f550m_pos1_drz.fits\", \"j8rh03_f550m_pos2_drz.fits\", \"j8rh04_f658n_pos1_drz.fits\", \"j8rh04_f658n_pos2_drz.fits\", \"j8rh05_f660n_pos1_drz.fits\", \"j8rh05_f660n_pos2_drz.fits\"]','{\"panels\": 2, \"overlap\": 10}'),('256f7cd3-54a7-409a-a6bf-914d7759aa2d','Cigar Galaxy','Galaxy with active star formation','HST','09 55 52','+69 40 47','galaxy',NULL,'{\"F658N\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 658, \"exposure\": 1100}, \"F160W\": {\"instrument\": \"WFC3/IR\", \"wavelength\": 1600, \"exposure\": 1842}, \"F225W\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 225, \"exposure\": 1070}}','[\"j9e1020q_pos1_drz.fits\", \"j9e1020q_pos2_drz.fits\", \"j9e1020q_pos3_drz.fits\", \"j9e1020q_pos4_drz.fits\", \"j9e1020q_pos5_drz.fits\", \"ibhj01e4q_pos1_drz.fits\", \"ibhj01e4q_pos2_drz.fits\", \"ibhj01e4q_pos3_drz.fits\", \"ibhj01e4q_pos4_drz.fits\", \"ibhj01e4q_pos5_drz.fits\", \"ibhj01010_pos1_drz.fits\", \"ibhj01010_pos2_drz.fits\", \"ibhj01010_pos3_drz.fits\", \"ibhj01010_pos4_drz.fits\", \"ibhj01010_pos5_drz.fits\"]','{\"panels\": 5, \"overlap\": 12}'),('2c05e185-da99-4a09-b28c-09037a87c743','Sombrero Galaxy','Iconic galaxy with a bright nucleus','HST','12 39 59','-11 37 23','galaxy',NULL,'{\"F435W\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 435, \"exposure\": 2700}, \"F555W\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 555, \"exposure\": 2000}, \"F625W\": {\"instrument\": \"ACS/WFC\", \"wavelength\": 625, \"exposure\": 1400}}','[\"hst_9714_02_acs_wfc_f435w_j8lw02_drz.fits\", \"hst_9714_03_acs_wfc_f435w_j8lw03_drz.fits\", \"hst_9714_04_acs_wfc_f435w_j8lw04_drz.fits\", \"hst_9714_06_acs_wfc_f435w_j8lw06_drz.fits\", \"hst_9714_02_acs_wfc_f555w_j8lw02_drz.fits\", \"hst_9714_03_acs_wfc_f555w_j8lw03_drz.fits\", \"hst_9714_04_acs_wfc_f555w_j8lw04_drz.fits\", \"hst_9714_06_acs_wfc_f555w_j8lw06_drz.fits\", \"hst_9714_02_acs_wfc_f625w_j8lw02_drz.fits\", \"hst_9714_03_acs_wfc_f625w_j8lw03_drz.fits\", \"hst_9714_04_acs_wfc_f625w_j8lw04_drz.fits\", \"hst_9714_06_acs_wfc_f625w_j8lw06_drz.fits\"]','{\"positions\": [\"POS2\", \"POS3\", \"POS4\", \"POS6\"], \"overlap\": 15}'),('30928f29-35ca-47b7-964d-a20ad39db5e1','Southern Ring Nebula','Spectacular planetary nebula','JWST','10 07 02','-40 26 11','nebula',NULL,'{\"F090W\": {\"instrument\": \"NIRCam\", \"wavelength\": 900, \"exposure\": 1460.2}, \"F187N\": {\"instrument\": \"NIRCam\", \"wavelength\": 1870, \"exposure\": 2319.144}, \"F770W\": {\"instrument\": \"MIRI\", \"wavelength\": 7700, \"exposure\": 2708.432}}','[\"jw02733-o001_t001_nircam_clear-f090w_drz.fits\", \"jw02733-o001_t001_nircam_clear-f187n_drz.fits\", \"jw02733-o001_t001_nircam_clear-f212n_drz.fits\", \"jw02733-o001_t001_nircam_clear-f356w_drz.fits\", \"jw02733-o001_t001_nircam_clear-f444w_drz.fits\", \"jw02733-o001_t001_nircam_clear-f405n_drz.fits\", \"jw02733-o001_t001_nircam_clear-f470n_drz.fits\", \"jw02733-o001_t001_miri_f770w_drz.fits\", \"jw02733-o001_t001_miri_f1130w_drz.fits\", \"jw02733-o001_t001_miri_f1280w_drz.fits\", \"jw02733-o001_t001_miri_f1800w_drz.fits\"]','{\"mosaic_type\": \"full\", \"overlap\": 10}'),('95986125-c37b-45c2-aaa6-96b41dba58c4','Eagle Nebula','Famous for the Pillars of Creation','JWST','18 18 48','-13 49 00','nebula',NULL,'{\"F090W\": {\"instrument\": \"NIRCam\", \"wavelength\": 900, \"exposure\": 3221.04}, \"F187N\": {\"instrument\": \"NIRCam\", \"wavelength\": 1870, \"exposure\": 3221.04}, \"F200W\": {\"instrument\": \"NIRCam\", \"wavelength\": 2000, \"exposure\": 3221.04}, \"F335M\": {\"instrument\": \"NIRCam\", \"wavelength\": 3350, \"exposure\": 3221.04}, \"F444W\": {\"instrument\": \"NIRCam\", \"wavelength\": 4440, \"exposure\": 3221.04}, \"F405N\": {\"instrument\": \"NIRCam\", \"wavelength\": 4050, \"exposure\": 3221.04}, \"F470N\": {\"instrument\": \"NIRCam\", \"wavelength\": 4700, \"exposure\": 3221.04}, \"F770W\": {\"instrument\": \"MIRI\", \"wavelength\": 7700, \"exposure\": 2708.432}, \"F1130W\": {\"instrument\": \"MIRI\", \"wavelength\": 11300, \"exposure\": 2708.432}, \"F1280W\": {\"instrument\": \"MIRI\", \"wavelength\": 12800, \"exposure\": 2708.432}, \"F1800W\": {\"instrument\": \"MIRI\", \"wavelength\": 18000, \"exposure\": 2708.432}}','[\"jw02739-o001_t001_nircam_clear-f090w_drz.fits\", \"jw02739-o001_t001_nircam_clear-f187n_drz.fits\", \"jw02739-o001_t001_nircam_clear-f200w_drz.fits\", \"jw02739-o001_t001_nircam_clear-f335m_drz.fits\", \"jw02739-o001_t001_nircam_clear-f444w_drz.fits\", \"jw02739-o001_t001_nircam_clear-f405n_drz.fits\", \"jw02739-o001_t001_nircam_clear-f470n_drz.fits\", \"jw02739-o002_t001_miri_f770w_drz.fits\", \"jw02739-o002_t001_miri_f1130w_drz.fits\", \"jw02739-o002_t001_miri_f1280w_drz.fits\", \"jw02739-o002_t001_miri_f1800w_drz.fits\"]','{\"mosaic_type\": \"full\", \"overlap\": 10}'),('9e9ea377-c135-4035-9738-78c05b81fd45','Butterfly Nebula','Spectacular planetary nebula','HST','17 13 44','-37 06 16','nebula',NULL,'{\"F438W\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 438, \"exposure\": 270}, \"F555W\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 555, \"exposure\": 42}, \"F814W\": {\"instrument\": \"WFC3/UVIS\", \"wavelength\": 814, \"exposure\": 36}}','[\"ib5741010_pos1_drz.fits\", \"ib5741010_pos2_drz.fits\", \"ib5741010_pos3_drz.fits\", \"ib5741020_pos1_drz.fits\", \"ib5741020_pos2_drz.fits\", \"ib5741020_pos3_drz.fits\", \"ib5741030_pos1_drz.fits\", \"ib5741030_pos2_drz.fits\", \"ib5741030_pos3_drz.fits\"]','{\"panels\": 3, \"overlap\": 10}'),('b58f13c3-2dc2-44b4-8508-ae31d755bb5a','Stephan\'s Quintet','Compact group of five galaxies','JWST','22 35 58','+33 57 36','galaxy',NULL,'{\"F090W\": {\"instrument\": \"NIRCam\", \"wavelength\": 900, \"exposure\": 7086.27}, \"F150W\": {\"instrument\": \"NIRCam\", \"wavelength\": 1500, \"exposure\": 7086.27}, \"F770W\": {\"instrument\": \"MIRI\", \"wavelength\": 7700, \"exposure\": 2708.432}}','[\"jw02734-o001_t001_nircam_clear-f090w_drz.fits\", \"jw02734-o001_t001_nircam_clear-f150w_drz.fits\", \"jw02734-o001_t001_nircam_clear-f200w_drz.fits\", \"jw02734-o001_t001_nircam_clear-f277w_drz.fits\", \"jw02734-o001_t001_nircam_clear-f356w_drz.fits\", \"jw02734-o001_t001_nircam_clear-f444w_drz.fits\", \"jw02734-o001_t001_miri_f770w_drz.fits\", \"jw02734-o001_t001_miri_f1000w_drz.fits\", \"jw02734-o001_t001_miri_f1500w_drz.fits\"]','{\"mosaic_type\": \"full\", \"overlap\": 10}'),('fbb4630f-4a9a-43a8-9acc-bfb7b1a745d3','Cartwheel Galaxy','Ring galaxy formed by collision','JWST','00 37 41','-33 42 59','galaxy',NULL,'{\"F090W\": {\"instrument\": \"NIRCam\", \"wavelength\": 900, \"exposure\": 2748.616}, \"F150W\": {\"instrument\": \"NIRCam\", \"wavelength\": 1500, \"exposure\": 2748.616}, \"F200W\": {\"instrument\": \"NIRCam\", \"wavelength\": 2000, \"exposure\": 2748.616}, \"F770W\": {\"instrument\": \"MIRI\", \"wavelength\": 7700, \"exposure\": 4040.464}}','[\"jw02736-o001_t001_nircam_clear-f090w_drz.fits\", \"jw02736-o001_t001_nircam_clear-f150w_drz.fits\", \"jw02736-o001_t001_nircam_clear-f200w_drz.fits\", \"jw02736-o001_t001_nircam_clear-f277w_drz.fits\", \"jw02736-o001_t001_nircam_clear-f356w_drz.fits\", \"jw02736-o001_t001_nircam_clear-f444w_drz.fits\", \"jw02736-o001_t001_miri_f770w_drz.fits\", \"jw02736-o001_t001_miri_f1000w_drz.fits\", \"jw02736-o001_t001_miri_f1280w_drz.fits\", \"jw02736-o001_t001_miri_f1800w_drz.fits\"]','{\"mosaic_type\": \"full\", \"overlap\": 10}');
/*!40000 ALTER TABLE `targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tasks`
--

DROP TABLE IF EXISTS `tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tasks` (
  `id` varchar(36) NOT NULL,
  `user_id` varchar(36) DEFAULT NULL,
  `type` varchar(50) NOT NULL,
  `status` varchar(50) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  `parameters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`parameters`)),
  `result` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`result`)),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `tasks_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tasks`
--

LOCK TABLES `tasks` WRITE;
/*!40000 ALTER TABLE `tasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `tasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` char(36) NOT NULL,
  `email` varchar(255) NOT NULL,
  `username` varchar(100) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `firstname` varchar(100) DEFAULT NULL,
  `lastname` varchar(100) DEFAULT NULL,
  `level` enum('BEGINNER','INTERMEDIATE','ADVANCED') NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `last_login` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `role` enum('ADMIN','OPERATOR','USER') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('5246b858-af3d-498b-9ab2-86ff625e8675','admin@stellarstudio.com','admin','$2b$12$G2/8tyIMWEqqZC4dORRgYORza/UEZRYr2hdDNilfzuU8XMG/CWVfe',NULL,NULL,'BEGINNER','2025-01-29 16:47:51','2025-02-03 18:01:29',1,'ADMIN');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflows`
--

DROP TABLE IF EXISTS `workflows`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `workflows` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `steps` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`steps`)),
  `is_default` tinyint(1) DEFAULT NULL,
  `target_type` varchar(100) NOT NULL,
  `required_filters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`required_filters`)),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflows`
--

LOCK TABLES `workflows` WRITE;
/*!40000 ALTER TABLE `workflows` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflows` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-04 13:07:20
