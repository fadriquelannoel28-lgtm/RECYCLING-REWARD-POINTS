<?php
$currentScript = basename($_SERVER['PHP_SELF']);
?>
<div class="eco-card p-3 mb-4">
  <div class="nav flex-column">
    <a href="dashboard.php" class="eco-sidebar-link <?php echo ($currentScript === 'dashboard.php') ? 'active' : ''; ?>">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
        <line x1="8" y1="21" x2="16" y2="21"></line>
        <line x1="12" y1="17" x2="12" y2="21"></line>
      </svg>
      <span>Dashboard</span>
    </a>

    <a href="ecopoints.php" class="eco-sidebar-link <?php echo ($currentScript === 'ecopoints.php') ? 'active' : ''; ?>">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 6v12M15 9.5a2.5 2.5 0 0 0-5 0c0 4 5 2 5 6a2.5 2.5 0 0 1-5 0"></path>
      </svg>
      <span>My EcoPoints</span>
    </a>

    <a href="history.php" class="eco-sidebar-link <?php echo ($currentScript === 'history.php') ? 'active' : ''; ?>">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
      <span>Recycling History</span>
    </a>

    <a href="rewards.php" class="eco-sidebar-link <?php echo ($currentScript === 'rewards.php') ? 'active' : ''; ?>">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="20 12 20 22 4 22 4 12"></polyline>
        <rect x="2" y="7" width="20" height="5"></rect>
        <line x1="12" y1="22" x2="12" y2="7"></line>
        <path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"></path>
        <path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"></path>
      </svg>
      <span>Rewards</span>
    </a>

    <a href="station-simulator.php" class="eco-sidebar-link <?php echo ($currentScript === 'station-simulator.php') ? 'active' : ''; ?>">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="7" height="7"></rect>
        <rect x="14" y="3" width="7" height="7"></rect>
        <rect x="14" y="14" width="7" height="7"></rect>
        <rect x="3" y="14" width="7" height="7"></rect>
      </svg>
      <span>Collection Station</span>
    </a>

    <div class="border-top my-3"></div>

    <a href="logout.php" class="eco-sidebar-link text-danger">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
        <polyline points="16 17 21 12 16 7"></polyline>
        <line x1="21" y1="12" x2="9" y2="12"></line>
      </svg>
      <span>Log out</span>
    </a>
  </div>
</div>
