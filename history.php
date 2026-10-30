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

$transactions = EcoDB::getTransactions($user['id']);

$pageTitle = 'Recycling History - EcoCoins';
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
          <h2 class="fw-bold text-dark mb-1">Recycling History</h2>
          <p class="text-secondary">Track your past recycling activities.</p>
        </div>

        <div class="eco-card p-4 p-lg-5">
          <div class="d-flex flex-wrap gap-2 mb-4 filter-group">
            <button class="eco-pill filter-pill active" data-filter="all">All</button>
            <button class="eco-pill filter-pill" data-filter="plastic">Plastic Bottle</button>
            <button class="eco-pill filter-pill" data-filter="can">Can</button>
            <button class="eco-pill filter-pill" data-filter="others">Others</button>
          </div>

          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Material</th>
                  <th>Quantity</th>
                  <th class="text-end">Points</th>
                </tr>
              </thead>
              <tbody>
                <?php if (empty($transactions)): ?>
                  <tr>
                    <td colspan="4" class="text-center text-muted py-4">No recycling history found.</td>
                  </tr>
                <?php else: ?>
                  <?php foreach ($transactions as $t): ?>
                    <?php 
                      $matName = strtolower($t['material_name']);
                      $cat = 'others';
                      $tile = 'tile-purple';
                      if (strpos($matName, 'bottle') !== false || strpos($matName, 'plastic') !== false) {
                          $cat = 'plastic';
                          $tile = 'tile-blue';
                      } elseif (strpos($matName, 'can') !== false) {
                          $cat = 'can';
                          $tile = 'tile-orange';
                      }
                    ?>
                    <tr class="filterable-item" data-category="<?php echo $cat; ?>">
                      <td class="text-secondary small">
                        <?php echo date('M d, Y · h:i A', strtotime($t['created_at'])); ?>
                      </td>
                      <td>
                        <div class="d-flex align-items-center gap-3">
                          <div class="eco-icon-tile <?php echo $tile; ?>">
                            <?php if ($cat === 'can'): ?>
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="5" y="4" width="14" height="16" rx="3"/>
                                <ellipse cx="12" cy="7" rx="5" ry="2"/>
                              </svg>
                            <?php elseif ($cat === 'plastic'): ?>
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 2h4v3h-4z"/>
                                <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
                              </svg>
                            <?php else: ?>
                              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                              </svg>
                            <?php endif; ?>
                          </div>
                          <span class="fw-bold text-dark small"><?php echo htmlspecialchars($t['material_name']); ?></span>
                        </div>
                      </td>
                      <td class="text-secondary small"><?php echo $t['quantity']; ?></td>
                      <td class="text-end fw-bold text-success small">+<?php echo $t['points_earned']; ?></td>
                    </tr>
                  <?php endforeach; ?>
                <?php endif; ?>
              </tbody>
            </table>
          </div>

          <div class="d-flex flex-column flex-sm-row justify-content-between align-items-center gap-3 pt-4 mt-2 border-top">
            <span class="text-secondary small">Showing <?php echo count($transactions); ?> transactions</span>
            <div class="d-flex gap-2">
              <button class="btn btn-outline-secondary btn-sm rounded-circle p-0 d-flex align-items-center justify-content-center" style="width: 36px; height: 36px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
              </button>
              <button class="btn btn-outline-secondary btn-sm rounded-circle p-0 d-flex align-items-center justify-content-center" style="width: 36px; height: 36px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
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
