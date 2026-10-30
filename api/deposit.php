<?php
header('Content-Type: application/json');
require_once __DIR__ . '/../config/db.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'message' => 'Only POST requests are supported.']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
if (!is_array($input)) {
    $input = $_POST;
}

$qrCode = trim($input['qr_code'] ?? '');
$materialId = (int)($input['material_id'] ?? 0);
$quantity = max(1, (int)($input['quantity'] ?? 1));

if (empty($qrCode) || empty($materialId)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'message' => 'Missing qr_code or material_id.']);
    exit;
}

$resident = EcoDB::getUserByQR($qrCode);
$material = EcoDB::getMaterialById($materialId);

if (!$resident) {
    http_response_code(404);
    echo json_encode(['success' => false, 'message' => 'Resident QR not recognized.']);
    exit;
}

if (!$material) {
    http_response_code(404);
    echo json_encode(['success' => false, 'message' => 'Material not recognized.']);
    exit;
}

$pointsEarned = $quantity * (int)$material['points_per_unit'];
$receiptNo = EcoDB::recordTransaction($resident['id'], $material['id'], $material['name'], $quantity, $pointsEarned);
$updated = EcoDB::getUserById($resident['id']);

echo json_encode([
    'success' => true,
    'message' => 'Deposit recorded successfully.',
    'receipt_no' => $receiptNo,
    'resident_name' => $resident['full_name'],
    'material' => $material['name'],
    'quantity' => $quantity,
    'points_earned' => $pointsEarned,
    'current_balance' => $updated['points']
]);
