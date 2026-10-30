<?php
require_once __DIR__ . '/config/db.php';

$receiptData = null;
$error = '';

$users = EcoDB::getUsers();
$residents = array_filter($users, fn($u) => ($u['role'] ?? 'resident') === 'resident');
$materials = EcoDB::getMaterials();

$prefillQR = '';
if (isset($_SESSION['user_id'])) {
    $me = EcoDB::getUserById($_SESSION['user_id']);
    if ($me) $prefillQR = $me['qr_code'];
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $qrCode = trim($_POST['qr_code'] ?? '');
    $materialId = (int)($_POST['material_id'] ?? 0);
    $quantity = max(1, (int)($_POST['quantity'] ?? 1));

    $resident = EcoDB::getUserByQR($qrCode);
    $material = EcoDB::getMaterialById($materialId);

    if (!$resident) {
        $error = 'Unrecognized QR Code. Please check the code or register first.';
    } elseif (!$material) {
        $error = 'Invalid material selected.';
    } else {
        $pointsEarned = $quantity * (int)$material['points_per_unit'];
        $receiptNo = EcoDB::recordTransaction($resident['id'], $material['id'], $material['name'], $quantity, $pointsEarned);
        $updatedResident = EcoDB::getUserById($resident['id']);

        $receiptData = [
            'receipt_no' => $receiptNo,
            'resident_name' => $resident['full_name'],
            'qr_code' => $resident['qr_code'],
            'material_name' => $material['name'],
            'quantity' => $quantity,
            'unit' => $material['unit'],
            'points_earned' => $pointsEarned,
            'new_total_points' => $updatedResident['points'],
            'date_time' => date('Y-m-d h:i A')
        ];
    }
}

$pageTitle = 'Automated Collection Station - EcoCoins';
require_once __DIR__ . '/includes/header.php';
require_once __DIR__ . '/includes/navbar.php';
?>

