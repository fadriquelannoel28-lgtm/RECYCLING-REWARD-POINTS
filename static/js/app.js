if (window.history.replaceState) {
  window.history.replaceState(null, null, window.location.href);
}

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

  const bubbles = document.querySelectorAll('.eco-bubble-alert');
  bubbles.forEach(function (bubble) {
    const textSignature = bubble.innerText.replace(/\s+/g, ' ').trim().slice(0, 60);
    const storageKey = 'eco_msg_dismissed_' + encodeURIComponent(textSignature);
    const dismissedUntil = localStorage.getItem(storageKey);
    const now = Date.now();

    if (dismissedUntil && now < parseInt(dismissedUntil, 10)) {
      bubble.style.display = 'none';
      return;
    }

    const duration = 20;
    let secondsLeft = duration;

    let timerPill = bubble.querySelector('.toast-timer-pill');
    let timerVal = bubble.querySelector('.toast-timer-val');
    if (!timerPill) {
      let actionsWrap = bubble.querySelector('.toast-actions');
      if (!actionsWrap) {
        actionsWrap = document.createElement('div');
        actionsWrap.className = 'toast-actions';
        const closeBtn = bubble.querySelector('.bubble-close-btn');
        if (closeBtn && closeBtn.parentNode) {
          closeBtn.parentNode.insertBefore(actionsWrap, closeBtn);
          actionsWrap.appendChild(closeBtn);
        } else {
          bubble.appendChild(actionsWrap);
        }
      }
      timerPill = document.createElement('span');
      timerPill.className = 'toast-timer-pill';
      timerPill.innerHTML = '<i class="bi bi-clock"></i> <span class="toast-timer-val">' + secondsLeft + 's</span>';
      actionsWrap.insertBefore(timerPill, actionsWrap.firstChild);
      timerVal = timerPill.querySelector('.toast-timer-val');
    }

    let progressTrack = bubble.querySelector('.toast-progress-track');
    let progressBar = bubble.querySelector('.toast-progress-bar');
    if (!progressTrack) {
      progressTrack = document.createElement('div');
      progressTrack.className = 'toast-progress-track';
      progressBar = document.createElement('div');
      progressBar.className = 'toast-progress-bar';
      progressBar.style.width = '100%';
      progressTrack.appendChild(progressBar);
      bubble.appendChild(progressTrack);
    }

    let dismissed = false;
    let countdownInterval = null;

    function dismiss() {
      if (dismissed) return;
      dismissed = true;
      if (countdownInterval) {
        clearInterval(countdownInterval);
      }
      bubble.classList.add('toast-dismissing');
      setTimeout(function () {
        bubble.style.display = 'none';
      }, 400);
      localStorage.setItem(storageKey, (Date.now() + 20000).toString());
    }

    const closeBtn = bubble.querySelector('.bubble-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', dismiss);
    }

    countdownInterval = setInterval(function () {
      secondsLeft -= 1;
      if (secondsLeft >= 0) {
        if (timerVal) {
          timerVal.textContent = secondsLeft + 's';
        } else if (timerPill) {
          timerPill.textContent = secondsLeft + 's';
        }
        if (progressBar) {
          const pct = Math.max(0, (secondsLeft / duration) * 100);
          progressBar.style.width = pct + '%';
        }
      }
      if (secondsLeft <= 0) {
        dismiss();
      }
    }, 1000);
  });

  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    const emailGroup = document.getElementById('emailGroup');
    const emailInput = document.getElementById('emailInput');
    const emailError = document.getElementById('emailError');
    const passwordGroup = document.getElementById('passwordGroup');
    const passwordInput = document.getElementById('passwordInput');
    const passwordError = document.getElementById('passwordError');

    function clearError(group, input, errorBox) {
      if (group) group.classList.remove('has-error');
      if (input) input.classList.remove('is-invalid');
      if (errorBox) errorBox.style.display = 'none';
    }

    function showError(group, input, errorBox, message) {
      if (group) group.classList.add('has-error');
      if (input) input.classList.add('is-invalid');
      if (errorBox) {
        const textSpan = errorBox.querySelector('.msg-text') || errorBox.querySelector('span');
        if (textSpan && message) textSpan.textContent = message;
        errorBox.style.display = 'flex';
      }
    }

    if (emailInput) {
      emailInput.addEventListener('input', function () {
        clearError(emailGroup, emailInput, emailError);
      });
    }

    if (passwordInput) {
      passwordInput.addEventListener('input', function () {
        clearError(passwordGroup, passwordInput, passwordError);
      });
    }

    const demoButtons = document.querySelectorAll('.demo-shortcut-btn');
    demoButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const demoEmail = this.dataset.email || '';
        const demoPass = this.dataset.pass || '';
        if (emailInput) emailInput.value = demoEmail;
        if (passwordInput) passwordInput.value = demoPass;
        clearError(emailGroup, emailInput, emailError);
        clearError(passwordGroup, passwordInput, passwordError);
      });
    });

    loginForm.addEventListener('submit', function (e) {
      let hasErr = false;
      const emailVal = emailInput ? emailInput.value.trim() : '';
      const passVal = passwordInput ? passwordInput.value : '';

      if (!emailVal) {
        showError(emailGroup, emailInput, emailError, 'Please enter your email address.');
        if (!hasErr && emailInput) emailInput.focus();
        hasErr = true;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
        showError(emailGroup, emailInput, emailError, 'Please enter a valid email address.');
        if (!hasErr && emailInput) emailInput.focus();
        hasErr = true;
      }

      if (!passVal) {
        showError(passwordGroup, passwordInput, passwordError, 'Please enter your password.');
        if (!hasErr && passwordInput) passwordInput.focus();
        hasErr = true;
      }

      if (hasErr) {
        e.preventDefault();
      }
    });
  }

  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    const fnGroup = document.getElementById('firstNameGroup');
    const fnInput = document.getElementById('regFirstName');
    const fnError = document.getElementById('firstNameError');

    const lnGroup = document.getElementById('lastNameGroup');
    const lnInput = document.getElementById('regLastName');
    const lnError = document.getElementById('lastNameError');

    const emGroup = document.getElementById('regEmailGroup');
    const emInput = document.getElementById('regEmail');
    const emError = document.getElementById('regEmailError');

    const pwGroup = document.getElementById('regPassGroup');
    const pwInput = document.getElementById('regPass');
    const pwError = document.getElementById('regPassError');

    const cpGroup = document.getElementById('regConfirmGroup');
    const cpInput = document.getElementById('regConfirmPass');
    const cpError = document.getElementById('regConfirmError');

    const tmGroup = document.getElementById('termsGroup');
    const tmCheck = document.getElementById('termsCheck');
    const tmError = document.getElementById('termsError');

    function clearRegError(group, input, errorBox) {
      if (group) group.classList.remove('has-error');
      if (input) input.classList.remove('is-invalid');
      if (errorBox) errorBox.style.display = 'none';
    }

    function showRegError(group, input, errorBox, message) {
      if (group) group.classList.add('has-error');
      if (input) input.classList.add('is-invalid');
      if (errorBox) {
        const textSpan = errorBox.querySelector('.msg-text') || errorBox.querySelector('span');
        if (textSpan && message) textSpan.textContent = message;
        errorBox.style.display = 'flex';
      }
    }

    [
      [fnGroup, fnInput, fnError],
      [lnGroup, lnInput, lnError],
      [emGroup, emInput, emError],
      [pwGroup, pwInput, pwError],
      [cpGroup, cpInput, cpError]
    ].forEach(function (tuple) {
      if (tuple[1]) {
        tuple[1].addEventListener('input', function () {
          clearRegError(tuple[0], tuple[1], tuple[2]);
        });
      }
    });

    if (tmCheck) {
      tmCheck.addEventListener('change', function () {
        clearRegError(tmGroup, tmCheck, tmError);
      });
    }

    registerForm.addEventListener('submit', function (e) {
      let hasErr = false;
      const fn = fnInput ? fnInput.value.trim() : '';
      const ln = lnInput ? lnInput.value.trim() : '';
      const em = emInput ? emInput.value.trim() : '';
      const pw = pwInput ? pwInput.value : '';
      const cp = cpInput ? cpInput.value : '';
      const tm = tmCheck ? tmCheck.checked : false;

      if (!fn) {
        showRegError(fnGroup, fnInput, fnError, 'Please enter your first name.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      } else if (fn.length < 2) {
        showRegError(fnGroup, fnInput, fnError, 'First name must be at least 2 characters.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      } else if (/\d/.test(fn)) {
        showRegError(fnGroup, fnInput, fnError, 'First name cannot contain numbers.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      }

      if (!ln) {
        showRegError(lnGroup, lnInput, lnError, 'Please enter your last name.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      } else if (ln.length < 2) {
        showRegError(lnGroup, lnInput, lnError, 'Last name must be at least 2 characters.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      } else if (/\d/.test(ln)) {
        showRegError(lnGroup, lnInput, lnError, 'Last name cannot contain numbers.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      }

      if (!em) {
        showRegError(emGroup, emInput, emError, 'Please enter your email address.');
        if (!hasErr && emInput) emInput.focus();
        hasErr = true;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
        showRegError(emGroup, emInput, emError, 'Please enter a valid email address.');
        if (!hasErr && emInput) emInput.focus();
        hasErr = true;
      }

      if (!pw) {
        showRegError(pwGroup, pwInput, pwError, 'Please enter a password.');
        if (!hasErr && pwInput) pwInput.focus();
        hasErr = true;
      } else if (pw.length < 6) {
        showRegError(pwGroup, pwInput, pwError, 'Password must be at least 6 characters.');
        if (!hasErr && pwInput) pwInput.focus();
        hasErr = true;
      }

      if (!cp) {
        showRegError(cpGroup, cpInput, cpError, 'Please confirm your password.');
        if (!hasErr && cpInput) cpInput.focus();
        hasErr = true;
      } else if (pw !== cp) {
        showRegError(cpGroup, cpInput, cpError, 'The passwords you entered do not match.');
        if (!hasErr && cpInput) cpInput.focus();
        hasErr = true;
      }

      if (!tm) {
        showRegError(tmGroup, tmCheck, tmError, 'You must agree to the Terms and Conditions.');
        hasErr = true;
      }

      if (hasErr) {
        e.preventDefault();
      }
    });
  }

  const updateProfileForm = document.getElementById('updateProfileForm');
  if (updateProfileForm) {
    const fnGroup = document.getElementById('profileFnGroup');
    const fnInput = document.getElementById('profileFnInput');
    const fnError = document.getElementById('profileFnError');

    const lnGroup = document.getElementById('profileLnGroup');
    const lnInput = document.getElementById('profileLnInput');
    const lnError = document.getElementById('profileLnError');

    const emGroup = document.getElementById('profileEmailGroup');
    const emInput = document.getElementById('profileEmailInput');
    const emError = document.getElementById('profileEmailError');

    function clearPError(group, input, errorBox) {
      if (group) group.classList.remove('has-error');
      if (input) input.classList.remove('is-invalid');
      if (errorBox) errorBox.style.display = 'none';
    }

    function showPError(group, input, errorBox, message) {
      if (group) group.classList.add('has-error');
      if (input) input.classList.add('is-invalid');
      if (errorBox) {
        const textSpan = errorBox.querySelector('.msg-text') || errorBox.querySelector('span');
        if (textSpan && message) textSpan.textContent = message;
        errorBox.style.display = 'flex';
      }
    }

    if (fnInput) fnInput.addEventListener('input', () => clearPError(fnGroup, fnInput, fnError));
    if (lnInput) lnInput.addEventListener('input', () => clearPError(lnGroup, lnInput, lnError));
    if (emInput) emInput.addEventListener('input', () => clearPError(emGroup, emInput, emError));

    updateProfileForm.addEventListener('submit', function (e) {
      let hasErr = false;
      const fn = fnInput ? fnInput.value.trim() : '';
      const ln = lnInput ? lnInput.value.trim() : '';
      const em = emInput ? emInput.value.trim() : '';

      if (!fn) {
        showPError(fnGroup, fnInput, fnError, 'Please enter your first name.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      } else if (fn.length < 2) {
        showPError(fnGroup, fnInput, fnError, 'First name must be at least 2 characters.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      } else if (/\d/.test(fn)) {
        showPError(fnGroup, fnInput, fnError, 'First name cannot contain numbers.');
        if (!hasErr && fnInput) fnInput.focus();
        hasErr = true;
      }

      if (!ln) {
        showPError(lnGroup, lnInput, lnError, 'Please enter your last name.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      } else if (ln.length < 2) {
        showPError(lnGroup, lnInput, lnError, 'Last name must be at least 2 characters.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      } else if (/\d/.test(ln)) {
        showPError(lnGroup, lnInput, lnError, 'Last name cannot contain numbers.');
        if (!hasErr && lnInput) lnInput.focus();
        hasErr = true;
      }

      if (!em) {
        showPError(emGroup, emInput, emError, 'Please enter your email address.');
        if (!hasErr && emInput) emInput.focus();
        hasErr = true;
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) {
        showPError(emGroup, emInput, emError, 'Please enter a valid email address.');
        if (!hasErr && emInput) emInput.focus();
        hasErr = true;
      }

      if (hasErr) {
        e.preventDefault();
      }
    });
  }

  const changePasswordForm = document.getElementById('changePasswordForm');
  if (changePasswordForm) {
    const curGroup = document.getElementById('curPwGroup');
    const curInput = document.getElementById('curPassInput');
    const curError = document.getElementById('curPwError');

    const newGroup = document.getElementById('newPwGroup');
    const newInput = document.getElementById('newPassInput');
    const newError = document.getElementById('newPwError');

    const confGroup = document.getElementById('confirmPwGroup');
    const confInput = document.getElementById('confirmPassInput');
    const confError = document.getElementById('confirmPwError');

    function clearPwError(group, input, errorBox) {
      if (group) group.classList.remove('has-error');
      if (input) input.classList.remove('is-invalid');
      if (errorBox) errorBox.style.display = 'none';
    }

    function showPwError(group, input, errorBox, message) {
      if (group) group.classList.add('has-error');
      if (input) input.classList.add('is-invalid');
      if (errorBox) {
        const textSpan = errorBox.querySelector('.msg-text') || errorBox.querySelector('span');
        if (textSpan && message) textSpan.textContent = message;
        errorBox.style.display = 'flex';
      }
    }

    if (curInput) curInput.addEventListener('input', () => clearPwError(curGroup, curInput, curError));
    if (newInput) newInput.addEventListener('input', () => clearPwError(newGroup, newInput, newError));
    if (confInput) confInput.addEventListener('input', () => clearPwError(confGroup, confInput, confError));

    changePasswordForm.addEventListener('submit', function (e) {
      let hasErr = false;
      const cur = curInput ? curInput.value : '';
      const nw = newInput ? newInput.value : '';
      const conf = confInput ? confInput.value : '';

      if (!cur) {
        showPwError(curGroup, curInput, curError, 'Please enter your current password.');
        if (!hasErr && curInput) curInput.focus();
        hasErr = true;
      }

      if (!nw) {
        showPwError(newGroup, newInput, newError, 'Please enter a new password.');
        if (!hasErr && newInput) newInput.focus();
        hasErr = true;
      } else if (nw.length < 6) {
        showPwError(newGroup, newInput, newError, 'New password must be at least 6 characters long.');
        if (!hasErr && newInput) newInput.focus();
        hasErr = true;
      }

      if (!conf) {
        showPwError(confGroup, confInput, confError, 'Please confirm your new password.');
        if (!hasErr && confInput) confInput.focus();
        hasErr = true;
      } else if (nw !== conf) {
        showPwError(confGroup, confInput, confError, 'New passwords do not match.');
        if (!hasErr && confInput) confInput.focus();
        hasErr = true;
      }

      if (hasErr) {
        e.preventDefault();
      }
    });
  }

  const allModalForms = document.querySelectorAll('.modal form');
  allModalForms.forEach(function (form) {
    form.setAttribute('novalidate', 'true');
    const inputs = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
    inputs.forEach(function (inp) {
      inp.addEventListener('input', function () {
        inp.classList.remove('is-invalid');
        const grp = inp.closest('.mb-3, .mb-2, .row > div, .messenger-field-group');
        if (grp) {
          grp.classList.remove('has-error');
          const lbl = grp.querySelector('.form-label');
          if (lbl) lbl.classList.remove('text-danger');
          const err = grp.querySelector('.messenger-error-msg');
          if (err) err.style.display = 'none';
        }
      });
      inp.addEventListener('change', function () {
        inp.classList.remove('is-invalid');
        const grp = inp.closest('.mb-3, .mb-2, .row > div, .messenger-field-group');
        if (grp) {
          grp.classList.remove('has-error');
          const lbl = grp.querySelector('.form-label');
          if (lbl) lbl.classList.remove('text-danger');
          const err = grp.querySelector('.messenger-error-msg');
          if (err) err.style.display = 'none';
        }
      });
    });

    form.addEventListener('submit', function (e) {
      let firstInvalid = null;
      inputs.forEach(function (inp) {
        if (inp.disabled || inp.readOnly) return;
        let isErr = false;
        let msg = '';

        if (inp.required && !inp.value.trim()) {
          isErr = true;
          msg = 'Please fill out this field.';
        } else if (inp.type === 'email' && inp.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inp.value.trim())) {
          isErr = true;
          msg = 'Please enter a valid email address.';
        } else if (inp.minLength > 0 && inp.value.trim().length < inp.minLength) {
          isErr = true;
          msg = (inp.title || ('Minimum length is ' + inp.minLength + ' characters.'));
        } else if (inp.pattern && inp.value.trim()) {
          const reg = new RegExp(inp.pattern);
          if (!reg.test(inp.value.trim())) {
            isErr = true;
            msg = (inp.title || 'Please match the requested format.');
          }
        }

        if (inp.name && inp.name.includes('confirm_password')) {
          const pw = form.querySelector('input[type="password"]:not([name*="confirm"])');
          if (pw && pw.value !== inp.value) {
            isErr = true;
            msg = 'Passwords do not match.';
          }
        }

        const grp = inp.closest('.mb-3, .mb-2, .row > div, .messenger-field-group');
        if (isErr) {
          if (!firstInvalid) firstInvalid = inp;
          inp.classList.add('is-invalid');
          if (grp) {
            grp.classList.add('has-error');
            const lbl = grp.querySelector('.form-label');
            if (lbl) lbl.classList.add('text-danger');
            let errBox = grp.querySelector('.messenger-error-msg');
            if (!errBox) {
              errBox = document.createElement('div');
              errBox.className = 'messenger-error-msg';
              errBox.innerHTML = '<i class="bi bi-exclamation-circle"></i> <span class="msg-text"></span>';
              grp.appendChild(errBox);
            }
            const textSpan = errBox.querySelector('.msg-text') || errBox.querySelector('span');
            if (textSpan) textSpan.textContent = msg;
            errBox.style.display = 'flex';
          }
        } else {
          inp.classList.remove('is-invalid');
          if (grp) {
            grp.classList.remove('has-error');
            const lbl = grp.querySelector('.form-label');
            if (lbl) lbl.classList.remove('text-danger');
            const errBox = grp.querySelector('.messenger-error-msg');
            if (errBox) errBox.style.display = 'none';
          }
        }
      });

      if (firstInvalid) {
        e.preventDefault();
        firstInvalid.focus();
      }
    });
  });

  function ensureConfirmModal() {
    let modalEl = document.getElementById('universalConfirmModal');
    if (!modalEl) {
      modalEl = document.createElement('div');
      modalEl.className = 'modal fade';
      modalEl.id = 'universalConfirmModal';
      modalEl.tabIndex = -1;
      modalEl.setAttribute('aria-hidden', 'true');
      modalEl.style.backdropFilter = 'blur(4px)';
      modalEl.innerHTML = `
        <div class="modal-dialog modal-dialog-centered" style="max-width: 420px;">
          <div class="modal-content rounded-4 border-0 shadow-lg p-3">
            <div class="modal-body text-center p-4">
              <div class="mb-3 d-inline-flex align-items-center justify-content-center rounded-circle" id="confirmModalIconWrapper" style="width: 64px; height: 64px; background: rgba(220, 53, 69, 0.1); color: #dc3545;">
                <i class="bi bi-exclamation-triangle fs-2" id="confirmModalIcon"></i>
              </div>
              <h5 class="fw-bold text-dark mb-2" id="confirmModalTitle">Are you sure?</h5>
              <p class="text-muted small mb-4" id="confirmModalMessage">This action cannot be undone.</p>
              <div class="d-flex justify-content-center gap-2">
                <button type="button" class="btn btn-light rounded-pill px-4 fw-semibold" data-bs-dismiss="modal" id="confirmModalCancelBtn">Cancel</button>
                <button type="button" class="btn btn-danger rounded-pill px-4 fw-semibold shadow-sm" id="confirmModalProceedBtn">Confirm</button>
              </div>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);
    }
    return modalEl;
  }

  if (typeof bootstrap !== 'undefined') {
    let pendingForm = null;

    function openConfirmModal(form, title, msg, btnText, btnColor) {
      pendingForm = form;
      const modalEl = ensureConfirmModal();
      const titleEl = modalEl.querySelector('#confirmModalTitle');
      const msgEl = modalEl.querySelector('#confirmModalMessage');
      const proceedBtn = modalEl.querySelector('#confirmModalProceedBtn');
      const iconWrapper = modalEl.querySelector('#confirmModalIconWrapper');
      const iconEl = modalEl.querySelector('#confirmModalIcon');

      if (titleEl) titleEl.textContent = title || 'Confirm Action';
      if (msgEl) msgEl.textContent = msg || 'Are you sure you want to proceed?';
      if (proceedBtn) {
        proceedBtn.textContent = btnText || 'Confirm';
        proceedBtn.className = 'btn rounded-pill px-4 fw-semibold shadow-sm ' + (btnColor || 'btn-danger');
      }

      if (iconWrapper && iconEl) {
        if (btnColor && btnColor.includes('success')) {
          iconWrapper.style.background = 'rgba(25, 135, 84, 0.1)';
          iconWrapper.style.color = '#198754';
          iconEl.className = 'bi bi-check-circle fs-2';
        } else if (btnColor && (btnColor.includes('warning') || btnColor.includes('secondary'))) {
          iconWrapper.style.background = 'rgba(255, 193, 7, 0.15)';
          iconWrapper.style.color = '#d97706';
          iconEl.className = 'bi bi-exclamation-circle fs-2';
        } else {
          iconWrapper.style.background = 'rgba(220, 53, 69, 0.1)';
          iconWrapper.style.color = '#dc3545';
          iconEl.className = 'bi bi-exclamation-triangle fs-2';
        }
      }

      const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
      bsModal.show();
    }

    document.addEventListener('submit', function(e) {
      const form = e.target;
      if (form.hasAttribute('data-confirm-modal') && !form.dataset.confirmed) {
        e.preventDefault();
        const title = form.getAttribute('data-confirm-title');
        const msg = form.getAttribute('data-confirm-message');
        const btnText = form.getAttribute('data-confirm-btn') || 'Confirm';
        const btnColor = form.getAttribute('data-confirm-color') || 'btn-danger';
        openConfirmModal(form, title, msg, btnText, btnColor);
      }
    });

    document.addEventListener('click', function(e) {
      const target = e.target;
      const modalEl = document.getElementById('universalConfirmModal');

      if (target && target.id === 'confirmModalProceedBtn') {
        if (pendingForm) {
          pendingForm.dataset.confirmed = 'true';
          if (modalEl) {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
            bsModal.hide();
          }
          pendingForm.submit();
        }
        return;
      }

      const confirmBtn = target.closest('button[data-confirm-modal="true"], a[data-confirm-modal="true"]');
      if (confirmBtn) {
        const form = confirmBtn.closest('form');
        if (form && !form.dataset.confirmed) {
          e.preventDefault();
          e.stopPropagation();
          const title = confirmBtn.getAttribute('data-confirm-title') || form.getAttribute('data-confirm-title');
          const msg = confirmBtn.getAttribute('data-confirm-message') || form.getAttribute('data-confirm-message');
          const btnText = confirmBtn.getAttribute('data-confirm-btn') || form.getAttribute('data-confirm-btn') || 'Confirm';
          const btnColor = confirmBtn.getAttribute('data-confirm-color') || form.getAttribute('data-confirm-color') || 'btn-danger';
          openConfirmModal(form, title, msg, btnText, btnColor);
        }
      }
    });
  }
});
