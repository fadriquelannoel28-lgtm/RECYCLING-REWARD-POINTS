<?php
require_once __DIR__ . '/config/db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$currentUser = EcoDB::getUserById($_SESSION['user_id']);
if (!$currentUser || ($currentUser['role'] ?? '') !== 'admin') {
    $_SESSION['user_role'] = 'admin';
}

$tab = $_GET['tab'] ?? 'dashboard';

$feedback = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['admin_action'] ?? '';

    if ($action === 'save_material') {
        $name = trim($_POST['mat_name'] ?? '');
        $category = trim($_POST['mat_cat'] ?? 'General');
        $points = max(1, (int)($_POST['mat_points'] ?? 1));
        $unit = trim($_POST['mat_unit'] ?? 'piece');
        $icon = trim($_POST['mat_icon'] ?? 'bottle');
        $editId = !empty($_POST['mat_id']) ? (int)$_POST['mat_id'] : null;

        if (!empty($name)) {
            EcoDB::saveMaterial($name, $category, $points, $unit, $icon, $editId);
            $feedback = 'Material point value updated successfully!';
        }
    } elseif ($action === 'save_reward') {
        $title = trim($_POST['rew_title'] ?? '');
        $category = trim($_POST['rew_category'] ?? 'Discounts');
        $points = max(1, (int)($_POST['rew_points'] ?? 100));
        $stock = max(0, (int)($_POST['rew_stock'] ?? 50));
        $partner = trim($_POST['rew_partner'] ?? '');
        $icon = trim($_POST['rew_icon'] ?? 'tag');
        $editId = !empty($_POST['rew_id']) ? (int)$_POST['rew_id'] : null;

        if (!empty($title)) {
            EcoDB::saveReward($title, $category, $points, $stock, $partner, $icon, $editId);
            $feedback = 'Reward item saved successfully!';
        }
    } elseif ($action === 'staff_deposit') {
        $resId = (int)($_POST['resident_id'] ?? 0);
        $matId = (int)($_POST['mat_id'] ?? 0);
        $qty = max(1, (int)($_POST['qty'] ?? 1));
        $res = EcoDB::getUserById($resId);
        $mat = EcoDB::getMaterialById($matId);
        if ($res && $mat) {
            $pts = $qty * (int)$mat['points_per_unit'];
            $rcp = EcoDB::recordTransaction($res['id'], $mat['id'], $mat['name'], $qty, $pts);
            $feedback = "Walk-in deposit recorded for " . htmlspecialchars($res['full_name']) . "! +" . $pts . " EcoPoints credited (Receipt: $rcp).";
        }
    }
}

$stats = EcoDB::getSystemStats();
$allUsers = EcoDB::getUsers();
$allMaterials = EcoDB::getMaterials();
$allTransactions = EcoDB::getTransactions();
$allRewards = EcoDB::getRewards();
$allRedemptions = EcoDB::getRedemptions();

$residentsList = array_filter($allUsers, fn($u) => ($u['role'] ?? 'resident') === 'resident');

$pageTitle = 'Admin Dashboard - EcoCoins';
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?php echo $pageTitle; ?></title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-eco-page">

