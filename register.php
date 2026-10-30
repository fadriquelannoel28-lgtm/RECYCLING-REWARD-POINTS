<?php
require_once __DIR__ . '/config/db.php';

$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $fullName = trim($_POST['full_name'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $password = $_POST['password'] ?? '';
    $confirmPassword = $_POST['confirm_password'] ?? '';
    $terms = isset($_POST['terms']);

    if (empty($fullName) || empty($email) || empty($password)) {
        $error = 'Please fill in all required fields.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Please provide a valid email address.';
    } elseif ($password !== $confirmPassword) {
        $error = 'Passwords do not match.';
    } elseif (strlen($password) < 6) {
        $error = 'Password must be at least 6 characters.';
    } elseif (!$terms) {
        $error = 'You must agree to the Terms & Conditions.';
    } else {
        $existing = EcoDB::getUserByEmail($email);
        if ($existing) {
            $error = 'An account with this email address already exists.';
        } else {
            $newUser = EcoDB::createUser($fullName, $email, $password, 'resident');
            if ($newUser) {
                $_SESSION['user_id'] = $newUser['id'];
                $_SESSION['user_role'] = $newUser['role'];
                $_SESSION['user_name'] = $newUser['full_name'];
                header('Location: dashboard.php');
                exit;
            } else {
                $error = 'Failed to create account. Please try again.';
            }
        }
    }
}

$pageTitle = 'Sign Up - EcoCoins';
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
          <h1 class="display-4 fw-bold text-dark lh-sm mb-4">
            Join us and Start<br>
            <span class="text-success">earning rewards</span><br>
            for recycling!
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
            <h3 class="fw-bold text-dark mb-1">Create an Account</h3>
          </div>

          <?php if (!empty($error)): ?>
            <div class="alert alert-danger py-2 small rounded-3"><?php echo htmlspecialchars($error); ?></div>
          <?php endif; ?>

          <form action="register.php" method="POST">
            <div class="mb-3">
              <label class="form-label small fw-semibold text-secondary mb-1">Full Name</label>
              <input type="text" name="full_name" class="form-control rounded-3" placeholder="Your Full Name" value="<?php echo htmlspecialchars($_POST['full_name'] ?? ''); ?>" required>
            </div>

            <div class="mb-3">
              <label class="form-label small fw-semibold text-secondary mb-1">Email Address</label>
              <div class="input-group">
                <input type="email" name="email" class="form-control rounded-start-3" placeholder="you@example.com" value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>" required>
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
                <input type="password" name="password" id="regPass" class="form-control rounded-start-3" placeholder="Create a password" required>
                <button type="button" class="btn btn-outline-secondary border-start-0 rounded-end-3 toggle-password" data-target="regPass">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label small fw-semibold text-secondary mb-1">Confirm Password</label>
              <div class="input-group">
                <input type="password" name="confirm_password" id="regConfirmPass" class="form-control rounded-start-3" placeholder="Re-enter your password" required>
                <button type="button" class="btn btn-outline-secondary border-start-0 rounded-end-3 toggle-password" data-target="regConfirmPass">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                </button>
              </div>
            </div>

            <div class="form-check mb-4">
              <input class="form-check-input" type="checkbox" id="termsCheck" name="terms" required>
              <label class="form-check-label small text-secondary" for="termsCheck">
                I agree to the <a href="#" class="text-success text-decoration-none fw-semibold">Terms & Conditions</a>
              </label>
            </div>

            <button type="submit" class="btn btn-eco w-100 py-2 fs-6 mb-3">Create Account</button>

            <div class="text-center small text-secondary">
              Already have an account? <a href="login.php" class="text-success fw-bold text-decoration-none">Log In</a>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="assets/js/app.js"></script>
</body>
</html>
