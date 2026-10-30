<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

class EcoDB {
    private static $pdo = null;
    private static $jsonFile = __DIR__ . '/../database/data.json';
    private static $isMySQL = false;

    public static function init() {
        if (self::$pdo !== null || self::$isMySQL) {
            return;
        }

        $host = '127.0.0.1';
        $user = 'root';
        $pass = '';
        $dbname = 'ecocoins_db';

        try {
            $rawPdo = new PDO("mysql:host=$host", $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_SILENT,
                PDO::ATTR_TIMEOUT => 2
            ]);
            $rawPdo->exec("CREATE DATABASE IF NOT EXISTS `$dbname` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            self::$pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_SILENT,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
            ]);
            self::$isMySQL = true;
            self::setupMySQLTables();
            self::seedDefaultData();
            return;
        } catch (\Throwable $e) {
            self::$isMySQL = false;
        }

        self::initJsonStore();
    }

    private static function setupMySQLTables() {
        if (!self::$pdo) return;
        self::$pdo->exec("CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(120) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('resident','admin') DEFAULT 'resident',
            qr_code VARCHAR(64) NOT NULL UNIQUE,
            points INT DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )");

        self::$pdo->exec("CREATE TABLE IF NOT EXISTS materials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            points_per_unit INT NOT NULL,
            unit VARCHAR(30) DEFAULT 'piece',
            icon VARCHAR(50) DEFAULT 'bottle',
            status ENUM('active','inactive') DEFAULT 'active'
        )");

        self::$pdo->exec("CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            material_id INT NULL,
            material_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL,
            points_earned INT NOT NULL,
            receipt_no VARCHAR(64) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )");

        self::$pdo->exec("CREATE TABLE IF NOT EXISTS rewards (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            category VARCHAR(50) NOT NULL,
            points_required INT NOT NULL,
            stock INT DEFAULT 100,
            partner_name VARCHAR(100) DEFAULT '',
            icon VARCHAR(50) DEFAULT 'tag',
            status ENUM('available','out_of_stock') DEFAULT 'available'
        )");

        self::$pdo->exec("CREATE TABLE IF NOT EXISTS redemptions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            reward_id INT NOT NULL,
            reward_title VARCHAR(150) NOT NULL,
            points_spent INT NOT NULL,
            redemption_code VARCHAR(64) NOT NULL,
            status ENUM('claimed','pending') DEFAULT 'claimed',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )");
    }

    private static function initJsonStore() {
        $dir = dirname(self::$jsonFile);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }

        if (!file_exists(self::$jsonFile)) {
            $initial = self::getDefaultSeedArray();
            file_put_contents(self::$jsonFile, json_encode($initial, JSON_PRETTY_PRINT));
        }
    }

    private static function getDefaultSeedArray() {
        return [
            'users' => [
                [
                    'id' => 1,
                    'full_name' => 'Admin Officer',
                    'email' => 'admin@ecocoins.ph',
                    'password' => password_hash('admin123', PASSWORD_DEFAULT),
                    'role' => 'admin',
                    'qr_code' => 'ECO-ADM-0001',
                    'points' => 0,
                    'created_at' => '2026-10-01 08:00:00'
                ],
                [
                    'id' => 2,
                    'full_name' => 'User',
                    'email' => 'user@example.com',
                    'password' => password_hash('user123', PASSWORD_DEFAULT),
                    'role' => 'resident',
                    'qr_code' => 'ECO-RES-88219',
                    'points' => 1250,
                    'created_at' => '2026-10-10 09:30:00'
                ],
                [
                    'id' => 3,
                    'full_name' => 'Annie Flores',
                    'email' => 'annie@example.com',
                    'password' => password_hash('user123', PASSWORD_DEFAULT),
                    'role' => 'resident',
                    'qr_code' => 'ECO-RES-10492',
                    'points' => 840,
                    'created_at' => '2026-10-12 11:20:00'
                ],
                [
                    'id' => 4,
                    'full_name' => 'Theresa Ramos',
                    'email' => 'theresa@example.com',
                    'password' => password_hash('user123', PASSWORD_DEFAULT),
                    'role' => 'resident',
                    'qr_code' => 'ECO-RES-29381',
                    'points' => 960,
                    'created_at' => '2026-10-14 14:15:00'
                ],
                [
                    'id' => 5,
                    'full_name' => 'Cathrine Santos',
                    'email' => 'cathrine@example.com',
                    'password' => password_hash('user123', PASSWORD_DEFAULT),
                    'role' => 'resident',
                    'qr_code' => 'ECO-RES-50123',
                    'points' => 1100,
                    'created_at' => '2026-10-15 16:40:00'
                ],
                [
                    'id' => 6,
                    'full_name' => 'Noel Batumbakal',
                    'email' => 'noel@example.com',
                    'password' => password_hash('user123', PASSWORD_DEFAULT),
                    'role' => 'resident',
                    'qr_code' => 'ECO-RES-77401',
                    'points' => 620,
                    'created_at' => '2026-10-16 10:10:00'
                ]
            ],
            'materials' => [
                ['id' => 1, 'name' => 'Plastic Bottle', 'category' => 'Plastic', 'points_per_unit' => 5, 'unit' => 'piece', 'icon' => 'bottle', 'status' => 'active'],
                ['id' => 2, 'name' => 'Can', 'category' => 'Metal', 'points_per_unit' => 8, 'unit' => 'piece', 'icon' => 'cup', 'status' => 'active'],
                ['id' => 3, 'name' => 'Glass Bottle', 'category' => 'Glass', 'points_per_unit' => 10, 'unit' => 'piece', 'icon' => 'glass', 'status' => 'active'],
                ['id' => 4, 'name' => 'Cardboard / Paper', 'category' => 'Paper', 'points_per_unit' => 4, 'unit' => 'kg', 'icon' => 'paper', 'status' => 'active']
            ],
            'transactions' => [
                ['id' => 1, 'user_id' => 2, 'material_id' => 1, 'material_name' => 'Plastic Bottle', 'quantity' => 2, 'points_earned' => 10, 'receipt_no' => 'REC-20261022-01', 'created_at' => '2026-10-22 10:24:00'],
                ['id' => 2, 'user_id' => 2, 'material_id' => 2, 'material_name' => 'Can', 'quantity' => 1, 'points_earned' => 8, 'receipt_no' => 'REC-20261021-02', 'created_at' => '2026-10-21 16:32:00'],
                ['id' => 3, 'user_id' => 2, 'material_id' => 1, 'material_name' => 'Plastic Bottle', 'quantity' => 2, 'points_earned' => 10, 'receipt_no' => 'REC-20261019-03', 'created_at' => '2026-10-19 11:20:00'],
                ['id' => 4, 'user_id' => 2, 'material_id' => 2, 'material_name' => 'Can', 'quantity' => 3, 'points_earned' => 24, 'receipt_no' => 'REC-20261018-04', 'created_at' => '2026-10-18 15:15:00'],
                ['id' => 5, 'user_id' => 2, 'material_id' => 1, 'material_name' => 'Plastic Bottle', 'quantity' => 1, 'points_earned' => 5, 'receipt_no' => 'REC-20261016-05', 'created_at' => '2026-10-16 09:40:00'],
                ['id' => 6, 'user_id' => 3, 'material_id' => 1, 'material_name' => 'Plastic Bottle', 'quantity' => 2, 'points_earned' => 10, 'receipt_no' => 'REC-20261022-06', 'created_at' => '2026-10-22 10:24:00'],
                ['id' => 7, 'user_id' => 4, 'material_id' => 2, 'material_name' => 'Can', 'quantity' => 3, 'points_earned' => 24, 'receipt_no' => 'REC-20261022-07', 'created_at' => '2026-10-22 10:11:00'],
                ['id' => 8, 'user_id' => 5, 'material_id' => 1, 'material_name' => 'Plastic Bottle', 'quantity' => 4, 'points_earned' => 20, 'receipt_no' => 'REC-20261022-08', 'created_at' => '2026-10-22 09:52:00'],
                ['id' => 9, 'user_id' => 6, 'material_id' => 2, 'material_name' => 'Can', 'quantity' => 1, 'points_earned' => 8, 'receipt_no' => 'REC-20261022-09', 'created_at' => '2026-10-22 09:30:00']
            ],
            'rewards' => [
                ['id' => 1, 'title' => '10% Off at SM Lipa', 'category' => 'Discounts', 'points_required' => 500, 'stock' => 50, 'partner_name' => 'SM City Lipa', 'icon' => 'tag', 'status' => 'available'],
                ['id' => 2, 'title' => 'Eco Tote Bag', 'category' => 'Merchandise', 'points_required' => 1000, 'stock' => 30, 'partner_name' => 'Barangay Green Store', 'icon' => 'bag', 'status' => 'available'],
                ['id' => 3, 'title' => 'Discount Voucher (₱50) · Robinsons Lipa', 'category' => 'Discounts', 'points_required' => 1800, 'stock' => 40, 'partner_name' => 'Robinsons Place Lipa', 'icon' => 'ticket', 'status' => 'available'],
                ['id' => 4, 'title' => 'Free Drink · The Coffee Project', 'category' => 'Partners', 'points_required' => 750, 'stock' => 25, 'partner_name' => 'The Coffee Project Lipa', 'icon' => 'coffee', 'status' => 'available'],
                ['id' => 5, 'title' => 'EcoCoins Keychain', 'category' => 'Merchandise', 'points_required' => 300, 'stock' => 80, 'partner_name' => 'Barangay Green Store', 'icon' => 'key', 'status' => 'available'],
                ['id' => 6, 'title' => 'Movie Pass (1 Ticket) · SM Cinema Lipa', 'category' => 'Partners', 'points_required' => 1500, 'stock' => 20, 'partner_name' => 'SM Cinema Lipa', 'icon' => 'film', 'status' => 'available']
            ],
            'redemptions' => [
                ['id' => 1, 'user_id' => 2, 'reward_id' => 5, 'reward_title' => 'EcoCoins Keychain', 'points_spent' => 300, 'redemption_code' => 'RDM-88219-01', 'status' => 'claimed', 'created_at' => '2026-10-15 14:00:00']
            ]
        ];
    }

    private static function seedDefaultData() {
        if (!self::$pdo) return;
        $stmt = self::$pdo->query("SELECT COUNT(*) AS total FROM users");
        $row = $stmt ? $stmt->fetch() : null;
        if ($row && $row['total'] > 0) return;

        $seeds = self::getDefaultSeedArray();
        foreach ($seeds['users'] as $u) {
            $q = self::$pdo->prepare("INSERT INTO users (id, full_name, email, password, role, qr_code, points, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            $q->execute([$u['id'], $u['full_name'], $u['email'], $u['password'], $u['role'], $u['qr_code'], $u['points'], $u['created_at']]);
        }
        foreach ($seeds['materials'] as $m) {
            $q = self::$pdo->prepare("INSERT INTO materials (id, name, category, points_per_unit, unit, icon, status) VALUES (?, ?, ?, ?, ?, ?, ?)");
            $q->execute([$m['id'], $m['name'], $m['category'], $m['points_per_unit'], $m['unit'], $m['icon'], $m['status']]);
        }
        foreach ($seeds['transactions'] as $t) {
            $q = self::$pdo->prepare("INSERT INTO transactions (id, user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            $q->execute([$t['id'], $t['user_id'], $t['material_id'], $t['material_name'], $t['quantity'], $t['points_earned'], $t['receipt_no'], $t['created_at']]);
        }
        foreach ($seeds['rewards'] as $r) {
            $q = self::$pdo->prepare("INSERT INTO rewards (id, title, category, points_required, stock, partner_name, icon, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            $q->execute([$r['id'], $r['title'], $r['category'], $r['points_required'], $r['stock'], $r['partner_name'], $r['icon'], $r['status']]);
        }
        foreach ($seeds['redemptions'] as $rd) {
            $q = self::$pdo->prepare("INSERT INTO redemptions (id, user_id, reward_id, reward_title, points_spent, redemption_code, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            $q->execute([$rd['id'], $rd['user_id'], $rd['reward_id'], $rd['reward_title'], $rd['points_spent'], $rd['redemption_code'], $rd['status'], $rd['created_at']]);
        }
    }

    private static function readJson() {
        self::initJsonStore();
        $content = file_get_contents(self::$jsonFile);
        $data = json_decode($content, true);
        if (!is_array($data)) {
            $data = self::getDefaultSeedArray();
            file_put_contents(self::$jsonFile, json_encode($data, JSON_PRETTY_PRINT));
        }
        return $data;
    }

    private static function writeJson($data) {
        self::initJsonStore();
        file_put_contents(self::$jsonFile, json_encode($data, JSON_PRETTY_PRINT));
    }

    public static function getUsers() {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->query("SELECT * FROM users ORDER BY id DESC");
            return $stmt ? $stmt->fetchAll() : [];
        }
        $data = self::readJson();
        return $data['users'] ?? [];
    }

    public static function getUserById($id) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("SELECT * FROM users WHERE id = ?");
            $stmt->execute([$id]);
            return $stmt->fetch();
        }
        $data = self::readJson();
        foreach ($data['users'] as $u) {
            if ($u['id'] == $id) return $u;
        }
        return null;
    }

    public static function getUserByEmail($email) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("SELECT * FROM users WHERE LOWER(email) = LOWER(?)");
            $stmt->execute([trim($email)]);
            return $stmt->fetch();
        }
        $data = self::readJson();
        foreach ($data['users'] as $u) {
            if (strtolower($u['email']) === strtolower(trim($email))) return $u;
        }
        return null;
    }

    public static function getUserByQR($qr) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("SELECT * FROM users WHERE qr_code = ?");
            $stmt->execute([trim($qr)]);
            return $stmt->fetch();
        }
        $data = self::readJson();
        foreach ($data['users'] as $u) {
            if (trim($u['qr_code']) === trim($qr)) return $u;
        }
        return null;
    }

    public static function createUser($fullName, $email, $password, $role = 'resident') {
        self::init();
        $code = 'ECO-RES-' . rand(10000, 99999);
        $hashed = password_hash($password, PASSWORD_DEFAULT);
        $createdAt = date('Y-m-d H:i:s');

        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("INSERT INTO users (full_name, email, password, role, qr_code, points, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)");
            $stmt->execute([$fullName, $email, $hashed, $role, $code, $createdAt]);
            return self::getUserById(self::$pdo->lastInsertId());
        }

        $data = self::readJson();
        $nextId = 1;
        foreach ($data['users'] as $u) {
            if ($u['id'] >= $nextId) $nextId = $u['id'] + 1;
        }
        $newUser = [
            'id' => $nextId,
            'full_name' => $fullName,
            'email' => $email,
            'password' => $hashed,
            'role' => $role,
            'qr_code' => $code,
            'points' => 0,
            'created_at' => $createdAt
        ];
        $data['users'][] = $newUser;
        self::writeJson($data);
        return $newUser;
    }

    public static function updateUserPoints($userId, $diff) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("UPDATE users SET points = GREATEST(0, points + ?) WHERE id = ?");
            $stmt->execute([$diff, $userId]);
            return;
        }
        $data = self::readJson();
        foreach ($data['users'] as &$u) {
            if ($u['id'] == $userId) {
                $u['points'] = max(0, $u['points'] + $diff);
                break;
            }
        }
        self::writeJson($data);
    }

    public static function getMaterials() {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->query("SELECT * FROM materials ORDER BY id ASC");
            return $stmt ? $stmt->fetchAll() : [];
        }
        $data = self::readJson();
        return $data['materials'] ?? [];
    }

    public static function getMaterialById($id) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("SELECT * FROM materials WHERE id = ?");
            $stmt->execute([$id]);
            return $stmt->fetch();
        }
        $data = self::readJson();
        foreach ($data['materials'] as $m) {
            if ($m['id'] == $id) return $m;
        }
        return null;
    }

    public static function saveMaterial($name, $category, $points, $unit, $icon, $id = null) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            if ($id) {
                $stmt = self::$pdo->prepare("UPDATE materials SET name = ?, category = ?, points_per_unit = ?, unit = ?, icon = ? WHERE id = ?");
                $stmt->execute([$name, $category, $points, $unit, $icon, $id]);
            } else {
                $stmt = self::$pdo->prepare("INSERT INTO materials (name, category, points_per_unit, unit, icon, status) VALUES (?, ?, ?, ?, ?, 'active')");
                $stmt->execute([$name, $category, $points, $unit, $icon]);
            }
            return;
        }
        $data = self::readJson();
        if ($id) {
            foreach ($data['materials'] as &$m) {
                if ($m['id'] == $id) {
                    $m['name'] = $name;
                    $m['category'] = $category;
                    $m['points_per_unit'] = (int)$points;
                    $m['unit'] = $unit;
                    $m['icon'] = $icon;
                    break;
                }
            }
        } else {
            $nextId = 1;
            foreach ($data['materials'] as $m) {
                if ($m['id'] >= $nextId) $nextId = $m['id'] + 1;
            }
            $data['materials'][] = [
                'id' => $nextId,
                'name' => $name,
                'category' => $category,
                'points_per_unit' => (int)$points,
                'unit' => $unit,
                'icon' => $icon,
                'status' => 'active'
            ];
        }
        self::writeJson($data);
    }

    public static function getTransactions($userId = null) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            if ($userId) {
                $stmt = self::$pdo->prepare("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC");
                $stmt->execute([$userId]);
            } else {
                $stmt = self::$pdo->query("SELECT t.*, u.full_name AS resident_name FROM transactions t LEFT JOIN users u ON t.user_id = u.id ORDER BY t.created_at DESC");
            }
            return $stmt ? $stmt->fetchAll() : [];
        }
        $data = self::readJson();
        $list = $data['transactions'] ?? [];
        if ($userId) {
            $filtered = [];
            foreach ($list as $t) {
                if ($t['user_id'] == $userId) $filtered[] = $t;
            }
            usort($filtered, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
            return $filtered;
        }
        $userMap = [];
        foreach ($data['users'] as $u) {
            $userMap[$u['id']] = $u['full_name'];
        }
        foreach ($list as &$t) {
            $t['resident_name'] = $userMap[$t['user_id']] ?? 'Unknown';
        }
        usort($list, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
        return $list;
    }

    public static function recordTransaction($userId, $materialId, $materialName, $quantity, $pointsEarned) {
        self::init();
        $receipt = 'REC-' . date('Ymd') . '-' . rand(1000, 9999);
        $createdAt = date('Y-m-d H:i:s');

        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)");
            $stmt->execute([$userId, $materialId, $materialName, $quantity, $pointsEarned, $receipt, $createdAt]);
            self::updateUserPoints($userId, $pointsEarned);
            return $receipt;
        }

        $data = self::readJson();
        $nextId = 1;
        foreach ($data['transactions'] as $t) {
            if ($t['id'] >= $nextId) $nextId = $t['id'] + 1;
        }
        $data['transactions'][] = [
            'id' => $nextId,
            'user_id' => (int)$userId,
            'material_id' => (int)$materialId,
            'material_name' => $materialName,
            'quantity' => (int)$quantity,
            'points_earned' => (int)$pointsEarned,
            'receipt_no' => $receipt,
            'created_at' => $createdAt
        ];
        self::writeJson($data);
        self::updateUserPoints($userId, $pointsEarned);
        return $receipt;
    }

    public static function getRewards() {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->query("SELECT * FROM rewards ORDER BY points_required ASC");
            return $stmt ? $stmt->fetchAll() : [];
        }
        $data = self::readJson();
        $list = $data['rewards'] ?? [];
        usort($list, fn($a, $b) => $a['points_required'] <=> $b['points_required']);
        return $list;
    }

    public static function getRewardById($id) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("SELECT * FROM rewards WHERE id = ?");
            $stmt->execute([$id]);
            return $stmt->fetch();
        }
        $data = self::readJson();
        foreach ($data['rewards'] as $r) {
            if ($r['id'] == $id) return $r;
        }
        return null;
    }

    public static function saveReward($title, $category, $points, $stock, $partner, $icon, $id = null) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            if ($id) {
                $stmt = self::$pdo->prepare("UPDATE rewards SET title = ?, category = ?, points_required = ?, stock = ?, partner_name = ?, icon = ? WHERE id = ?");
                $stmt->execute([$title, $category, $points, $stock, $partner, $icon, $id]);
            } else {
                $stmt = self::$pdo->prepare("INSERT INTO rewards (title, category, points_required, stock, partner_name, icon, status) VALUES (?, ?, ?, ?, ?, ?, 'available')");
                $stmt->execute([$title, $category, $points, $stock, $partner, $icon]);
            }
            return;
        }
        $data = self::readJson();
        if ($id) {
            foreach ($data['rewards'] as &$r) {
                if ($r['id'] == $id) {
                    $r['title'] = $title;
                    $r['category'] = $category;
                    $r['points_required'] = (int)$points;
                    $r['stock'] = (int)$stock;
                    $r['partner_name'] = $partner;
                    $r['icon'] = $icon;
                    break;
                }
            }
        } else {
            $nextId = 1;
            foreach ($data['rewards'] as $r) {
                if ($r['id'] >= $nextId) $nextId = $r['id'] + 1;
            }
            $data['rewards'][] = [
                'id' => $nextId,
                'title' => $title,
                'category' => $category,
                'points_required' => (int)$points,
                'stock' => (int)$stock,
                'partner_name' => $partner,
                'icon' => $icon,
                'status' => 'available'
            ];
        }
        self::writeJson($data);
    }

    public static function redeemReward($userId, $rewardId) {
        self::init();
        $user = self::getUserById($userId);
        $reward = self::getRewardById($rewardId);

        if (!$user || !$reward) {
            return ['success' => false, 'message' => 'User or Reward not found.'];
        }

        if ($user['points'] < $reward['points_required']) {
            return ['success' => false, 'message' => 'Insufficient EcoPoints balance.'];
        }

        if (isset($reward['stock']) && $reward['stock'] <= 0) {
            return ['success' => false, 'message' => 'This reward is currently out of stock.'];
        }

        $code = 'RDM-' . substr(md5(uniqid()), 0, 8);
        $createdAt = date('Y-m-d H:i:s');

        if (self::$isMySQL && self::$pdo) {
            $stmt = self::$pdo->prepare("INSERT INTO redemptions (user_id, reward_id, reward_title, points_spent, redemption_code, status, created_at) VALUES (?, ?, ?, ?, ?, 'claimed', ?)");
            $stmt->execute([$userId, $rewardId, $reward['title'], $reward['points_required'], $code, $createdAt]);
            self::$pdo->prepare("UPDATE rewards SET stock = GREATEST(0, stock - 1) WHERE id = ?")->execute([$rewardId]);
            self::updateUserPoints($userId, -$reward['points_required']);
            return ['success' => true, 'code' => $code, 'new_points' => $user['points'] - $reward['points_required']];
        }

        $data = self::readJson();
        $nextId = 1;
        foreach ($data['redemptions'] as $rd) {
            if ($rd['id'] >= $nextId) $nextId = $rd['id'] + 1;
        }
        $data['redemptions'][] = [
            'id' => $nextId,
            'user_id' => (int)$userId,
            'reward_id' => (int)$rewardId,
            'reward_title' => $reward['title'],
            'points_spent' => (int)$reward['points_required'],
            'redemption_code' => $code,
            'status' => 'claimed',
            'created_at' => $createdAt
        ];
        foreach ($data['rewards'] as &$r) {
            if ($r['id'] == $rewardId && isset($r['stock'])) {
                $r['stock'] = max(0, $r['stock'] - 1);
            }
        }
        self::writeJson($data);
        self::updateUserPoints($userId, -$reward['points_required']);

        return ['success' => true, 'code' => $code, 'new_points' => $user['points'] - $reward['points_required']];
    }

    public static function getRedemptions($userId = null) {
        self::init();
        if (self::$isMySQL && self::$pdo) {
            if ($userId) {
                $stmt = self::$pdo->prepare("SELECT * FROM redemptions WHERE user_id = ? ORDER BY created_at DESC");
                $stmt->execute([$userId]);
            } else {
                $stmt = self::$pdo->query("SELECT rd.*, u.full_name AS resident_name FROM redemptions rd LEFT JOIN users u ON rd.user_id = u.id ORDER BY rd.created_at DESC");
            }
            return $stmt ? $stmt->fetchAll() : [];
        }
        $data = self::readJson();
        $list = $data['redemptions'] ?? [];
        if ($userId) {
            $filtered = [];
            foreach ($list as $rd) {
                if ($rd['user_id'] == $userId) $filtered[] = $rd;
            }
            usort($filtered, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
            return $filtered;
        }
        $userMap = [];
        foreach ($data['users'] as $u) {
            $userMap[$u['id']] = $u['full_name'];
        }
        foreach ($list as &$rd) {
            $rd['resident_name'] = $userMap[$rd['user_id']] ?? 'Unknown';
        }
        usort($list, fn($a, $b) => strcmp($b['created_at'], $a['created_at']));
        return $list;
    }

    public static function getSystemStats() {
        self::init();
        $users = self::getUsers();
        $residents = array_filter($users, fn($u) => ($u['role'] ?? 'resident') === 'resident');
        $transactions = self::getTransactions();
        $rewards = self::getRewards();
        $redemptions = self::getRedemptions();

        $today = date('Y-m-d');
        $todayItems = 0;
        $totalPointsIssued = 0;
        $materialCounts = ['Plastic Bottles' => 0, 'Cans' => 0, 'Others' => 0];

        foreach ($transactions as $t) {
            $totalPointsIssued += (int)$t['points_earned'];
            if (strpos($t['created_at'], $today) === 0) {
                $todayItems += (int)$t['quantity'];
            }
            $mat = strtolower($t['material_name']);
            if (strpos($mat, 'bottle') !== false || strpos($mat, 'plastic') !== false) {
                $materialCounts['Plastic Bottles'] += (int)$t['quantity'];
            } elseif (strpos($mat, 'can') !== false) {
                $materialCounts['Cans'] += (int)$t['quantity'];
            } else {
                $materialCounts['Others'] += (int)$t['quantity'];
            }
        }

        return [
            'total_residents' => count($residents),
            'today_items' => $todayItems,
            'total_points_issued' => $totalPointsIssued,
            'total_redemptions' => count($redemptions),
            'material_counts' => $materialCounts,
            'recent_transactions' => array_slice($transactions, 0, 6)
        ];
    }
}
