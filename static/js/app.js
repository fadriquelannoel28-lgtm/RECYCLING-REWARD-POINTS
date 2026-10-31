document.addEventListener('DOMContentLoaded', function () {
  const toggleButtons = document.querySelectorAll('.toggle-password');
  toggleButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetInput = document.getElementById(this.dataset.target);
      if (targetInput) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          this.innerHTML = '<i class="bi bi-eye-slash"></i>';
        } else {
          targetInput.type = 'password';
          this.innerHTML = '<i class="bi bi-eye"></i>';
        }
      }
    });
  });

  const filterButtons = document.querySelectorAll('.filter-btn');
  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const parent = this.closest('.filter-container');
      if (parent) {
        parent.querySelectorAll('.filter-btn').forEach(function (b) {
          b.classList.remove('active', 'btn-success');
          b.classList.add('btn-outline-success');
        });
      }
      this.classList.remove('btn-outline-success');
      this.classList.add('active', 'btn-success');

      const category = this.dataset.filter;
      const items = document.querySelectorAll('.filter-item');
      items.forEach(function (item) {
        if (category === 'all' || item.dataset.category === category) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

  const redeemButtons = document.querySelectorAll('.btn-redeem');
  redeemButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const id = this.dataset.id;
      const title = this.dataset.title;
      const points = this.dataset.points;

      const inputId = document.getElementById('modalRewardId');
      const textTitle = document.getElementById('modalRewardTitle');
      const textPoints = document.getElementById('modalRewardPoints');

      if (inputId) inputId.value = id;
      if (textTitle) textTitle.textContent = title;
      if (textPoints) textPoints.textContent = points;
    });
  });
});
