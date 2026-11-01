CREATE DATABASE IF NOT EXISTS `ecocoins_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ecocoins_db`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(120) NOT NULL UNIQUE,
  `password` varchar(255) NOT NULL,
  `role` enum('resident','staff','admin') DEFAULT 'resident',
  `qr_code` varchar(64) NOT NULL UNIQUE,
  `points` int(11) DEFAULT 0,
  `status` varchar(20) DEFAULT 'active',
  `station_name` varchar(255) DEFAULT 'Barangay Pinagkawitan, Lipa City',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `materials` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `points_per_unit` int(11) NOT NULL,
  `unit` varchar(30) DEFAULT 'piece',
  `icon` varchar(50) DEFAULT 'bottle',
  `status` enum('active','inactive') DEFAULT 'active',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `transactions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `material_id` int(11) DEFAULT NULL,
  `material_name` varchar(100) NOT NULL,
  `quantity` int(11) NOT NULL,
  `points_earned` int(11) NOT NULL,
  `receipt_no` varchar(64) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `rewards` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(150) NOT NULL,
  `category` varchar(50) NOT NULL,
  `points_required` int(11) NOT NULL,
  `stock` int(11) DEFAULT 100,
  `partner_name` varchar(100) DEFAULT '',
  `icon` varchar(50) DEFAULT 'tag',
  `status` enum('available','out_of_stock') DEFAULT 'available',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `redemptions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `reward_id` int(11) NOT NULL,
  `reward_title` varchar(150) NOT NULL,
  `points_spent` int(11) NOT NULL,
  `redemption_code` varchar(64) NOT NULL,
  `status` enum('claimed','pending') DEFAULT 'claimed',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `users` (`id`, `full_name`, `email`, `password`, `role`, `qr_code`, `points`, `created_at`) VALUES
