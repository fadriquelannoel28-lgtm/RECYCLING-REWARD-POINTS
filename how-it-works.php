<?php
require_once __DIR__ . '/config/db.php';
$pageTitle = 'How It Works - EcoCoins';
require_once __DIR__ . '/includes/header.php';
require_once __DIR__ . '/includes/navbar.php';
?>

<main class="py-5">
  <div class="container py-lg-4">
    <div class="mb-5">
      <h1 class="display-5 fw-bold text-dark mb-2">How It Works</h1>
      <p class="text-secondary fs-5">It's easy! Just follow these simple steps.</p>
    </div>

    <div class="eco-card p-4 p-lg-5 mb-5">
      <div class="row g-4 text-center justify-content-center">
        <div class="col-6 col-md-4 col-lg-2">
          <div class="position-relative d-inline-block mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 76px; height: 76px; background-color: #d8efe0; color: #1b5e3c;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 2h4v3h-4z"/>
                <path d="M8 5h8v2a4 4 0 0 1 4 4v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-9a4 4 0 0 1 4-4V5z"/>
              </svg>
            </div>
            <span class="position-absolute bottom-0 end-0 badge rounded-pill bg-success fw-bold" style="background-color: #1b5e3c !important;">1</span>
          </div>
          <h6 class="fw-bold text-dark mb-1">Collect</h6>
          <p class="text-secondary small mb-0">Gather recyclable materials like plastic bottles and cans.</p>
        </div>

        <div class="col-6 col-md-4 col-lg-2">
          <div class="position-relative d-inline-block mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 76px; height: 76px; background-color: #d8efe0; color: #1b5e3c;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7"></rect>
                <rect x="14" y="3" width="7" height="7"></rect>
                <rect x="14" y="14" width="7" height="7"></rect>
                <rect x="3" y="14" width="7" height="7"></rect>
              </svg>
            </div>
            <span class="position-absolute bottom-0 end-0 badge rounded-pill bg-success fw-bold" style="background-color: #1b5e3c !important;">2</span>
          </div>
          <h6 class="fw-bold text-dark mb-1">Scan your QR</h6>
          <p class="text-secondary small mb-0">Scan your personal QR code at the collection station.</p>
        </div>

        <div class="col-6 col-md-4 col-lg-2">
          <div class="position-relative d-inline-block mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 76px; height: 76px; background-color: #d8efe0; color: #1b5e3c;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 3v12m0 0l-4-4m4 4l4-4"/>
                <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>
              </svg>
            </div>
            <span class="position-absolute bottom-0 end-0 badge rounded-pill bg-success fw-bold" style="background-color: #1b5e3c !important;">3</span>
          </div>
          <h6 class="fw-bold text-dark mb-1">Insert</h6>
          <p class="text-secondary small mb-0">Put the material into the machine. Sensors and camera identify it.</p>
        </div>

        <div class="col-6 col-md-4 col-lg-2">
          <div class="position-relative d-inline-block mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 76px; height: 76px; background-color: #d8efe0; color: #1b5e3c;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="9"/>
                <path d="M14.8 9A2 2 0 0 0 13 8h-2a2 2 0 0 0 0 4h2a2 2 0 0 1 0 4h-2a2 2 0 0 1-1.8-1"/>
                <path d="M12 6v12"/>
              </svg>
            </div>
            <span class="position-absolute bottom-0 end-0 badge rounded-pill bg-success fw-bold" style="background-color: #1b5e3c !important;">4</span>
          </div>
          <h6 class="fw-bold text-dark mb-1">Earn</h6>
          <p class="text-secondary small mb-0">EcoPoints are calculated and added to your account automatically.</p>
        </div>

        <div class="col-6 col-md-4 col-lg-2">
          <div class="position-relative d-inline-block mb-3">
            <div class="rounded-circle d-flex align-items-center justify-content-center mx-auto" style="width: 76px; height: 76px; background-color: #d8efe0; color: #1b5e3c;">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 12 20 22 4 22 4 12"/>
                <rect x="2" y="7" width="20" height="5"/>
                <line x1="12" y1="22" x2="12" y2="7"/>
              </svg>
            </div>
            <span class="position-absolute bottom-0 end-0 badge rounded-pill bg-success fw-bold" style="background-color: #1b5e3c !important;">5</span>
          </div>
          <h6 class="fw-bold text-dark mb-1">Get Rewards</h6>
          <p class="text-secondary small mb-0">Redeem your EcoPoints for rewards and discounts.</p>
        </div>
      </div>
    </div>

    <div class="eco-card p-4 p-lg-5">
      <div class="row align-items-center g-4">
        <div class="col-lg-5 text-center">
          <div class="d-inline-flex justify-content-center align-items-center position-relative py-3">
            <div class="rounded-circle" style="width: 240px; height: 240px; background-color: #d8efe0; position: absolute; z-index: 1;"></div>
            <div class="station-machine-box position-relative z-2">
              <div class="station-screen shadow-sm">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#6ee7b7" stroke-width="2.2">
                  <path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/>
                  <path d="M11 19h8.2a1.8 1.8 0 0 0 1.57-2.665L18.8 13"/>
                  <path d="m16 6-3.8 6.5"/>
                  <path d="M12 2v4"/>
                  <path d="m5 10 3-4"/>
                </svg>
              </div>
              <div class="station-slot"></div>
            </div>
          </div>
        </div>

        <div class="col-lg-7">
          <h2 class="fw-bold text-dark mb-3">The EcoCoins Station</h2>
          <p class="text-secondary fs-5 mb-4">
            An automated collection station reads your QR code, detects the recyclable you insert using sensors and camera-based recognition, and sends the record straight to your EcoCoins account. No manual logging needed.
          </p>
          <?php if ($currentUser): ?>
            <a href="station-simulator.php" class="btn btn-eco px-4 py-2">Try Station Simulator &rarr;</a>
          <?php else: ?>
            <a href="register.php" class="btn btn-eco px-4 py-2">Create an Account</a>
          <?php endif; ?>
        </div>
      </div>
    </div>
  </div>
</main>

<?php
require_once __DIR__ . '/includes/footer.php';
?>