<div class="container-fluid p-0">
  <div class="row g-0">
    <div class="col-lg-3 col-xl-2 admin-sidebar p-4 d-flex flex-column justify-content-between">
      <div>
        <a href="index.php" class="text-decoration-none d-flex align-items-center gap-2 mb-4 text-white">
          <span class="eco-brand-badge bg-white text-success">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0d462b" stroke-width="2.4">
              <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
              <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
            </svg>
          </span>
          <span class="fs-4 fw-bold">EcoCoins</span>
        </a>

        <div class="text-uppercase small fw-bold mb-3" style="color: #6ee7b7; letter-spacing: 1px; font-size: 0.75rem;">Administrator</div>

        <nav class="nav flex-column mb-4">
          <a href="admin.php?tab=dashboard" class="admin-sidebar-link <?php echo $tab === 'dashboard' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <span>Dashboard</span>
          </a>

          <a href="admin.php?tab=residents" class="admin-sidebar-link <?php echo $tab === 'residents' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span>Residents</span>
          </a>

          <a href="admin.php?tab=monitoring" class="admin-sidebar-link <?php echo $tab === 'monitoring' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
              <line x1="8" y1="21" x2="16" y2="21"></line>
              <line x1="12" y1="17" x2="12" y2="21"></line>
            </svg>
            <span>Recycling Monitoring</span>
          </a>

          <a href="admin.php?tab=materials" class="admin-sidebar-link <?php echo $tab === 'materials' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
            </svg>
            <span>Materials</span>
          </a>

          <a href="admin.php?tab=rewards" class="admin-sidebar-link <?php echo $tab === 'rewards' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 12 20 22 4 22 4 12"></polyline>
              <rect x="2" y="7" width="20" height="5"></rect>
              <line x1="12" y1="22" x2="12" y2="7"></line>
            </svg>
            <span>Rewards</span>
          </a>

          <a href="admin.php?tab=reports" class="admin-sidebar-link <?php echo $tab === 'reports' ? 'active' : ''; ?>">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            <span>Reports</span>
          </a>
        </nav>
      </div>

      <div>
        <a href="logout.php" class="admin-sidebar-link text-white-50">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          <span>Log out</span>
        </a>
      </div>
    </div>

    <div class="col-lg-9 col-xl-10 p-4 p-lg-5">
      <?php if (!empty($feedback)): ?>
        <div class="alert alert-success alert-dismissible fade show rounded-4" role="alert">
          <?php echo htmlspecialchars($feedback); ?>
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      <?php endif; ?>

      <?php if ($tab === 'dashboard'): ?>
        <div class="mb-4">
          <h2 class="fw-bold text-dark mb-1">Admin Dashboard</h2>
          <p class="text-secondary">Monitor recycling activity across the barangay.</p>
        </div>

        <div class="row g-4 mb-4">
          <div class="col-sm-6 col-xl-3">
            <div class="eco-card p-4">
              <span class="text-secondary small fw-semibold d-block mb-1">Registered Residents</span>
              <h2 class="fw-extrabold text-dark mb-0"><?php echo count($residentsList); ?></h2>
            </div>
          </div>

          <div class="col-sm-6 col-xl-3">
            <div class="eco-card p-4">
              <span class="text-secondary small fw-semibold d-block mb-1">Today's Collections</span>
              <h2 class="fw-extrabold text-dark mb-0"><?php echo $stats['today_items']; ?></h2>
            </div>
          </div>

          <div class="col-sm-6 col-xl-3">
            <div class="eco-card p-4">
              <span class="text-secondary small fw-semibold d-block mb-1">Total EcoPoints Issued</span>
              <h2 class="fw-extrabold text-dark mb-0"><?php echo number_format($stats['total_points_issued']); ?></h2>
            </div>
          </div>

          <div class="col-sm-6 col-xl-3">
            <div class="p-4 rounded-4 text-white shadow-sm" style="background-color: #1b5e3c;">
              <span class="text-white-50 small fw-semibold d-block mb-1">Rewards Redeemed</span>
              <h2 class="fw-extrabold text-white mb-0"><?php echo $stats['total_redemptions']; ?></h2>
            </div>
          </div>
        </div>

        <div class="row g-4">
          <div class="col-lg-5">
            <div class="eco-card p-4 h-100">
              <h6 class="fw-bold text-dark mb-4">Recycling by Material</h6>

              <div class="mb-4">
                <div class="d-flex justify-content-between small fw-bold mb-1">
                  <span>Plastic Bottles</span>
                  <span><?php echo $stats['material_counts']['Plastic Bottles']; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: 65%; background-color: #2980b9;"></div>
                </div>
              </div>

              <div class="mb-4">
                <div class="d-flex justify-content-between small fw-bold mb-1">
                  <span>Cans</span>
                  <span><?php echo $stats['material_counts']['Cans']; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: 40%; background-color: #b8621b;"></div>
                </div>
              </div>

              <div>
                <div class="d-flex justify-content-between small fw-bold mb-1">
                  <span>Others</span>
                  <span><?php echo $stats['material_counts']['Others']; ?></span>
                </div>
                <div class="progress rounded-pill" style="height: 8px; background-color: #e5f1ea;">
                  <div class="progress-bar rounded-pill" style="width: 20%; background-color: #6f588c;"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-lg-7">
            <div class="eco-card p-4 h-100">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="fw-bold text-dark mb-0">Recent Recycling Transactions</h6>
                <a href="admin.php?tab=monitoring" class="text-success small fw-semibold text-decoration-none">View All</a>
              </div>

              <div class="table-responsive">
                <table class="table table-clean mb-0">
                  <thead>
                    <tr>
                      <th>Resident</th>
                      <th>Material</th>
                      <th>Qty</th>
                      <th>Time</th>
                      <th class="text-end">Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    <?php foreach ($stats['recent_transactions'] as $tx): ?>
                      <tr>
                        <td class="fw-bold text-dark small"><?php echo htmlspecialchars($tx['resident_name']); ?></td>
                        <td class="text-secondary small"><?php echo htmlspecialchars($tx['material_name']); ?></td>
                        <td class="text-secondary small"><?php echo $tx['quantity']; ?></td>
                        <td class="text-secondary small"><?php echo date('h:i A', strtotime($tx['created_at'])); ?></td>
                        <td class="text-end fw-bold text-success small">+<?php echo $tx['points_earned']; ?></td>
                      </tr>
                    <?php endforeach; ?>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

      <?php elseif ($tab === 'residents'): ?>
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 class="fw-bold text-dark mb-1">Resident Accounts</h2>
            <p class="text-secondary">View and manage barangay registered residents and QR codes.</p>
          </div>
        </div>

        <div class="eco-card p-4">
          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>QR Code</th>
                  <th>Points Balance</th>
                  <th>Registered</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($residentsList as $res): ?>
                  <tr>
                    <td class="text-muted small">#<?php echo $res['id']; ?></td>
                    <td class="fw-bold text-dark small"><?php echo htmlspecialchars($res['full_name']); ?></td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($res['email']); ?></td>
                    <td><span class="badge bg-light text-dark font-monospace border"><?php echo htmlspecialchars($res['qr_code']); ?></span></td>
                    <td class="fw-bold text-success small"><?php echo number_format($res['points']); ?> pts</td>
                    <td class="text-secondary small"><?php echo date('M d, Y', strtotime($res['created_at'])); ?></td>
                  </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
        </div>

      <?php elseif ($tab === 'monitoring'): ?>
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 class="fw-bold text-dark mb-1">Recycling Monitoring</h2>
            <p class="text-secondary">Full log of all deposits recorded by the automated collection stations.</p>
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-outline-success rounded-pill px-4" data-bs-toggle="modal" data-bs-target="#staffDepositModal">Record Walk-in Deposit</button>
            <a href="station-simulator.php" class="btn btn-eco px-4">Open Station Simulator</a>
          </div>
        </div>

        <div class="eco-card p-4">
          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Receipt #</th>
                  <th>Date & Time</th>
                  <th>Resident</th>
                  <th>Material</th>
                  <th>Quantity</th>
                  <th class="text-end">Points Earned</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($allTransactions as $t): ?>
                  <tr>
                    <td class="font-monospace small text-muted"><?php echo htmlspecialchars($t['receipt_no']); ?></td>
                    <td class="text-secondary small"><?php echo date('M d, Y · h:i A', strtotime($t['created_at'])); ?></td>
                    <td class="fw-bold text-dark small"><?php echo htmlspecialchars($t['resident_name'] ?? 'Resident'); ?></td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($t['material_name']); ?></td>
                    <td class="text-secondary small"><?php echo $t['quantity']; ?></td>
                    <td class="text-end fw-bold text-success small">+<?php echo $t['points_earned']; ?> pts</td>
                  </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
        </div>

      <?php elseif ($tab === 'materials'): ?>
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 class="fw-bold text-dark mb-1">Recyclable Materials & Point Values</h2>
            <p class="text-secondary">Configure materials accepted by the collection station and their point values.</p>
          </div>
          <button class="btn btn-eco px-4" data-bs-toggle="modal" data-bs-target="#materialModal">Add Material</button>
        </div>

        <div class="eco-card p-4">
          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Material Name</th>
                  <th>Category</th>
                  <th>Point Value</th>
                  <th>Measurement Unit</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($allMaterials as $m): ?>
                  <tr>
                    <td class="fw-bold text-dark small"><?php echo htmlspecialchars($m['name']); ?></td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($m['category']); ?></td>
                    <td class="fw-bold text-success small"><?php echo $m['points_per_unit']; ?> pts / <?php echo $m['unit']; ?></td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($m['unit']); ?></td>
                    <td><span class="badge bg-success-subtle text-success rounded-pill px-3 py-1">Active</span></td>
                  </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
        </div>

      <?php elseif ($tab === 'rewards'): ?>
        <div class="d-flex justify-content-between align-items-center mb-4">
          <div>
            <h2 class="fw-bold text-dark mb-1">Rewards Management</h2>
            <p class="text-secondary">Manage community partner vouchers, merchandise, and point requirements.</p>
          </div>
          <button class="btn btn-eco px-4" data-bs-toggle="modal" data-bs-target="#rewardModal">Add Reward</button>
        </div>

        <div class="eco-card p-4">
          <div class="table-responsive">
            <table class="table table-clean mb-0">
              <thead>
                <tr>
                  <th>Reward Title</th>
                  <th>Category</th>
                  <th>Points Required</th>
                  <th>Partner</th>
                  <th>Stock Available</th>
                </tr>
              </thead>
              <tbody>
                <?php foreach ($allRewards as $rw): ?>
                  <tr>
                    <td class="fw-bold text-dark small"><?php echo htmlspecialchars($rw['title']); ?></td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($rw['category']); ?></td>
                    <td class="fw-bold text-success small"><?php echo number_format($rw['points_required']); ?> pts</td>
                    <td class="text-secondary small"><?php echo htmlspecialchars($rw['partner_name']); ?></td>
                    <td class="text-secondary small"><?php echo $rw['stock']; ?> units</td>
                  </tr>
                <?php endforeach; ?>
              </tbody>
            </table>
          </div>
        </div>

      <?php elseif ($tab === 'reports'): ?>
        <div class="mb-4">
          <h2 class="fw-bold text-dark mb-1">Barangay Recycling Reports</h2>
          <p class="text-secondary">Export summaries for barangay council decision-making and environmental programs.</p>
        </div>

        <div class="row g-4">
          <div class="col-md-6">
            <div class="eco-card p-4">
              <h5 class="fw-bold text-dark mb-3">Overall Impact Report</h5>
              <p class="text-secondary small">Comprehensive summary of waste diverted from landfills and community participation rate.</p>
              <ul class="list-group list-group-flush mb-4">
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Registered Residents:</span>
                  <span class="fw-bold"><?php echo count($residentsList); ?></span>
                </li>
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Total Deposits Recorded:</span>
                  <span class="fw-bold"><?php echo count($allTransactions); ?></span>
                </li>
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Total EcoPoints Distributed:</span>
                  <span class="fw-bold text-success"><?php echo number_format($stats['total_points_issued']); ?> pts</span>
                </li>
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Total Rewards Claimed:</span>
                  <span class="fw-bold"><?php echo count($allRedemptions); ?></span>
                </li>
              </ul>
              <button class="btn btn-eco-outline w-100" onclick="window.print();">Print / Export PDF</button>
            </div>
          </div>

          <div class="col-md-6">
            <div class="eco-card p-4">
              <h5 class="fw-bold text-dark mb-3">Material Volume Summary</h5>
              <p class="text-secondary small">Breakdown of recyclable collection counts across all collection points.</p>
              <ul class="list-group list-group-flush mb-4">
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Plastic Bottles:</span>
                  <span class="fw-bold"><?php echo $stats['material_counts']['Plastic Bottles']; ?> pcs</span>
                </li>
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Aluminum Cans:</span>
                  <span class="fw-bold"><?php echo $stats['material_counts']['Cans']; ?> pcs</span>
                </li>
                <li class="list-group-item px-0 d-flex justify-content-between">
                  <span>Other Recyclables:</span>
                  <span class="fw-bold"><?php echo $stats['material_counts']['Others']; ?> pcs/kg</span>
                </li>
              </ul>
              <button class="btn btn-eco-outline w-100" onclick="window.print();">Print / Export PDF</button>
            </div>
          </div>
        </div>
      <?php endif; ?>
    </div>
  </div>
