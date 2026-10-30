<?php
require_once __DIR__ . '/config/db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user = EcoDB::getUserById($_SESSION['user_id']);
if (!$user) {
    header('Location: logout.php');
    exit;
}

$userTransactions = EcoDB::getTransactions($user['id']);

$bottleCount = 0;
$canCount = 0;
$otherCount = 0;

foreach ($userTransactions as $t) {
    $name = strtolower($t['material_name']);
    if (strpos($name, 'bottle') !== false || strpos($name, 'plastic') !== false) {
        $bottleCount += (int)$t['quantity'];
    } elseif (strpos($name, 'can') !== false) {
        $canCount += (int)$t['quantity'];
    } else {
        $otherCount += (int)$t['quantity'];
    }
}

$pageTitle = 'Dashboard - EcoCoins';
require_once __DIR__ . '/includes/header.php';
require_once __DIR__ . '/includes/navbar.php';
?>

<main class="py-4 py-lg-5">
  <div class="container">
    <div class="row g-4">
      <div class="col-lg-3">
        <?php require_once __DIR__ . '/includes/resident_sidebar.php'; ?>
      </div>

      <div class="col-lg-9">
        <div class="mb-4">
          <h2 class="fw-bold text-dark mb-1">Hello, <?php echo htmlspecialchars($user['full_name']); ?>!</h2>
          <p class="text-secondary">Here's your recycling summary.</p>
        </div>

        <div class="row g-4 mb-4">
          <div class="col-md-6 col-xl-5">
            <div class="p-4 rounded-4 text-white d-flex flex-column justify-content-between h-100 shadow-sm" style="background-color: #1b5e3c;">
              <div>
                <div class="d-flex align-items-center gap-2 mb-2 text-white-50">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  </svg>
                  <span class="fw-semibold">Total EcoPoints</span>
                </div>
                <div class="display-4 fw-extrabold mb-3"><?php echo number_format($user['points']); ?></div>
              </div>
              <div>
                <a href="rewards.php" class="btn btn-light rounded-pill px-4 fw-semibold text-success shadow-none">View Rewards</a>
              </div>
            </div>
          </div>

          <div class="col-md-6 col-xl-7">
            <div class="eco-card p-4 h-100">
              <h6 class="fw-bold text-dark mb-3">Recyclable Materials This Month</h6>
              <div class="row g-2">
                <div class="col-4">
                  <div class="p-3 rounded-4 text-center" style="background-color: #f0f7f4;">
                    <div class="mb-2 text-primary" style="color: #2980b9 !important;">
                      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 2h4v3h-4z"/>
                        <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
                      </svg>
                    </div>
                    <div class="fs-4 fw-bold text-dark mb-0"><?php echo $bottleCount; ?></div>
                    <div class="small text-secondary" style="font-size: 0.75rem;">Plastic Bottles</div>
                  </div>
                </div>

                <div class="col-4">
                  <div class="p-3 rounded-4 text-center" style="background-color: #fbf3ec;">
                    <div class="mb-2" style="color: #b8621b;">
                      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="5" y="4" width="14" height="16" rx="3"/>
                        <ellipse cx="12" cy="7" rx="5" ry="2"/>
                      </svg>
                    </div>
                    <div class="fs-4 fw-bold text-dark mb-0"><?php echo $canCount; ?></div>
                    <div class="small text-secondary" style="font-size: 0.75rem;">Cans</div>
                  </div>
                </div>

                <div class="col-4">
                  <div class="p-3 rounded-4 text-center" style="background-color: #f4eef9;">
                    <div class="mb-2" style="color: #6f588c;">
                      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                    </div>
                    <div class="fs-4 fw-bold text-dark mb-0"><?php echo $otherCount; ?></div>
                    <div class="small text-secondary" style="font-size: 0.75rem;">Others</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="row g-4">
          <div class="col-lg-7">
            <div class="eco-card p-4 h-100">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="fw-bold text-dark mb-0">Recent Activity</h6>
                <a href="history.php" class="text-success small fw-semibold text-decoration-none">View All</a>
              </div>

              <?php if (empty($userTransactions)): ?>
                <div class="text-center py-4 text-muted small">No recycling activities recorded yet.</div>
              <?php else: ?>
                <div class="list-group list-group-flush">
                  <?php foreach (array_slice($userTransactions, 0, 4) as $item): ?>
                    <?php 
                      $isCan = stripos($item['material_name'], 'can') !== false;
                      $tileClass = $isCan ? 'tile-orange' : 'tile-blue';
                    ?>
                    <div class="list-group-item px-0 py-3 d-flex align-items-center justify-content-between bg-transparent border-eco">
                      <div class="d-flex align-items-center gap-3">
                        <div class="eco-icon-tile <?php echo $tileClass; ?>">
                          <?php if ($isCan): ?>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <rect x="5" y="4" width="14" height="16" rx="3"/>
                              <ellipse cx="12" cy="7" rx="5" ry="2"/>
                            </svg>
                          <?php else: ?>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M10 2h4v3h-4z"/>
                              <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
                            </svg>
                          <?php endif; ?>
                        </div>
                        <div>
                          <div class="fw-bold text-dark small mb-0"><?php echo htmlspecialchars($item['material_name']); ?></div>
                          <div class="text-secondary" style="font-size: 0.75rem;"><?php echo date('M d, Y · h:i A', strtotime($item['created_at'])); ?></div>
                        </div>
                      </div>
                      <span class="text-success fw-bold small">+<?php echo $item['points_earned']; ?> pts</span>
                    </div>
                  <?php endforeach; ?>
                </div>
              <?php endif; ?>
            </div>
          </div>

          <div class="col-lg-5">
            <div class="eco-card p-4 text-center h-100 d-flex flex-column justify-content-between">
              <div>
                <h6 class="fw-bold text-dark mb-3 text-start">My QR Code</h6>
                <div class="qr-preview-box mb-3">
                  <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=<?php echo urlencode($user['qr_code']); ?>" alt="QR Code" class="img-fluid rounded-2" style="width: 150px; height: 150px;" onerror="this.src='';this.alt='<?php echo $user['qr_code']; ?>';">
                </div>
                <div class="fw-bold text-success mb-2"><?php echo htmlspecialchars($user['qr_code']); ?></div>
                <p class="text-secondary small mb-3">
                  Scan this code at the EcoCoins station before you insert your recyclables.
                </p>
              </div>
              <div>
                <a href="station-simulator.php" class="btn btn-outline-success btn-sm rounded-pill w-100 py-2">Test At Collection Station</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
