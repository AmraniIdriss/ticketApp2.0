"use strict";
document.addEventListener("DOMContentLoaded", () => {
  console.log("[view_tickets] JS loaded");

  // Utils
  const $ = (sel, scope = document) => scope.querySelector(sel);
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

  // 2) TIMER with display update
  console.log("[Timer] Timer initialization");

  document.addEventListener('click', function (e) {
    // START BUTTON
    const startButton = e.target.closest('.start-timer');
    if (startButton) {
      console.log('Start button clicked');
      const row = startButton.closest('tr');
      const ticketId = row.querySelector('td:first-child').textContent.trim();
      console.log('Ticket ID:', ticketId);
      const csrfToken = getCSRF();

      if (!csrfToken) {
        alert('Missing CSRF token');
        return;
      }

      // Disable the button during the request
      startButton.disabled = true;
      startButton.innerHTML = '<i class="bi bi-play-fill"></i> Starting...';

      fetch(`/tickets/${ticketId}/start/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        }
      })
        .then(response => {
          // Handle HTTP errors
          if (!response.ok) {
            return response.json().then(err => {
              throw new Error(err.error || `HTTP ${response.status}`);
            });
          }
          return response.json();
        })
        .then(data => {
          console.log('Start response:', data);

          // Update the display in the row
          const startDisplaySpan = row.querySelector('.activity-start-display');
          const statusBadge = row.querySelector('.activity-start-time');
          const stopButton = row.querySelector('.stop-timer');

          // Show the start date
          if (startDisplaySpan && data.activity_start) {
            startDisplaySpan.textContent = formatDateTime(data.activity_start);
            startDisplaySpan.classList.remove('text-muted');
          }

          // Update the status badge
          if (statusBadge) {
            statusBadge.textContent = 'Running...';
            statusBadge.classList.remove('bg-info', 'bg-secondary', 'bg-warning');
            statusBadge.classList.add('bg-success');

          }

          // Update the buttons
          startButton.disabled = true;
          startButton.innerHTML = '<i class="bi bi-play-fill"></i> Running';

          if (stopButton) {
            stopButton.disabled = false;
          }

          alert('Timer started!');
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error: ' + error.message);

          // Re-enable the button in case of error
          startButton.disabled = false;
          startButton.innerHTML = '<i class="bi bi-play-fill"></i> Start';
        });
      return; // Prevents handling both start and stop on the same click
    }

    // STOP BUTTON
    const stopButton = e.target.closest('.stop-timer');
    if (stopButton) {
      console.log('Stop button clicked');
      const row = stopButton.closest('tr');
      const ticketId = row.querySelector('td:first-child').textContent.trim();
      const csrfToken = getCSRF();

      // Disable the button during the request
      stopButton.disabled = true;
      stopButton.innerHTML = '<i class="bi bi-stop-fill"></i> Stopping...';

      fetch(`/tickets/${ticketId}/stop/`, {
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

          // Update the display in the row
          console.log('🧩 DEBUG row:', row);
          console.log('🧩 row HTML:', row.outerHTML);
          console.log('🧩 has badge:', row.querySelector('.activity-start-time'));

          const startDisplaySpan = row.querySelector('.activity-start-display');

          const endDisplaySpan = row.querySelector('.activity-end-time');

          const statusBadge = row.querySelector('.activity-start-time');
          const startButton = row.querySelector('.start-timer');
          const timeSpentSpan = row.querySelector('.time-spent-display');

          // Reset the start display (since it's reset server-side)
          // Keep the start date visible when stopping
          if (startDisplaySpan && data.activity_start) {
            startDisplaySpan.textContent = formatDateTime(data.activity_start);
            startDisplaySpan.classList.remove('text-muted');
          }


          // Show the end date
          if (endDisplaySpan && data.activity_end) {
            endDisplaySpan.textContent = formatDateTime(data.activity_end);
            endDisplaySpan.classList.remove('text-muted');
          }

          // ✅ Update the status badge (corrigé)
          if (statusBadge) {
            statusBadge.textContent = 'Finished';
            statusBadge.classList.remove('bg-success', 'bg-info', 'bg-warning');
            statusBadge.classList.add('bg-secondary');

          } else {
            console.warn('⚠️ statusBadge not found for this row:', row.outerHTML);
          }

          // Update the time spent in the last column
          if (timeSpentSpan && data.time_spent !== undefined) {
            timeSpentSpan.innerHTML = data.time_spent + ' h';
          } else if (timeSpentSpan) {
            timeSpentSpan.innerHTML = '0.00 h';
          }

          // Update the buttons
          stopButton.disabled = true;
          stopButton.innerHTML = '<i class="bi bi-stop-fill"></i> Stop';

          if (startButton) {
            startButton.disabled = false;
            startButton.innerHTML = '<i class="bi bi-play-fill"></i> Start';
          }

          alert('Timer stopped! Time spent: ' + (data.time_spent || 0) + ' hours');
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error: ' + error.message);

          // Re-enable the button in case of error
          stopButton.disabled = false;
          stopButton.innerHTML = '<i class="bi bi-stop-fill"></i> Stop';
        });
    }
  });

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
        const ticketId = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
        const customer = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
        const reportedUser = row.querySelector('td:nth-child(4)').textContent.toLowerCase();
        const reportedBy = row.querySelector('td:nth-child(5)').textContent.toLowerCase();
        const activityType = row.querySelector('td:nth-child(7)').textContent.toLowerCase();
        const activityTitle = row.querySelector('td:nth-child(12)').textContent.toLowerCase();
        const currentState = row.querySelector('td:nth-child(11)').textContent.toLowerCase();
        const analyst = row.querySelector('td:nth-child(9)').textContent.toLowerCase();

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

      // Show a message if no result
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