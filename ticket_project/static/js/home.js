"use strict";

document.addEventListener("DOMContentLoaded", () => {
  console.log("[home] Navigation handler loaded");

  // Handle ticket row clicks in all tables
  const ticketTables = document.querySelectorAll('.ticket-section table tbody');
  
  ticketTables.forEach(tbody => {
    tbody.addEventListener('click', (e) => {
      // Find the clicked row
      const row = e.target.closest('tr');
      
      // Ignore clicks on empty rows or header rows
      if (!row || row.querySelector('td[colspan]')) {
        return;
      }
      
      // Get the ticket ID from the third column (Ticket ID)
      const ticketIdCell = row.querySelector('td:nth-child(3)');
      
      if (!ticketIdCell) {
        return;
      }
      
      const ticketId = ticketIdCell.textContent.trim();
      
      if (!ticketId || ticketId === '') {
        return;
      }
      
      console.log(`[home] Navigating to ticket detail #${ticketId}`);
      
      // Navigate to the new ticket detail page
      window.location.href = `/tickets/ticket/${encodeURIComponent(ticketId)}/`;
    });
  });
  
  // Add hover effect to indicate clickability
  const allRows = document.querySelectorAll('.ticket-section table tbody tr');
  
  allRows.forEach(row => {
    // Skip empty state rows
    if (row.querySelector('td[colspan]')) {
      return;
    }
    
    // Add cursor pointer style
    row.style.cursor = 'pointer';
    
    // Add visual feedback on hover
    row.addEventListener('mouseenter', () => {
      row.style.backgroundColor = 'var(--row-alt)';
      // Add a slight scale effect
      row.style.transform = 'scale(1.01)';
      row.style.transition = 'all 0.2s ease';
    });
    
    row.addEventListener('mouseleave', () => {
      row.style.backgroundColor = '';
      row.style.transform = 'scale(1)';
    });
  });
  
  console.log("[home] Navigation handler initialized successfully");
});