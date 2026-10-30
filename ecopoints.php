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

$bottlePoints = 0;
$canPoints = 0;
$otherPoints = 0;

foreach ($userTransactions as $t) {
    $name = strtolower($t['material_name']);
    $pts = (int)$t['points_earned'];
    if (strpos($name, 'bottle') !== false || strpos($name, 'plastic') !== false) {
        $bottlePoints += $pts;
    } elseif (strpos($name, 'can') !== false) {
        $canPoints += $pts;
    } else {
        $otherPoints += $pts;
    }
}

$totalEarned = max(1, $bottlePoints + $canPoints + $otherPoints);
$bottlePct = round(($bottlePoints / $totalEarned) * 100);
$canPct = round(($canPoints / $totalEarned) * 100);
$otherPct = round(($otherPoints / $totalEarned) * 100);

$pageTitle = 'My EcoPoints - EcoCoins';
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
          <h2 class="fw-bold text-dark mb-1">My EcoPoints</h2>
          <p class="text-secondary">Your efforts make a difference!</p>
        </div>

        <div class="row g-4 mb-4">
          <div class="col-lg-5">
            <div class="eco-card p-4 p-xl-5 text-center h-100 d-flex flex-column justify-content-between">
              <div>
                <div class="eco-circle-meter mb-3">
                  <div class="text-success mb-1">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                    </svg>
                  </div>
                  <div class="h1 fw-extrabold text-dark mb-0"><?php echo number_format($user['points']); ?></div>
                  <div class="small text-secondary fw-semibold">EcoPoints</div>
                </div>
              </div>

              <div>
                <a href="rewards.php" class="btn btn-eco w-100 py-2">Redeem Rewards</a>
              </div>
            </div>
          </div>

          <div class="col-lg-7">
            <div class="eco-card p-4 p-xl-5 h-100 d-flex flex-column justify-content-center">
              <h5 class="fw-bold text-dark mb-4">Points Breakdown</h5>

              <div class="mb-4">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <div class="d-flex align-items-center gap-2">
                    <div class="eco-icon-tile tile-blue" style="width: 32px; height: 32px;">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 2h4v3h-4z"/>
                        <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
                      </svg>
                    </div>
                    <span class="fw-semibold text-dark small">Plastic Bottles</span>
                  </div>
                  <span class="fw-bold text-dark small"><?php echo $bottlePoints; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: <?php echo $bottlePct; ?>%; background-color: #2980b9;"></div>
                </div>
              </div>

              <div class="mb-4">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <div class="d-flex align-items-center gap-2">
                    <div class="eco-icon-tile tile-orange" style="width: 32px; height: 32px;">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="5" y="4" width="14" height="16" rx="3"/>
                        <ellipse cx="12" cy="7" rx="5" ry="2"/>
                      </svg>
                    </div>
                    <span class="fw-semibold text-dark small">Cans</span>
                  </div>
                  <span class="fw-bold text-dark small"><?php echo $canPoints; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: <?php echo $canPct; ?>%; background-color: #b8621b;"></div>
                </div>
              </div>

              <div>
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <div class="d-flex align-items-center gap-2">
                    <div class="eco-icon-tile tile-purple" style="width: 32px; height: 32px;">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      </svg>
                    </div>
                    <span class="fw-semibold text-dark small">Others</span>
                  </div>
                  <span class="fw-bold text-dark small"><?php echo $otherPoints; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: <?php echo $otherPct; ?>%; background-color: #6f588c;"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="eco-card p-4">
          <h5 class="fw-bold text-dark mb-3">EcoPoints History</h5>
          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Material</th>
                  <th>Quantity</th>
                  <th class="text-end">Points</th>
                </tr>
              </thead>
              <tbody>
                <?php if (empty($userTransactions)): ?>
                  <tr>
                    <td colspan="4" class="text-center text-muted py-4">No points history yet.</td>
                  </tr>
                <?php else: ?>
                  <?php foreach ($userTransactions as $row): ?>
                    <tr>
                      <td class="text-secondary small"><?php echo date('M d, Y', strtotime($row['created_at'])); ?></td>
                      <td class="fw-semibold text-dark small"><?php echo htmlspecialchars($row['material_name']); ?></td>
                      <td class="text-secondary small"><?php echo $row['quantity']; ?></td>
                      <td class="text-end fw-bold text-success small">+<?php echo $row['points_earned']; ?></td>
                    </tr>
                  <?php endforeach; ?>
                <?php endif; ?>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