(1, 'Admin Officer', 'admin@ecocoins.ph', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'admin', 'ECO-ADM-0001', 0, '2026-10-01 08:00:00'),
(2, 'Barangay Staff', 'staff@ecocoins.ph', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'staff', 'ECO-STF-0001', 0, '2026-10-02 08:00:00'),
(3, 'User', 'user@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-88219', 1250, '2026-10-10 09:30:00'),
(3, 'Annie Flores', 'annie@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-10492', 840, '2026-10-12 11:20:00'),
(4, 'Theresa Ramos', 'theresa@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-29381', 960, '2026-10-14 14:15:00'),
(5, 'Cathrine Santos', 'cathrine@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-50123', 1100, '2026-10-15 16:40:00'),
(6, 'Noel Batumbakal', 'noel@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-77401', 620, '2026-10-16 10:10:00'),
(7, 'Juan Dela Cruz', 'juan.delacruz@example.com', 'user123', 'resident', 'ECO-RES-30101', 350, '2026-10-15 08:30:00'),
(8, 'Maria Clara De los Santos', 'maria.delossantos@example.com', 'user123', 'resident', 'ECO-RES-30102', 720, '2026-10-15 09:15:00'),
(9, 'Jose Rizalino Mercado', 'jose.mercado@example.com', 'user123', 'resident', 'ECO-RES-30103', 540, '2026-10-16 10:00:00'),
(10, 'Angela Mae Garcia', 'angela.garcia@example.com', 'user123', 'resident', 'ECO-RES-30104', 280, '2026-10-16 11:20:00'),
(11, 'Gabriel Paolo Mendoza', 'gabriel.mendoza@example.com', 'user123', 'resident', 'ECO-RES-30105', 890, '2026-10-17 08:45:00'),
(12, 'Beatrice Nicole Reyes', 'beatrice.reyes@example.com', 'user123', 'resident', 'ECO-RES-30106', 410, '2026-10-17 13:10:00'),
(13, 'Christian Dave Bautista', 'christian.bautista@example.com', 'user123', 'resident', 'ECO-RES-30107', 630, '2026-10-18 09:05:00'),
(14, 'Danica Joy Fernandez', 'danica.fernandez@example.com', 'user123', 'resident', 'ECO-RES-30108', 150, '2026-10-18 14:30:00'),
(15, 'Emmanuel Luis Cruz', 'emmanuel.cruz@example.com', 'user123', 'resident', 'ECO-RES-30109', 980, '2026-10-19 10:15:00'),
(16, 'Frances Diana Villanueva', 'frances.villanueva@example.com', 'user123', 'resident', 'ECO-RES-30110', 320, '2026-10-19 15:40:00'),
(17, 'Gerald Ryan Ramos', 'gerald.ramos@example.com', 'user123', 'resident', 'ECO-RES-30111', 470, '2026-10-20 08:25:00'),
(18, 'Hannah Patricia Castro', 'hannah.castro@example.com', 'user123', 'resident', 'ECO-RES-30112', 810, '2026-10-20 11:50:00'),
(19, 'Ian Joseph Aquino', 'ian.aquino@example.com', 'user123', 'resident', 'ECO-RES-30113', 220, '2026-10-21 09:40:00'),
(20, 'Jasmine Rose Salazar', 'jasmine.salazar@example.com', 'user123', 'resident', 'ECO-RES-30114', 590, '2026-10-21 14:15:00'),
(21, 'Kevin Mark Navarro', 'kevin.navarro@example.com', 'user123', 'resident', 'ECO-RES-30115', 660, '2026-10-22 10:30:00'),
(22, 'Kimberly Ann Morales', 'kimberly.morales@example.com', 'user123', 'resident', 'ECO-RES-30116', 390, '2026-10-22 16:05:00'),
(23, 'Lorenzo Miguel Soriano', 'lorenzo.soriano@example.com', 'user123', 'resident', 'ECO-RES-30117', 740, '2026-10-23 08:50:00'),
(24, 'Maricar Lopez Pascual', 'maricar.pascual@example.com', 'user123', 'resident', 'ECO-RES-30118', 510, '2026-10-23 13:35:00'),
(25, 'Nathaniel David Tolentino', 'nathaniel.tolentino@example.com', 'user123', 'resident', 'ECO-RES-30119', 180, '2026-10-24 09:10:00'),
(26, 'Olivia Grace Domingo', 'olivia.domingo@example.com', 'user123', 'resident', 'ECO-RES-30120', 850, '2026-10-24 15:20:00'),
(27, 'Patrick James Cortez', 'patrick.cortez@example.com', 'user123', 'resident', 'ECO-RES-30121', 430, '2026-10-25 10:45:00'),
(28, 'Queenie May Alcantara', 'queenie.alcantara@example.com', 'user123', 'resident', 'ECO-RES-30122', 670, '2026-10-25 14:00:00'),
(29, 'Rafael Vincent Valdez', 'rafael.valdez@example.com', 'user123', 'resident', 'ECO-RES-30123', 290, '2026-10-26 08:15:00'),
(30, 'Stephanie Joy Manalo', 'stephanie.manalo@example.com', 'user123', 'resident', 'ECO-RES-30124', 920, '2026-10-26 11:30:00'),
(31, 'Tristan Angelo Miranda', 'tristan.miranda@example.com', 'user123', 'resident', 'ECO-RES-30125', 360, '2026-10-27 09:25:00'),
(32, 'Vanessa Marie Pineda', 'vanessa.pineda@example.com', 'user123', 'resident', 'ECO-RES-30126', 580, '2026-10-27 15:10:00'),
(33, 'William Alexander De Leon', 'william.deleon@example.com', 'user123', 'resident', 'ECO-RES-30127', 770, '2026-10-28 10:05:00'),
(34, 'Xyriel Faye Guinto', 'xyriel.guinto@example.com', 'user123', 'resident', 'ECO-RES-30128', 240, '2026-10-28 14:40:00'),
(35, 'Yuri Sebastian Ocampo', 'yuri.ocampo@example.com', 'user123', 'resident', 'ECO-RES-30129', 610, '2026-10-29 08:40:00'),
(36, 'Zoe Isabelle Roxas', 'zoe.roxas@example.com', 'user123', 'resident', 'ECO-RES-30130', 880, '2026-10-29 13:15:00');

