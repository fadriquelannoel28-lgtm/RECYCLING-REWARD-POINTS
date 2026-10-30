<?php
require_once __DIR__ . '/config/db.php';
$pageTitle = 'EcoCoins - Recycle Today, Earn EcoPoints!';
require_once __DIR__ . '/includes/header.php';
require_once __DIR__ . '/includes/navbar.php';
?>

<main>
  <section class="py-5">
    <div class="container py-lg-4">
      <div class="row align-items-center g-5">
        <div class="col-lg-6">
          <span class="text-success fw-bold text-uppercase fs-6 mb-2 d-block">Small Actions. Big Impact.</span>
          <h1 class="display-4 fw-bold text-dark lh-sm mb-3">
            Recycle Today,<br>
            Earn <span class="text-success">EcoPoints!</span>
          </h1>
          <p class="text-secondary fs-5 mb-4 pe-lg-4">
            Turn your recyclable materials into rewards. Scan your QR code at the EcoCoins station and be part of a cleaner, greener barangay.
          </p>
          <div class="d-flex flex-wrap gap-3">
            <?php if ($currentUser): ?>
              <a href="dashboard.php" class="btn btn-eco px-4 py-2 fs-6">Go to Dashboard &rarr;</a>
              <a href="station-simulator.php" class="btn btn-eco-outline px-4 py-2 fs-6">Deposit Station</a>
            <?php else: ?>
              <a href="register.php" class="btn btn-eco px-4 py-2 fs-6">Get Started &rarr;</a>
              <a href="how-it-works.php" class="btn btn-eco-outline px-4 py-2 fs-6">Learn more</a>
            <?php endif; ?>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="position-relative d-flex justify-content-center align-items-center py-4">
            <div class="position-absolute rounded-circle" style="width: 380px; height: 380px; background-color: #d8efe0; z-index: 1;"></div>
            
            <div class="station-machine-box z-2">
              <div class="station-screen shadow-sm">
                <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="#6ee7b7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/>
                  <path d="M11 19h8.2a1.8 1.8 0 0 0 1.57-2.665L18.8 13"/>
                  <path d="m16 6-3.8 6.5"/>
                  <path d="M12 2v4"/>
                  <path d="m5 10 3-4"/>
                </svg>
              </div>
              <div class="station-slot"></div>
            </div>

            <div class="position-absolute end-0 top-0 z-3 p-3 bg-dark-subtle text-white rounded-4 shadow" style="background-color: #0d462b !important; max-width: 170px;">
              <div class="fw-bold mb-1 fs-6">Recycle</div>
              <div class="small text-light">&bull; Earn Points</div>
              <div class="small text-light">&bull; Get Rewards</div>
            </div>

            <div class="position-absolute start-0 top-0 z-2 bg-white p-2 rounded-4 shadow-sm border border-eco">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#2980b9" stroke-width="2">
                <path d="M10 2h4v3h-4z"/>
                <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
              </svg>
            </div>

            <div class="position-absolute end-0 bottom-0 z-2 bg-white p-2 rounded-4 shadow-sm border border-eco">
              <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#b8621b" stroke-width="2">
                <rect x="5" y="4" width="14" height="16" rx="3"/>
                <ellipse cx="12" cy="7" rx="5" ry="2"/>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4 mt-5">
        <div class="col-12">
          <div class="eco-card p-4 p-lg-5">
            <div class="row g-4">
              <div class="col-md-6 col-lg-3 d-flex align-items-start gap-3">
                <div class="eco-icon-tile tile-green">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  </svg>
                </div>
                <div>
                  <h6 class="fw-bold text-dark mb-1">Reduce Waste</h6>
                  <p class="text-secondary small mb-0">Keep recyclables out of regular trash and help keep the barangay clean.</p>
                </div>
              </div>

              <div class="col-md-6 col-lg-3 d-flex align-items-start gap-3">
                <div class="eco-icon-tile tile-green">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="9"/>
                    <path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"/>
                    <path d="M12 6v12"/>
                  </svg>
                </div>
                <div>
                  <h6 class="fw-bold text-dark mb-1">Earn EcoPoints</h6>
                  <p class="text-secondary small mb-0">Points are calculated automatically for every recyclable you deposit.</p>
                </div>
              </div>

              <div class="col-md-6 col-lg-3 d-flex align-items-start gap-3">
                <div class="eco-icon-tile tile-green">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20 12 20 22 4 22 4 12"/>
                    <rect x="2" y="7" width="20" height="5"/>
                    <line x1="12" y1="22" x2="12" y2="7"/>
                  </svg>
                </div>
                <div>
                  <h6 class="fw-bold text-dark mb-1">Get Rewards</h6>
                  <p class="text-secondary small mb-0">Redeem your points for vouchers, discounts and merchandise.</p>
                </div>
              </div>

              <div class="col-md-6 col-lg-3 d-flex align-items-start gap-3">
                <div class="eco-icon-tile tile-green">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                </div>
                <div>
                  <h6 class="fw-bold text-dark mb-1">Support the Community</h6>
                  <p class="text-secondary small mb-0">A barangay-run program that rewards residents who recycle.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</main>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
