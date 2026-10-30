<?php
$currentPage = basename($_SERVER['PHP_SELF']);
?>
<nav class="navbar navbar-expand-lg bg-white sticky-top py-3 border-bottom shadow-sm">
  <div class="container">
    <a class="navbar-brand d-flex align-items-center gap-2 fw-bold text-dark fs-4" href="index.php">
      <span class="eco-brand-badge">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
          <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
        </svg>
      </span>
      <span>EcoCoins</span>
    </a>

    <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#navbarMenu">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarMenu">
      <ul class="navbar-nav mx-auto my-2 my-lg-0 gap-lg-3">
        <li class="nav-item">
          <a class="nav-link <?php echo ($currentPage === 'index.php') ? 'text-success fw-bold' : 'text-secondary fw-semibold'; ?>" href="index.php">Home</a>
        </li>
        <li class="nav-item">
          <a class="nav-link <?php echo ($currentPage === 'how-it-works.php') ? 'text-success fw-bold' : 'text-secondary fw-semibold'; ?>" href="how-it-works.php">How It Works</a>
        </li>
        <li class="nav-item">
          <a class="nav-link <?php echo ($currentPage === 'ecopoints.php') ? 'text-success fw-bold' : 'text-secondary fw-semibold'; ?>" href="ecopoints.php">EcoPoints</a>
        </li>
        <li class="nav-item">
          <a class="nav-link <?php echo ($currentPage === 'rewards.php') ? 'text-success fw-bold' : 'text-secondary fw-semibold'; ?>" href="rewards.php">Rewards</a>
        </li>
        <li class="nav-item">
          <a class="nav-link text-secondary fw-semibold" href="station-simulator.php">Collection Station</a>
        </li>
      </ul>

      <div class="d-flex align-items-center gap-2 mt-3 mt-lg-0">
        <?php if ($currentUser): ?>
          <a href="#" class="btn btn-light rounded-circle p-2 d-flex align-items-center justify-content-center text-dark" style="width: 40px; height: 40px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </a>
          <div class="dropdown">
            <button class="btn btn-light rounded-pill px-3 py-1 d-flex align-items-center gap-2 dropdown-toggle border-0" type="button" data-bs-toggle="dropdown">
              <span class="rounded-circle bg-success text-white fw-bold d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                <?php echo strtoupper(substr($currentUser['full_name'] ?? 'U', 0, 1)); ?>
              </span>
              <span class="fw-semibold text-dark"><?php echo htmlspecialchars($currentUser['full_name']); ?></span>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow-sm border-0 rounded-4 mt-2">
              <?php if (($currentUser['role'] ?? '') === 'admin'): ?>
                <li><a class="dropdown-item fw-semibold text-success py-2" href="admin.php">Admin Panel</a></li>
                <li><hr class="dropdown-divider"></li>
              <?php else: ?>
                <li><a class="dropdown-item fw-semibold py-2" href="dashboard.php">Dashboard</a></li>
                <li><a class="dropdown-item fw-semibold py-2" href="ecopoints.php">My EcoPoints</a></li>
                <li><a class="dropdown-item fw-semibold py-2" href="history.php">Recycling History</a></li>
                <li><a class="dropdown-item fw-semibold py-2" href="rewards.php">Redeem Rewards</a></li>
                <li><hr class="dropdown-divider"></li>
              <?php endif; ?>
              <li><a class="dropdown-item text-danger fw-semibold py-2" href="logout.php">Log out</a></li>
            </ul>
          </div>
        <?php else: ?>
          <a href="login.php" class="btn btn-eco-outline px-4">Login</a>
          <a href="register.php" class="btn btn-eco px-4">Sign Up</a>
        <?php endif; ?>
      </div>
    </div>
  </div>
</nav>