INSERT INTO `materials` (`id`, `name`, `category`, `points_per_unit`, `unit`, `icon`, `status`) VALUES
(1, 'Plastic Bottle', 'Plastic', 5, 'piece', 'bottle', 'active'),
(2, 'Can', 'Metal', 8, 'piece', 'cup', 'active'),
(3, 'Glass Bottle', 'Glass', 10, 'piece', 'glass', 'active'),
(4, 'Cardboard / Paper', 'Paper', 4, 'kg', 'paper', 'active');

INSERT INTO `transactions` (`id`, `user_id`, `material_id`, `material_name`, `quantity`, `points_earned`, `receipt_no`, `created_at`) VALUES
(1, 2, 1, 'Plastic Bottle', 2, 10, 'REC-20261022-01', '2026-10-22 10:24:00'),
(2, 2, 2, 'Can', 1, 8, 'REC-20261021-02', '2026-10-21 16:32:00'),
(3, 2, 1, 'Plastic Bottle', 2, 10, 'REC-20261019-03', '2026-10-19 11:20:00'),
(4, 2, 2, 'Can', 3, 24, 'REC-20261018-04', '2026-10-18 15:15:00'),
(5, 2, 1, 'Plastic Bottle', 1, 5, 'REC-20261016-05', '2026-10-16 09:40:00'),
(6, 3, 1, 'Plastic Bottle', 2, 10, 'REC-20261022-06', '2026-10-22 10:24:00'),
(7, 4, 2, 'Can', 3, 24, 'REC-20261022-07', '2026-10-22 10:11:00'),
(8, 5, 1, 'Plastic Bottle', 4, 20, 'REC-20261022-08', '2026-10-22 09:52:00'),
(9, 6, 2, 'Can', 1, 8, 'REC-20261022-09', '2026-10-22 09:30:00');

INSERT INTO `rewards` (`id`, `title`, `category`, `points_required`, `stock`, `partner_name`, `icon`, `status`) VALUES
(1, '1kg Sinandomeng Rice (Bigas)', 'Food Staples', 300, 80, 'Barangay Food Bank', 'bag', 'available'),
(2, '5kg Dinorado Rice (Bigas)', 'Food Staples', 1400, 40, 'Barangay Food Bank', 'bag', 'available'),
(3, 'Delata Pack (2 Sardinas + 1 Corned Beef)', 'Canned Goods', 250, 75, 'Barangay Relief Hub', 'cup', 'available'),
(4, 'EcoCoins Heavy-Duty Payong (Umbrella)', 'Merchandise', 450, 50, 'Barangay Green Store', 'tag', 'available'),
(5, 'Eco Tote Bag (Reusable)', 'Merchandise', 200, 100, 'Barangay Green Store', 'bag', 'available'),
(6, 'Noodles & Coffee Bundle (3 Noodles + 3 Coffee)', 'Food Staples', 180, 90, 'Barangay Food Bank', 'coffee', 'available'),
(7, 'Family Hygiene Kit (Bath Soap, Detergent, Toothpaste)', 'Household', 350, 60, 'Barangay Health Center', 'tag', 'available'),
(8, 'Stainless Water Tumbler (500ml)', 'Merchandise', 500, 45, 'Barangay Green Store', 'bottle', 'available');

INSERT INTO `redemptions` (`id`, `user_id`, `reward_id`, `reward_title`, `points_spent`, `redemption_code`, `status`, `created_at`) VALUES
(1, 2, 5, 'EcoCoins Keychain', 300, 'RDM-88219-01', 'claimed', '2026-10-15 14:00:00');

CREATE TABLE IF NOT EXISTS `stations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `station_code` varchar(50) NOT NULL UNIQUE,
  `station_name` varchar(150) NOT NULL,
  `location` varchar(255) NOT NULL,
  `barangay` varchar(100) NOT NULL,
  `city` varchar(100) NOT NULL,
  `assigned_staff` varchar(150) DEFAULT '',
  `status` varchar(20) DEFAULT 'active',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `stations` (`id`, `station_code`, `station_name`, `location`, `barangay`, `city`, `assigned_staff`, `status`, `created_at`) VALUES
(1, 'STN-LP-01', 'Pinagkawitan Collection Hub', 'Barangay Pinagkawitan, Lipa City', 'Pinagkawitan', 'Lipa City', 'Barangay Staff', 'active', '2026-10-02 08:00:00');