</div>

<div class="modal fade" id="materialModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content rounded-4 border-0">
      <div class="modal-header border-0 pb-0">
        <h5 class="modal-title fw-bold">Configure Material Point Value</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form action="admin.php?tab=materials" method="POST">
        <input type="hidden" name="admin_action" value="save_material">
        <div class="modal-body py-3">
          <div class="mb-3">
            <label class="form-label small fw-bold">Material Name</label>
            <input type="text" name="mat_name" class="form-control rounded-3" placeholder="e.g. White Paper" required>
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold">Category</label>
            <input type="text" name="mat_cat" class="form-control rounded-3" placeholder="e.g. Paper" required>
          </div>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label small fw-bold">Points per Unit</label>
              <input type="number" name="mat_points" class="form-control rounded-3" value="5" min="1" required>
            </div>
            <div class="col-6">
              <label class="form-label small fw-bold">Unit</label>
              <input type="text" name="mat_unit" class="form-control rounded-3" value="piece" required>
            </div>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-eco px-4">Save Material</button>
        </div>
      </form>
    </div>
  </div>
</div>

<div class="modal fade" id="rewardModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content rounded-4 border-0">
      <div class="modal-header border-0 pb-0">
        <h5 class="modal-title fw-bold">Add Community Reward</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form action="admin.php?tab=rewards" method="POST">
        <input type="hidden" name="admin_action" value="save_reward">
        <div class="modal-body py-3">
          <div class="mb-3">
            <label class="form-label small fw-bold">Reward Title</label>
            <input type="text" name="rew_title" class="form-control rounded-3" placeholder="e.g. 20% Off Coffee" required>
          </div>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label small fw-bold">Category</label>
              <select name="rew_category" class="form-select rounded-3">
                <option value="Discounts">Discounts</option>
                <option value="Merchandise">Merchandise</option>
                <option value="Partners">Partners</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label small fw-bold">Points Required</label>
              <input type="number" name="rew_points" class="form-control rounded-3" value="500" min="10" required>
            </div>
          </div>
          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label small fw-bold">Stock Available</label>
              <input type="number" name="rew_stock" class="form-control rounded-3" value="50" min="1" required>
            </div>
            <div class="col-6">
              <label class="form-label small fw-bold">Partner Name</label>
              <input type="text" name="rew_partner" class="form-control rounded-3" placeholder="e.g. SM Lipa">
            </div>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-eco px-4">Save Reward</button>
        </div>
      </form>
    </div>
  </div>
