<?php
require_once __DIR__ . '/config/db.php';

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    $password = trim($_POST['password'] ?? '');

    if (empty($email) || empty($password)) {
        $error = 'Please fill in both email and password.';
    } else {
        $user = EcoDB::getUserByEmail($email);
        if ($user && password_verify($password, $user['password'])) {
            $_SESSION['user_id'] = $user['id'];
            $_SESSION['user_role'] = $user['role'];
            $_SESSION['user_name'] = $user['full_name'];

            if ($user['role'] === 'admin') {
                header('Location: admin.php');
            } else {
                header('Location: dashboard.php');
            }
            exit;
        } else {
            $error = 'Invalid email address or password.';
        }
    }
}

$pageTitle = 'Login - EcoCoins';
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
<body class="bg-eco-page min-vh-100 d-flex flex-column justify-content-center py-4">

  <div class="container my-auto">
    <div class="row align-items-center justify-content-center g-5">
      <div class="col-lg-6 d-none d-lg-block">
        <div class="pe-lg-4">
          <span class="text-success fw-bold text-uppercase fs-6 mb-2 d-block">Small Actions. Big Impact.</span>
          <h1 class="display-4 fw-bold text-dark lh-sm mb-4">
            Recycle Today,<br>
            Earn <span class="text-success">EcoPoints!</span>
          </h1>

          <div class="position-relative d-inline-flex justify-content-center align-items-center py-3">
            <div class="rounded-circle" style="width: 320px; height: 320px; background-color: #d8efe0; position: absolute; z-index: 1;"></div>
            <div class="station-machine-box position-relative z-2">
              <div class="station-screen shadow-sm">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6ee7b7" stroke-width="2.2">
                  <path d="M7 19H4.815a1.83 1.83 0 0 1-1.57-.881 1.785 1.785 0 0 1-.004-1.784L7.196 9.5"/>
                  <path d="M11 19h8.2a1.8 1.8 0 0 0 1.57-2.665L18.8 13"/>
                  <path d="m16 6-3.8 6.5"/>
                  <path d="M12 2v4"/>
                  <path d="m5 10 3-4"/>
                </svg>
              </div>
              <div class="station-slot"></div>
            </div>

            <div class="position-absolute end-0 top-0 z-3 p-3 bg-dark-subtle text-white rounded-4 shadow" style="background-color: #0d462b !important; max-width: 150px;">
              <div class="fw-bold fs-6">Recycle</div>
              <div class="small text-light">&bull; Earn Points</div>
              <div class="small text-light">&bull; Get Rewards</div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-12 col-md-8 col-lg-5 col-xl-4">
        <div class="eco-card p-4 p-lg-5 shadow">
          <div class="text-center mb-4">
            <a href="index.php" class="text-decoration-none d-inline-flex align-items-center gap-2 mb-3">
              <span class="eco-brand-badge">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                  <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
                </svg>
              </span>
              <span class="fs-4 fw-bold text-dark">EcoCoins</span>
            </a>
            <h3 class="fw-bold text-dark mb-1">Welcome Back</h3>
            <p class="text-secondary small">Less your effort to recycling and make a difference.</p>
          </div>

          <?php if (!empty($error)): ?>
            <div class="alert alert-danger py-2 small rounded-3"><?php echo htmlspecialchars($error); ?></div>
          <?php endif; ?>

          <form action="login.php" method="POST">
            <div class="mb-3">
              <label class="form-label small fw-semibold text-secondary mb-1">Email Address</label>
              <div class="input-group">
                <input type="email" name="email" id="emailInput" class="form-control rounded-3" placeholder="user@example.com" value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>" required>
                <span class="input-group-text bg-white border-start-0 rounded-end-3 text-secondary">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                  </svg>
                </span>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label small fw-semibold text-secondary mb-1">Password</label>
              <div class="input-group">
                <input type="password" name="password" id="passwordInput" class="form-control rounded-start-3" placeholder="Enter your password" required>
                <button type="button" class="btn btn-outline-secondary border-start-0 rounded-end-3 toggle-password" data-target="passwordInput">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
            </div>

            <div class="d-flex justify-content-between align-items-center mb-4">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="rememberMe">
                <label class="form-check-label small text-secondary" for="rememberMe">Remember me</label>
              </div>
              <a href="#" class="small text-success fw-semibold text-decoration-none">Forgot Password?</a>
            </div>

            <button type="submit" class="btn btn-eco w-100 py-2 fs-6 mb-3">Log In</button>

            <div class="text-center small text-secondary">
              Don't have an account? <a href="register.php" class="text-success fw-bold text-decoration-none">Sign up</a>
            </div>
          </form>

          <div class="mt-4 pt-3 border-top text-center">
            <span class="text-muted small d-block mb-2">Quick Demo Fill:</span>
            <div class="d-flex gap-2 justify-content-center">
              <button type="button" class="btn btn-sm btn-outline-success rounded-pill" onclick="document.getElementById('emailInput').value='user@example.com';document.getElementById('passwordInput').value='user123';">Resident Demo</button>
              <button type="button" class="btn btn-sm btn-outline-dark rounded-pill" onclick="document.getElementById('emailInput').value='admin@ecocoins.ph';document.getElementById('passwordInput').value='admin123';">Admin Demo</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="assets/js/app.js"></script>
</body>
</html>
