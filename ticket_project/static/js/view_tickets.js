"use strict";
document.addEventListener("DOMContentLoaded", () => {
  console.log("[view_tickets] JS loaded");

  // Utils
  const $ = (sel, scope = document) => scope.querySelector(sel);
  const $$ = (sel, scope = document) => scope.querySelectorAll(sel);
  const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(";").shift());
    return null;
  };
  const getCSRF = () =>
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    getCookie("csrftoken") ||
    "";

  // Row Selection System
  let selectedTicket = null;
  
  function updateRowSelection(checkbox, shouldCheck = true) {
    // Deselect any previously selected row
    const previouslySelected = $('.ticket-select:checked');
    if (previouslySelected && previouslySelected !== checkbox) {
      previouslySelected.checked = false;
      previouslySelected.closest('tr')?.classList.remove('table-active');
    }
    
    const row = checkbox.closest('tr');
    checkbox.checked = shouldCheck;
    
    if (checkbox.checked) {
      selectedTicket = checkbox.value;
      row.classList.add('table-active');
      updateControlButtons();
    } else {
      selectedTicket = null;
      row.classList.remove('table-active');
      updateControlButtons();
    }
    
    console.log('Selected ticket:', selectedTicket);
  }
  
  // Update the state of centralized control buttons
  function updateControlButtons() {
    const startBtn = $('#globalStartBtn');
    const stopBtn = $('#globalStopBtn');
    
    if (!selectedTicket) {
      startBtn.disabled = true;
      stopBtn.disabled = true;
      return;
    }
    
    const selectedRow = document.querySelector(`tr[data-ticket-id="${selectedTicket}"]`);
    if (!selectedRow) return;
    
    const statusBadge = selectedRow.querySelector('.activity-start-time');
    const statusText = statusBadge?.textContent.trim();
    
    // Enable/disable based on timer state
    if (statusText === 'Running...') {
      startBtn.disabled = true;
      stopBtn.disabled = false;
    } else if (statusText === 'Finished') {
      startBtn.disabled = false;
      stopBtn.disabled = true;
    } else {
      startBtn.disabled = false;
      stopBtn.disabled = true;
    }
  }
  
  // Handle checkbox selection
  document.addEventListener('change', (e) => {
    if (e.target.matches('.ticket-select')) {
      updateRowSelection(e.target, e.target.checked);
    }
  });

  // -------------------------------
  // Time-to-start timers (created -> activity_start)
  // -------------------------------
  const timeToStartIntervals = new Map();

  function formatDuration(ms) {
    if (ms < 0) ms = 0;
    const totalSec = Math.floor(ms / 1000);
    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    let parts = [];
    if (days) parts.push(days + 'd');
    if (hours || days) parts.push(String(hours).padStart(2, '0') + 'h');
    parts.push(String(mins).padStart(2, '0') + 'm');
    parts.push(String(secs).padStart(2, '0') + 's');
    return parts.join(' ');
  }

  function stopTimeToStartForRow(row, activityStartISO) {
    const ticketId = row.dataset.ticketId;
    const createdISO = row.dataset.created;
    if (!createdISO || !activityStartISO) return;
    // clear interval if running
    const key = ticketId;
    if (timeToStartIntervals.has(key)) {
      clearInterval(timeToStartIntervals.get(key));
      timeToStartIntervals.delete(key);
    }
    const created = new Date(createdISO);
    const activityStart = new Date(activityStartISO);
    const diff = activityStart - created;
    const el = row.querySelector('.time-to-start-display');
    if (el) el.textContent = formatDuration(diff) + ' (to start)';
  }

  function startTimeToStartForRow(row) {
    const ticketId = row.dataset.ticketId;
    const createdISO = row.dataset.created;
    const activityStartISO = row.dataset.activityStart || row.dataset.activityStart || row.getAttribute('data-activity-start');
    const display = row.querySelector('.time-to-start-display');
    if (!createdISO || !display) return;

    if (activityStartISO) {
      // already started: show final value
      stopTimeToStartForRow(row, activityStartISO);
      return;
    }

    // live timer until activity_start is set
    function tick() {
      const now = new Date();
      const created = new Date(createdISO);
      const diff = now - created;
      display.textContent = formatDuration(diff) + ' (waiting)';
    }

    tick();
    const interv = setInterval(tick, 1000);
    timeToStartIntervals.set(ticketId, interv);
  }

  // initialize timers for all rows
  document.querySelectorAll('tbody tr[data-ticket-id]').forEach(row => {
    // ensure dataset.created is present if data-created attribute exists
    if (!row.dataset.created) {
      const d = row.getAttribute('data-created');
      if (d) row.dataset.created = d;
    }
    if (!row.dataset.activityStart) {
      const as = row.getAttribute('data-activity-start');
      if (as) row.dataset.activityStart = as;
    }
    startTimeToStartForRow(row);
  });
  
  // Handle row click selection
  document.addEventListener('click', (e) => {
    const row = e.target.closest('tr');
    if (row && !e.target.matches('button, a, input, .btn-group *, .show-description-btn *')) {
      const checkbox = row.querySelector('.ticket-select');
      if (checkbox) {
        updateRowSelection(checkbox, !checkbox.checked);
      }
    }
  });

  // Function to format a date
  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB') + ' ' + date.toLocaleTimeString('en-GB');
  };

  // 1) Modal "Activity Resolution Description"
  const descModalEl = $("#descriptionModal");
  if (descModalEl && window.bootstrap?.Modal) {
    const descModal = new bootstrap.Modal(descModalEl);
    document.addEventListener("click", (e) => {
      const btn = e.target.closest(".show-description-btn");
      if (!btn) return;
      const desc = btn.getAttribute("data-description") || "-";
      const body = $("#descriptionModalBody");
      if (body) body.textContent = desc;
      descModal.show();
    });
  }

  // 2) CENTRALIZED TIMER CONTROLS
  console.log("[Timer] Timer initialization");

  // Global Start Button
  const globalStartBtn = $('#globalStartBtn');
  if (globalStartBtn) {
    globalStartBtn.addEventListener('click', function() {
      if (!selectedTicket) {
        alert('Please select a ticket first');
        return;
      }

      const row = document.querySelector(`tr[data-ticket-id="${selectedTicket}"]`);
      if (!row) return;

      const csrfToken = getCSRF();
      if (!csrfToken) {
        alert('Missing CSRF token');
        return;
      }

      globalStartBtn.disabled = true;
      globalStartBtn.innerHTML = '<i class="bi bi-play-fill"></i> Starting...';

      fetch(`/tickets/${selectedTicket}/start/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        }
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => {
              throw new Error(err.error || `HTTP ${response.status}`);
            });
          }
          return response.json();
        })
        .then(data => {
          console.log('Start response:', data);

          const startDisplaySpan = row.querySelector('.activity-start-display');
          const statusBadge = row.querySelector('.activity-start-time');

          if (startDisplaySpan && data.activity_start) {
            startDisplaySpan.textContent = formatDateTime(data.activity_start);
            startDisplaySpan.classList.remove('text-muted');
          }

          if (statusBadge) {
            statusBadge.textContent = 'Running...';
            statusBadge.classList.remove('bg-info', 'bg-secondary', 'bg-warning');
            statusBadge.classList.add('bg-success');
          }

          // Update row data and stop the waiting timer
          if (row) {
            row.dataset.activityStart = data.activity_start;
            try { stopTimeToStartForRow(row, data.activity_start); } catch (e) { /* ignore */ }
          }

          globalStartBtn.innerHTML = '<i class="bi bi-play-fill"></i> Start';
          updateControlButtons();
          alert('Timer started!');
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error: ' + error.message);
          globalStartBtn.disabled = false;
          globalStartBtn.innerHTML = '<i class="bi bi-play-fill"></i> Start';
        });
    });
  }

  // Global Stop Button
  const globalStopBtn = $('#globalStopBtn');
  if (globalStopBtn) {
    globalStopBtn.addEventListener('click', function() {
      if (!selectedTicket) {
        alert('Please select a ticket first');
        return;
      }

      const row = document.querySelector(`tr[data-ticket-id="${selectedTicket}"]`);
      if (!row) return;

      const csrfToken = getCSRF();
      if (!csrfToken) {
        alert('Missing CSRF token');
        return;
      }

      globalStopBtn.disabled = true;
      globalStopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> Stopping...';

      fetch(`/tickets/${selectedTicket}/stop/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current_state: "In Progress"
        })
      })
        .then(response => {
          if (!response.ok) {
            return response.json().then(err => {
              throw new Error(err.error || `HTTP ${response.status}`);
            });
          }
          return response.json();
        })
        .then(data => {
          console.log('Stop response:', data);

          const startDisplaySpan = row.querySelector('.activity-start-display');
          const endDisplaySpan = row.querySelector('.activity-end-time');
          const statusBadge = row.querySelector('.activity-start-time');
          const timeSpentSpan = row.querySelector('.time-spent-display');

          if (startDisplaySpan && data.activity_start) {
            startDisplaySpan.textContent = formatDateTime(data.activity_start);
            startDisplaySpan.classList.remove('text-muted');
          }

          if (endDisplaySpan && data.activity_end) {
            endDisplaySpan.textContent = formatDateTime(data.activity_end);
            endDisplaySpan.classList.remove('text-muted');
          }

          if (statusBadge) {
            statusBadge.textContent = 'Finished';
            statusBadge.classList.remove('bg-success', 'bg-info', 'bg-warning');
            statusBadge.classList.add('bg-secondary');
          }

          if (timeSpentSpan && data.time_spent !== undefined) {
            timeSpentSpan.innerHTML = data.time_spent + ' h';
          } else if (timeSpentSpan) {
            timeSpentSpan.innerHTML = '0.00 h';
          }

          globalStopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> Stop';
          updateControlButtons();
          alert('Timer stopped! Time spent: ' + (data.time_spent || 0) + ' hours');
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error: ' + error.message);
          globalStopBtn.disabled = false;
          globalStopBtn.innerHTML = '<i class="bi bi-stop-fill"></i> Stop';
        });
    });
  }

  // Initialize button states
  updateControlButtons();

  // 3) SEARCH BAR - Smart ticket filtering
  const searchInput = document.querySelector('input[name="q"]');

  if (searchInput) {
    searchInput.form.addEventListener('submit', (e) => {
      e.preventDefault();
    });

    searchInput.addEventListener('input', function () {
      const searchTerm = this.value.toLowerCase().trim();
      const rows = document.querySelectorAll('tbody tr[data-ticket-id]');
      let visibleCount = 0;

      rows.forEach(row => {
        const ticketId = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
        const customer = row.querySelector('td:nth-child(4)').textContent.toLowerCase();
        const reportedUser = row.querySelector('td:nth-child(5)').textContent.toLowerCase();
        const reportedBy = row.querySelector('td:nth-child(6)').textContent.toLowerCase();
        const activityType = row.querySelector('td:nth-child(8)').textContent.toLowerCase();
        const activityTitle = row.querySelector('td:nth-child(13)').textContent.toLowerCase();
        const currentState = row.querySelector('td:nth-child(12)').textContent.toLowerCase();
        const analyst = row.querySelector('td:nth-child(10)').textContent.toLowerCase();

        const matches = ticketId.includes(searchTerm) ||
          customer.includes(searchTerm) ||
          reportedUser.includes(searchTerm) ||
          reportedBy.includes(searchTerm) ||
          activityType.includes(searchTerm) ||
          activityTitle.includes(searchTerm) ||
          currentState.includes(searchTerm) ||
          analyst.includes(searchTerm);

        if (matches || searchTerm === '') {
          row.style.display = '';
          visibleCount++;
        } else {
          row.style.display = 'none';
        }
      });

      const tbody = document.querySelector('tbody');
      let noResultMsg = document.getElementById('no-result-message');

      if (visibleCount === 0 && searchTerm !== '') {
        if (!noResultMsg) {
          noResultMsg = document.createElement('tr');
          noResultMsg.id = 'no-result-message';
          noResultMsg.innerHTML = `
            <td colspan="17" class="text-center text-muted py-4">
              <i class="bi bi-search"></i> No tickets found for "${this.value}"
            </td>
          `;
          tbody.appendChild(noResultMsg);
        }
      } else if (noResultMsg) {
        noResultMsg.remove();
      }

      console.log(`Search: "${searchTerm}" - ${visibleCount} result(s)`);
    });
    console.log("[Search] Search bar initialized");
  }

  console.log("[Timer] Timer successfully initialized");
});