<main class="py-5">
  <div class="container py-lg-4">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="text-center mb-4">
          <span class="badge bg-success-subtle text-success px-3 py-2 rounded-pill fw-bold text-uppercase mb-2">Automated Collection Station Terminal</span>
          <h2 class="fw-bold text-dark mb-1">EcoCoins Smart Collection Unit</h2>
          <p class="text-secondary">Scan resident QR code and insert recyclables to automatically earn EcoPoints.</p>
        </div>

        <?php if (!empty($error)): ?>
          <div class="alert alert-danger rounded-4 py-3 mb-4"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>

        <?php if ($receiptData): ?>
          <div class="eco-card p-4 p-lg-5 mb-4 border-2 border-success">
            <div class="text-center mb-4">
              <div class="eco-brand-badge mb-2" style="width: 52px; height: 52px;">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <h3 class="fw-bold text-success mb-1">Recycling Deposit Successful!</h3>
              <p class="text-secondary small">Transaction validated & points credited to resident account.</p>
            </div>

            <div class="p-3 bg-light rounded-4 mb-4">
              <div class="d-flex justify-content-between py-2 border-bottom">
                <span class="text-secondary small">Receipt No:</span>
                <span class="fw-bold font-monospace"><?php echo $receiptData['receipt_no']; ?></span>
              </div>
              <div class="d-flex justify-content-between py-2 border-bottom">
                <span class="text-secondary small">Resident Name:</span>
                <span class="fw-semibold text-dark"><?php echo htmlspecialchars($receiptData['resident_name']); ?> (<?php echo $receiptData['qr_code']; ?>)</span>
              </div>
              <div class="d-flex justify-content-between py-2 border-bottom">
                <span class="text-secondary small">Material Deposited:</span>
                <span class="fw-semibold text-dark"><?php echo htmlspecialchars($receiptData['material_name']); ?></span>
              </div>
              <div class="d-flex justify-content-between py-2 border-bottom">
                <span class="text-secondary small">Quantity:</span>
                <span class="fw-semibold text-dark"><?php echo $receiptData['quantity']; ?> <?php echo $receiptData['unit']; ?>(s)</span>
              </div>
              <div class="d-flex justify-content-between py-2 border-bottom">
                <span class="text-secondary small">EcoPoints Earned:</span>
                <span class="fw-bold text-success fs-5">+<?php echo $receiptData['points_earned']; ?> pts</span>
              </div>
              <div class="d-flex justify-content-between py-2">
                <span class="text-secondary small">New Account Balance:</span>
                <span class="fw-bold text-dark fs-5"><?php echo number_format($receiptData['new_total_points']); ?> EcoPoints</span>
              </div>
            </div>

            <div class="d-flex gap-3 justify-content-center">
              <a href="station-simulator.php" class="btn btn-eco px-4">New Deposit</a>
              <a href="dashboard.php" class="btn btn-eco-outline px-4">View Dashboard</a>
            </div>
          </div>
        <?php endif; ?>

        <div class="eco-card p-4 p-lg-5 shadow-sm">
          <form action="station-simulator.php" method="POST">
            <div class="mb-4">
              <label class="form-label fw-bold text-dark">Resident QR Identification</label>
              <div class="input-group">
                <input type="text" name="qr_code" id="stationQrInput" class="form-control form-control-lg font-monospace rounded-start-3" placeholder="e.g. ECO-RES-88219" value="<?php echo htmlspecialchars($_POST['qr_code'] ?? $prefillQR); ?>" required>
                <button type="button" class="btn btn-outline-success" onclick="document.getElementById('stationQrInput').value='ECO-RES-88219';">Juan (Demo)</button>
              </div>
              <div class="form-text small">Select or scan resident QR code before depositing.</div>
            </div>

            <div class="mb-4">
              <label class="form-label fw-bold text-dark">Select Recyclable Material</label>
              <div class="row g-3">
                <?php foreach ($materials as $idx => $m): ?>
                  <div class="col-6 col-sm-3">
                    <label class="w-100 h-100">
                      <input type="radio" name="material_id" value="<?php echo $m['id']; ?>" class="d-none peer" <?php echo $idx === 0 ? 'checked' : ''; ?>>
                      <div class="p-3 border rounded-4 text-center cursor-pointer transition-all bg-light">
                        <div class="mb-2">
                          <?php if (strpos(strtolower($m['name']), 'bottle') !== false): ?>
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2980b9" stroke-width="2">
                              <path d="M10 2h4v3h-4z"/>
                              <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
                            </svg>
                          <?php else: ?>
                            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#b8621b" stroke-width="2">
                              <rect x="5" y="4" width="14" height="16" rx="3"/>
                              <ellipse cx="12" cy="7" rx="5" ry="2"/>
                            </svg>
                          <?php endif; ?>
                        </div>
                        <div class="fw-bold small text-dark mb-1"><?php echo htmlspecialchars($m['name']); ?></div>
                        <span class="badge bg-success-subtle text-success small">+<?php echo $m['points_per_unit']; ?> pts/<?php echo $m['unit']; ?></span>
                      </div>
                    </label>
                  </div>
                <?php endforeach; ?>
              </div>
            </div>

            <div class="mb-4">
              <label class="form-label fw-bold text-dark">Item Quantity</label>
              <input type="number" name="quantity" class="form-control form-control-lg rounded-3" value="1" min="1" max="100" required>
            </div>

            <div class="p-3 rounded-4 bg-light mb-4 d-flex align-items-center gap-3">
              <div class="spinner-grow text-success spinner-grow-sm" role="status"></div>
              <div class="small text-secondary">
                <strong class="text-dark">Automated Sensor Simulator Active:</strong> Optical & weight sensors ready to verify item authenticity.
              </div>
            </div>

            <button type="submit" class="btn btn-eco w-100 py-3 fs-5 fw-bold shadow-sm">
              Deposit Recyclable & Credit EcoPoints
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</main>

<style>
input[type="radio"]:checked + div {
  border-color: #1b5e3c !important;
  background-color: #d8efe0 !important;
  box-shadow: 0 0 0 2px #1b5e3c;
}
</style>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
