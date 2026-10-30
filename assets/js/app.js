document.addEventListener('DOMContentLoaded', function () {
  const togglePassBtns = document.querySelectorAll('.toggle-password');
  togglePassBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetId = this.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          this.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
        } else {
          input.type = 'password';
          this.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
        }
      }
    });
  });

  const filterPills = document.querySelectorAll('.filter-pill');
  filterPills.forEach(pill => {
    pill.addEventListener('click', function () {
      const container = this.closest('.filter-group');
      if (container) {
        container.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      }
      this.classList.add('active');

      const filterVal = this.getAttribute('data-filter');
      const targetItems = document.querySelectorAll('.filterable-item');

      targetItems.forEach(item => {
        const itemCat = item.getAttribute('data-category');
        if (filterVal === 'all' || itemCat === filterVal) {
          item.style.display = '';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

  const redeemButtons = document.querySelectorAll('.btn-redeem-action');
  redeemButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const rewardId = this.getAttribute('data-reward-id');
      const rewardTitle = this.getAttribute('data-reward-title');
      const rewardPoints = this.getAttribute('data-reward-points');
      
      const modalIdInput = document.getElementById('redeemRewardId');
      const modalTitleEl = document.getElementById('redeemRewardTitle');
      const modalPointsEl = document.getElementById('redeemRewardPoints');
      
      if (modalIdInput) modalIdInput.value = rewardId;
      if (modalTitleEl) modalTitleEl.textContent = rewardTitle;
      if (modalPointsEl) modalPointsEl.textContent = rewardPoints;
    });
  });
});
