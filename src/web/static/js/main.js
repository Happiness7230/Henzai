// Main JavaScript file to handle search interactions
  // Main JavaScript file to handle search interactions
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        const query = document.querySelector('input[name="query"]').value.trim();
        if (!query) {
            alert('Please enter a search query.');
            e.preventDefault();
          }
      });
 });
  