CREATE DATABASE IF NOT EXISTS `ecocoins_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ecocoins_db`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(120) NOT NULL,
  `email` varchar(120) NOT NULL UNIQUE,
  `password` varchar(255) NOT NULL,
  `role` enum('resident','admin') DEFAULT 'resident',
  `qr_code` varchar(64) NOT NULL UNIQUE,
  `points` int(11) DEFAULT 0,
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
(2, 'User', 'user@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-88219', 1250, '2026-10-10 09:30:00'),
(3, 'Annie Flores', 'annie@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-10492', 840, '2026-10-12 11:20:00'),
(4, 'Theresa Ramos', 'theresa@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-29381', 960, '2026-10-14 14:15:00'),
(5, 'Cathrine Santos', 'cathrine@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-50123', 1100, '2026-10-15 16:40:00'),
(6, 'Noel Batumbakal', 'noel@example.com', '$2y$10$wT8K48m1lYpYI2/iB9K1z.v1N0iN9B6t5K8GfV4P8B5K8GfV4P8B5', 'resident', 'ECO-RES-77401', 620, '2026-10-16 10:10:00');

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
(1, '10% Off at SM Lipa', 'Discounts', 500, 50, 'SM City Lipa', 'tag', 'available'),
(2, 'Eco Tote Bag', 'Merchandise', 1000, 30, 'Barangay Green Store', 'bag', 'available'),
(3, 'Discount Voucher (₱50) · Robinsons Lipa', 'Discounts', 1800, 40, 'Robinsons Place Lipa', 'ticket', 'available'),
(4, 'Free Drink · The Coffee Project', 'Partners', 750, 25, 'The Coffee Project Lipa', 'coffee', 'available'),
(5, 'EcoCoins Keychain', 'Merchandise', 300, 80, 'Barangay Green Store', 'key', 'available'),
(6, 'Movie Pass (1 Ticket) · SM Cinema Lipa', 'Partners', 1500, 20, 'SM Cinema Lipa', 'film', 'available');

INSERT INTO `redemptions` (`id`, `user_id`, `reward_id`, `reward_title`, `points_spent`, `redemption_code`, `status`, `created_at`) VALUES
(1, 2, 5, 'EcoCoins Keychain', 300, 'RDM-88219-01', 'claimed', '2026-10-15 14:00:00');
