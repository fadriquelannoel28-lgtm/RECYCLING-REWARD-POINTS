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

  const paginatedTables = document.querySelectorAll('table[data-paginate="true"]');
  paginatedTables.forEach(function (table) {
    let currentPage = 1;
    const pageSize = parseInt(table.dataset.pageSize || '15', 10);
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const tableId = table.id;
    const cardParent = table.closest('.card') || table.parentElement;
    const searchInput = (tableId ? document.querySelector(`.table-search-input[data-target="#${tableId}"]`) : null) || cardParent.querySelector('.table-search-input');
    const filterContainer = (tableId ? document.querySelector(`.filter-container[data-target="#${tableId}"]`) : null) || cardParent.querySelector('.filter-container');
    const paginationContainer = (tableId ? document.querySelector(`.pagination-container[data-target="#${tableId}"]`) : null) || cardParent.querySelector('.pagination-container');

    function getAllRows() {
      const explicit = Array.from(tbody.querySelectorAll('tr.table-row-item'));
      if (explicit.length > 0) return explicit;
      return Array.from(tbody.querySelectorAll('tr:not(.table-empty-search-row)'));
    }

    function getFilteredRows() {
      const rows = getAllRows();
      let activeFilter = 'all';
      if (filterContainer) {
        const activeBtn = filterContainer.querySelector('.filter-btn.active');
        if (activeBtn) activeFilter = activeBtn.dataset.filter || 'all';
      }
      const query = (searchInput ? searchInput.value : '').toLowerCase().trim();

      return rows.filter(function (row) {
        const category = row.dataset.category || '';
        const matchesFilter = (activeFilter === 'all' || category === activeFilter);
        if (!matchesFilter) return false;

        if (!query) return true;
        const searchTarget = (row.dataset.search || row.textContent).toLowerCase();
        return searchTarget.includes(query);
      });
    }

    function render() {
      const allRows = getAllRows();
      const matchingRows = getFilteredRows();
      const totalMatching = matchingRows.length;
      const totalPages = Math.max(1, Math.ceil(totalMatching / pageSize));

      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      allRows.forEach(function (row) {
        row.style.display = 'none';
      });

      const startIndex = (currentPage - 1) * pageSize;
      const endIndex = Math.min(startIndex + pageSize, totalMatching);

      for (let i = startIndex; i < endIndex; i++) {
        matchingRows[i].style.display = '';
      }

      let emptyRow = tbody.querySelector('.table-empty-search-row');
      if (totalMatching === 0 && allRows.length > 0) {
        if (!emptyRow) {
          const colSpan = table.querySelectorAll('thead th').length || 5;
          emptyRow = document.createElement('tr');
          emptyRow.className = 'table-empty-search-row';
          emptyRow.innerHTML = `<td colspan="${colSpan}" class="text-center py-4 text-muted">No matching records found.</td>`;
          tbody.appendChild(emptyRow);
        }
        emptyRow.style.display = '';
      } else if (emptyRow) {
        emptyRow.style.display = 'none';
      }

      if (paginationContainer) {
        const info = paginationContainer.querySelector('.pagination-info');
        const prevBtn = paginationContainer.querySelector('.pagination-prev');
        const nextBtn = paginationContainer.querySelector('.pagination-next');
        const pageIndicator = paginationContainer.querySelector('.pagination-page-indicator');

        if (totalMatching === 0) {
          if (info) info.textContent = 'Showing 0 of 0 entries';
          if (pageIndicator) pageIndicator.textContent = 'Page 0 of 0';
          if (prevBtn) prevBtn.disabled = true;
          if (nextBtn) nextBtn.disabled = true;
        } else {
          if (info) info.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${totalMatching} entries`;
          if (pageIndicator) pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
          if (prevBtn) prevBtn.disabled = (currentPage <= 1);
          if (nextBtn) nextBtn.disabled = (currentPage >= totalPages);
        }

        paginationContainer.style.display = (totalMatching > 0 || (searchInput && searchInput.value)) ? '' : 'none';
      }
    }

    if (searchInput) {
      searchInput.addEventListener('input', function () {
        currentPage = 1;
        render();
      });
    }

    if (filterContainer) {
      filterContainer.querySelectorAll('.filter-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          filterContainer.querySelectorAll('.filter-btn').forEach(function (b) {
            b.classList.remove('active', 'btn-success');
            b.classList.add('btn-outline-success');
          });
          this.classList.remove('btn-outline-success');
          this.classList.add('active', 'btn-success');
          currentPage = 1;
          render();
        });
      });
    }

    if (paginationContainer) {
      const prevBtn = paginationContainer.querySelector('.pagination-prev');
      const nextBtn = paginationContainer.querySelector('.pagination-next');
      if (prevBtn) {
        prevBtn.addEventListener('click', function () {
          if (currentPage > 1) {
            currentPage--;
            render();
          }
        });
      }
      if (nextBtn) {
        nextBtn.addEventListener('click', function () {
          const matching = getFilteredRows();
          const totalPages = Math.ceil(matching.length / pageSize);
          if (currentPage < totalPages) {
            currentPage++;
            render();
          }
        });
      }
    }

    render();
  });

  const standAloneFilterContainers = document.querySelectorAll('.filter-container:not([data-target])');
  standAloneFilterContainers.forEach(function (container) {
    if (container.closest('.card')?.querySelector('table[data-paginate="true"]')) return;
    container.querySelectorAll('.filter-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        container.querySelectorAll('.filter-btn').forEach(function (b) {
          b.classList.remove('active', 'btn-success');
          b.classList.add('btn-outline-success');
        });
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
  });
});
