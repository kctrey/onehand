CREATE DATABASE /*!32312 IF NOT EXISTS*/ `SOLITAIRE` /*!40100 DEFAULT CHARACTER SET utf8mb4 */;

USE `SOLITAIRE`;

--
-- Table structure for table `games`
--

DROP TABLE IF EXISTS `games`;
CREATE TABLE `games` (
  `game_id` int(11) NOT NULL AUTO_INCREMENT,
  `game_type` varchar(8) DEFAULT NULL,
  `win` tinyint(4) DEFAULT NULL,
  `cards_left` int(10) unsigned NOT NULL,
  `four_matches` int(10) unsigned NOT NULL,
  `two_matches` int(10) unsigned NOT NULL,
  `first_match_type` varchar(1) DEFAULT NULL,
  `first_match_card` int(10) unsigned DEFAULT NULL,
  `fingerprint` varchar(100) DEFAULT NULL,
  `run_id` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`game_id`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=utf8mb4;