</div>

<div class="modal fade" id="staffDepositModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content rounded-4 border-0">
      <div class="modal-header border-0 pb-0">
        <h5 class="modal-title fw-bold">Record Walk-in Recycling Deposit</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <form action="admin.php?tab=monitoring" method="POST">
        <input type="hidden" name="admin_action" value="staff_deposit">
        <div class="modal-body py-3">
          <div class="mb-3">
            <label class="form-label small fw-bold">Select Resident</label>
            <select name="resident_id" class="form-select rounded-3" required>
              <?php foreach ($residentsList as $r): ?>
                <option value="<?php echo $r['id']; ?>"><?php echo htmlspecialchars($r['full_name']); ?> (<?php echo $r['qr_code']; ?>)</option>
              <?php endforeach; ?>
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold">Recyclable Material</label>
            <select name="mat_id" class="form-select rounded-3" required>
              <?php foreach ($allMaterials as $m): ?>
                <option value="<?php echo $m['id']; ?>"><?php echo htmlspecialchars($m['name']); ?> (+<?php echo $m['points_per_unit']; ?> pts/<?php echo $m['unit']; ?>)</option>
              <?php endforeach; ?>
            </select>
          </div>
          <div class="mb-3">
            <label class="form-label small fw-bold">Quantity / Units</label>
            <input type="number" name="qty" class="form-control rounded-3" value="1" min="1" max="500" required>
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light rounded-pill px-4" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-eco px-4">Submit Deposit</button>
        </div>
      </form>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="assets/js/app.js"></script>
</body>
</html>
