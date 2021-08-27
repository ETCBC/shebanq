-- MySQL dump 10.14  Distrib 5.5.68-MariaDB, for Linux (x86_64)
--
-- Host: mysql11.dans.knaw.nl    Database: shebanq_note
-- ------------------------------------------------------
-- Server version	5.5.68-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `note`
--

DROP TABLE IF EXISTS `note`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `note` (
  `id` int(4) NOT NULL AUTO_INCREMENT,
  `version` varchar(32) DEFAULT NULL,
  `book` varchar(32) DEFAULT NULL,
  `chapter` int(4) DEFAULT NULL,
  `verse` int(4) DEFAULT NULL,
  `clause_atom` int(4) DEFAULT NULL,
  `created_by` int(4) DEFAULT NULL,
  `created_on` datetime DEFAULT NULL,
  `modified_on` datetime DEFAULT NULL,
  `is_shared` char(1) DEFAULT NULL,
  `shared_on` datetime DEFAULT NULL,
  `is_published` char(1) DEFAULT NULL,
  `published_on` datetime DEFAULT NULL,
  `status` char(1) DEFAULT NULL,
  `keywords` varchar(128) DEFAULT NULL,
  `ntext` longtext,
  `bulk` char(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `version` (`version`),
  KEY `book` (`book`,`chapter`,`verse`,`clause_atom`),
  KEY `created_by` (`created_by`),
  KEY `is_shared` (`is_shared`),
  KEY `is_published` (`is_published`),
  KEY `keywords` (`keywords`),
  CONSTRAINT `note_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `shebanq_web`.`auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=575810 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-02-05 12:18:21
