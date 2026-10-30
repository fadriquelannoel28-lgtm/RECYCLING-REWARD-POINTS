<?php
require_once __DIR__ . '/config/db.php';

$currentUser = null;
if (isset($_SESSION['user_id'])) {
    $currentUser = EcoDB::getUserById($_SESSION['user_id']);
}

$message = '';
$messageType = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'redeem') {
    if (!$currentUser) {
        header('Location: login.php');
        exit;
    }
    $rewardId = (int)($_POST['reward_id'] ?? 0);
    $result = EcoDB::redeemReward($currentUser['id'], $rewardId);
    if ($result['success']) {
        $message = "Reward redeemed successfully! Your redemption code is: " . $result['code'];
        $messageType = 'success';
        $currentUser = EcoDB::getUserById($currentUser['id']);
    } else {
        $message = $result['message'];
        $messageType = 'danger';
    }
}

$rewards = EcoDB::getRewards();
$redemptions = $currentUser ? EcoDB::getRedemptions($currentUser['id']) : [];
$userPoints = $currentUser['points'] ?? 0;

$pageTitle = 'Rewards - EcoCoins';
require_once __DIR__ . '/includes/header.php';
require_once __DIR__ . '/includes/navbar.php';
?>

<main class="py-5">
  <div class="container py-lg-4">
    <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-4">
      <div>
        <h1 class="display-6 fw-bold text-dark mb-1">Rewards</h1>
        <p class="text-secondary fs-6 mb-0">Use your EcoPoints for exciting rewards and discounts.</p>
      </div>

      <div class="d-flex align-items-center gap-2">
        <div class="badge rounded-pill bg-success py-2 px-3 fs-6 d-flex align-items-center gap-2" style="background-color: #1b5e3c !important;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
          </svg>
          <span><?php echo number_format($userPoints); ?> EcoPoints</span>
        </div>
      </div>
    </div>

    <?php if (!empty($message)): ?>
      <div class="alert alert-<?php echo $messageType; ?> alert-dismissible fade show rounded-4" role="alert">
        <strong><?php echo $messageType === 'success' ? 'Congratulations! ' : 'Notice: '; ?></strong>
        <?php echo htmlspecialchars($message); ?>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    <?php endif; ?>

    <div class="d-flex flex-wrap gap-2 mb-4 filter-group">
      <button class="eco-pill filter-pill active" data-filter="all">All</button>
      <button class="eco-pill filter-pill" data-filter="Discounts">Discounts</button>
      <button class="eco-pill filter-pill" data-filter="Merchandise">Merchandise</button>
      <button class="eco-pill filter-pill" data-filter="Partners">Partners</button>
    </div>

    <div class="row g-4 mb-5">
      <?php foreach ($rewards as $r): ?>
        <?php
          $cost = (int)$r['points_required'];
          $canAfford = ($userPoints >= $cost);
          $needed = $cost - $userPoints;
          $cat = $r['category'];
          
          $bgColor = '#fcf0e4';
          $iconColor = '#b8621b';
          if ($cat === 'Merchandise') {
              $bgColor = '#dcf2e3';
              $iconColor = '#1b5e3c';
          } elseif ($cat === 'Partners') {
              $bgColor = '#e6eff9';
              $iconColor = '#246b9c';
          }
        ?>
        <div class="col-md-6 col-lg-4 filterable-item" data-category="<?php echo htmlspecialchars($cat); ?>">
          <div class="eco-card h-100 overflow-hidden d-flex flex-column justify-content-between">
            <div>
              <div class="reward-card-banner" style="background-color: <?php echo $bgColor; ?>; color: <?php echo $iconColor; ?>;">
                <?php if ($r['icon'] === 'bag'): ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>
                    <path d="M3 6h18"/>
                    <path d="M16 10a4 4 0 0 1-8 0"/>
                  </svg>
                <?php elseif ($r['icon'] === 'ticket'): ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>
                    <path d="M13 5v2"/>
                    <path d="M13 17v2"/>
                    <path d="M13 11v2"/>
                  </svg>
                <?php elseif ($r['icon'] === 'coffee'): ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 8h1a4 4 0 1 1 0 8h-1"/>
                    <path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z"/>
                    <line x1="6" y1="2" x2="6" y2="4"/>
                    <line x1="10" y1="2" x2="10" y2="4"/>
                    <line x1="14" y1="2" x2="14" y2="4"/>
                  </svg>
                <?php elseif ($r['icon'] === 'key'): ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="7.5" cy="15.5" r="5.5"/>
                    <path d="m21 2-9.6 9.6"/>
                    <path d="m15.5 7.5 3 3L22 7l-3-3"/>
                  </svg>
                <?php elseif ($r['icon'] === 'film'): ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect width="18" height="18" x="3" y="3" rx="2"/>
                    <path d="M7 3v18M17 3v18M3 7.5h4M3 12h18M3 16.5h4M17 7.5h4M17 16.5h4"/>
                  </svg>
                <?php else: ?>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/>
                    <circle cx="7" cy="7" r=".5" fill="currentColor"/>
                  </svg>
                <?php endif; ?>
              </div>

              <div class="p-4">
                <h5 class="fw-bold text-dark mb-1"><?php echo htmlspecialchars($r['title']); ?></h5>
                <div class="text-success fw-bold small mb-3"><?php echo number_format($r['points_required']); ?> pts</div>
                <div class="text-muted small">Partner: <?php echo htmlspecialchars($r['partner_name'] ?: 'Barangay Program'); ?></div>
              </div>
            </div>

            <div class="p-4 pt-0">
              <?php if (!$currentUser): ?>
                <a href="login.php" class="btn btn-outline-secondary w-100 rounded-pill py-2 fw-semibold">Login to Redeem</a>
              <?php elseif ($canAfford): ?>
                <button type="button" class="btn btn-eco w-100 py-2 btn-redeem-action" data-bs-toggle="modal" data-bs-target="#redeemModal" data-reward-id="<?php echo $r['id']; ?>" data-reward-title="<?php echo htmlspecialchars($r['title']); ?>" data-reward-points="<?php echo number_format($r['points_required']); ?>">
                  Redeem
                </button>
              <?php else: ?>
                <button class="btn btn-light w-100 rounded-pill py-2 fw-semibold text-secondary" disabled>
                  <?php echo number_format($needed); ?> more pts to unlock
                </button>
              <?php endif; ?>
            </div>
          </div>
        </div>
      <?php endforeach; ?>
    </div>

    <?php if ($currentUser && !empty($redemptions)): ?>
      <div class="eco-card p-4 p-lg-5">
        <h4 class="fw-bold text-dark mb-3">My Claimed Rewards</h4>
        <div class="table-responsive">
          <table class="table table-clean mb-0">
            <thead>
              <tr>
                <th>Date Claimed</th>
                <th>Reward</th>
                <th>Points Spent</th>
                <th>Redemption Voucher Code</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <?php foreach ($redemptions as $rd): ?>
                <tr>
                  <td class="text-secondary small"><?php echo date('M d, Y · h:i A', strtotime($rd['created_at'])); ?></td>
                  <td class="fw-bold text-dark small"><?php echo htmlspecialchars($rd['reward_title']); ?></td>
                  <td class="text-secondary small"><?php echo number_format($rd['points_spent']); ?> pts</td>
                  <td>
                    <span class="badge bg-light text-dark border px-3 py-2 font-monospace fs-6"><?php echo htmlspecialchars($rd['redemption_code']); ?></span>
                  </td>
                  <td>
                    <span class="badge bg-success-subtle text-success px-3 py-1 rounded-pill">Claimed</span>
                  </td>
                </tr>
              <?php endforeach; ?>
            </tbody>
          </table>
        </div>
      </div>
    <?php endif; ?>
  </div>
</main>

<div class="modal fade" id="redeemModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content rounded-4 border-0 shadow">
      <div class="modal-header border-0 pb-0">
        <h5 class="modal-title fw-bold">Confirm Redemption</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form action="rewards.php" method="POST">
        <input type="hidden" name="action" value="redeem">
        <input type="hidden" name="reward_id" id="redeemRewardId">
        <div class="modal-body py-4">
          <p class="text-secondary mb-2">Are you sure you want to redeem:</p>
          <h5 class="fw-bold text-dark mb-3" id="redeemRewardTitle">Reward Title</h5>
          <div class="p-3 rounded-3 bg-light d-flex justify-content-between align-items-center">
            <span class="text-secondary small">Required Points:</span>
            <span class="fw-bold text-success fs-5"><span id="redeemRewardPoints">0</span> pts</span>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-eco px-4">Confirm & Redeem</button>
        </div>
      </form>
    </div>
  </div>
</div>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
