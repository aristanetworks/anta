// report_filter.js - Client-side filtering and sorting logic for ANTA HTML Report

// Wait for the entire HTML document to be fully loaded and parsed
document.addEventListener('DOMContentLoaded', () => {

    // --- DOM Element References ---
    // Get references to the filter control elements by their IDs
    const deviceFilter = document.getElementById('deviceFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    const testFilter = document.getElementById('testFilter');
    // Get all radio buttons used for status filtering
    const statusFilterGroup = document.querySelectorAll('input[name="statusFilter"]');

    // Get references related to the main results table
    const resultsTableBody = document.getElementById('results-tbody'); // The <tbody> element
    // Get all table rows (<tr>) within the body and convert the NodeList to an Array for easier manipulation (sorting)
    const tableRows = resultsTableBody ? Array.from(resultsTableBody.querySelectorAll('tr')) : [];
    // Get the element displaying the count of visible rows
    const filteredRowCount = document.getElementById('filtered-row-count');

    // Get references to clickable elements in the overall summary cards
    const overallSummaryLinks = document.querySelectorAll('.overall-summary-link');
    // Get all sortable table headers (<th> elements with class 'sortable')
    const sortableHeaders = document.querySelectorAll('#results-table thead th.sortable');
    // Get the "Back to Top" button
    const backToTopButton = document.getElementById('backToTopBtn');

    // --- State Variables ---
    // Keep track of the currently active sort column and direction
    let currentSort = {
        columnKey: null, // Key identifying the column (from data-column-key)
        direction: 'asc' // 'asc' (ascending) or 'desc' (descending)
    };

    // --- Utility Functions ---

    /**
     * Sets the value of a dropdown (<select>) filter element.
     * @param {HTMLSelectElement} filterElement - The select dropdown element.
     * @param {string} value - The value to set.
     */
    function setFilterValue(filterElement, value) {
        if (filterElement) { // Check if the element exists
            filterElement.value = value;
        }
    }

    /**
     * Checks the appropriate status radio button based on the provided value.
     * @param {string} value - The status value (e.g., "success", "failure", "" for all).
     */
    function setStatusRadio(value) {
        // Construct the ID of the target radio button (e.g., 'status_success', 'status_all')
        const targetRadioId = `status_${value || 'all'}`;
        const targetRadio = document.getElementById(targetRadioId);
        if (targetRadio) { // Check if the radio button exists
            targetRadio.checked = true; // Set it as checked
        }
    }

    /**
     * Shows or hides the "Back to Top" button based on vertical scroll position.
     */
    function handleScroll() {
        if (backToTopButton) { // Check if the button exists
            // Show button if scrolled down more than 100 pixels, otherwise hide it
            if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
                backToTopButton.style.display = "block";
            } else {
                backToTopButton.style.display = "none";
            }
        }
    }

    /**
     * Scrolls the window smoothly back to the top of the page.
     */
    function scrollToTop() {
        // Use documentElement for broader browser compatibility
        document.documentElement.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- Core Logic Functions ---

    /**
     * Filters the main results table rows based on the currently selected filter values.
     * Shows/hides rows and updates the visible row count.
     */
    function filterTable() {
        // Exit if the table body isn't found
        if (!resultsTableBody) return;

        // Get current values from filter controls
        const selectedDevice = deviceFilter ? deviceFilter.value : "";
        const selectedCategory = categoryFilter ? categoryFilter.value : "";
        const selectedTest = testFilter ? testFilter.value : "";
        const checkedStatusRadio = document.querySelector('input[name="statusFilter"]:checked');
        const selectedStatus = checkedStatusRadio ? checkedStatusRadio.value : "";
        let visibleRows = 0; // Counter for visible rows

        // Iterate through each row in the table
        tableRows.forEach(row => {
            // Read the data attributes stored on the row element
            const rowDevice = row.dataset.device || "";
            const rowStatus = row.dataset.status || "";
            const rowCategories = row.dataset.categories || ""; // Space-separated list
            const rowTest = row.dataset.test || "";

            // Determine if the row matches *all* active filters
            // An empty filter value means that filter is inactive (matches all)
            const deviceMatch = !selectedDevice || rowDevice === selectedDevice;
            const statusMatch = !selectedStatus || rowStatus === selectedStatus;
            // Category match checks if the selected category is present in the row's space-separated list
            const categoryMatch = !selectedCategory || (rowCategories && rowCategories.split(' ').includes(selectedCategory));
            const testMatch = !selectedTest || rowTest === selectedTest;

            // Show or hide the row based on whether all filters match
            if (deviceMatch && statusMatch && categoryMatch && testMatch) {
                row.style.display = ''; // Show row (reverts to default display: table-row)
                visibleRows++;
            } else {
                row.style.display = 'none'; // Hide row
            }
        });

        // Update the caption text showing the filtered count
        if (filteredRowCount) {
            filteredRowCount.textContent = `Showing ${visibleRows} of ${tableRows.length} results.`;
        }
    }

    /**
     * Gets the text content of a specific cell in a table row for sorting comparison.
     * @param {HTMLTableRowElement} row - The table row element.
     * @param {number} columnIndex - The index of the cell (0-based).
     * @returns {string} The trimmed text content of the cell.
     */
    function getCellValue(row, columnIndex) {
        // Use optional chaining (?.) to safely access cell and textContent, default to empty string
        return row.cells[columnIndex]?.textContent?.trim() || '';
    }

    /**
     * Sorts the main results table rows based on the clicked column header.
     * @param {number} columnIndex - The index of the clicked header cell within its row.
     * @param {string} columnKey - The unique key for the column (from data-column-key).
     */
    function sortTable(columnIndex, columnKey) {
        // Exit if the table body isn't found
        if (!resultsTableBody) return;

        // Determine sort direction: toggle if same column, default to 'asc' for new column
        if (currentSort.columnKey === columnKey) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.columnKey = columnKey;
            currentSort.direction = 'asc'; // Default to ascending for a new column
        }

        // Modifier for sorting direction (1 for asc, -1 for desc)
        const directionModifier = currentSort.direction === 'asc' ? 1 : -1;

        // Create a sorted copy of the row elements array
        const sortedRows = [...tableRows].sort((rowA, rowB) => {
            // Get cell values for comparison
            const valA = getCellValue(rowA, columnIndex);
            const valB = getCellValue(rowB, columnIndex);

            // Use localeCompare for proper string sorting (case-insensitive)
            // Future enhancement: Add logic here to handle numeric or date sorting if needed
            return valA.localeCompare(valB, undefined, { sensitivity: 'base' }) * directionModifier;
        });

        // Re-append the rows to the table body in the new sorted order
        // This physically rearranges the elements in the HTML DOM
        sortedRows.forEach(row => resultsTableBody.appendChild(row));

        // Update the visual sort indicator icons in the table headers
        updateSortIcons(columnIndex);
    }

    /**
     * Updates the visual sort icons (▲/▼/◇) in the table headers
     * to indicate the currently sorted column and direction.
     * @param {number} activeIndex - The cell index of the currently sorted column header.
     */
    function updateSortIcons(activeIndex) {
         sortableHeaders.forEach((header) => {
            const icon = header.querySelector('.sort-icon');
            if (!icon) return; // Skip if header doesn't have an icon element

            // Check if this header's cellIndex matches the currently sorted column index
            if (header.cellIndex === activeIndex) {
                // Set the icon based on the current sort direction
                icon.textContent = currentSort.direction === 'asc' ? ' ▲' : ' ▼';
                icon.style.opacity = '1'; // Make active icon fully visible
            } else {
                 // Set default icon for non-sorted columns
                 icon.textContent = ' ◇';
                 icon.style.opacity = '0.3'; // Dim inactive icons
            }
         });
    }

    // --- Event Listeners ---

    // Add 'change' listeners to standard filter controls (dropdowns, radio buttons)
    // These listeners simply call filterTable (scrolling removed)
    if (deviceFilter) deviceFilter.addEventListener('change', filterTable);
    if (categoryFilter) categoryFilter.addEventListener('change', filterTable);
    if (testFilter) testFilter.addEventListener('change', filterTable);
    statusFilterGroup.forEach(radio => {
        if (radio) radio.addEventListener('change', filterTable);
    });

    // Add 'click' listeners to the Overall Summary cards/links
     overallSummaryLinks.forEach(link => {
        link.addEventListener('click', (event) => {
             event.preventDefault(); // Prevent default anchor link behavior
             // Get the target status from the link's data attribute
             const targetStatus = link.dataset.statusFilter || "";
             // Reset other filters to show only results for the clicked status
             setFilterValue(deviceFilter, "");
             setFilterValue(categoryFilter, "");
             setFilterValue(testFilter, "");
             // Set the status radio button
             setStatusRadio(targetStatus);
             // Apply the filter
             filterTable();
             // No scroll needed as filters are sticky
        });
     });

     // Add 'click' listeners to sortable table headers
     sortableHeaders.forEach((header) => {
        // Get the column key and index needed for sorting logic
        const columnKey = header.dataset.columnKey;
        const columnIndex = header.cellIndex; // Get index within the <tr>

        if(columnKey) { // Only add listener if it's a sortable column with a key
             header.addEventListener('click', () => {
                // Call sortTable when header is clicked
                sortTable(columnIndex, columnKey);
             });
             // Initialize sort icon appearance
             const icon = header.querySelector('.sort-icon');
             if(icon) {
                icon.textContent = ' ◇'; // Default indicator
                icon.style.opacity = '0.3';
             }
             header.style.cursor = 'pointer'; // Change cursor to indicate clickable
        }
     });

    // Add 'scroll' listener for the Back to Top button visibility
    window.addEventListener('scroll', handleScroll);
    // Add 'click' listener for the Back to Top button action
    if (backToTopButton) {
        backToTopButton.addEventListener('click', scrollToTop);
    }

    // --- Initial Setup ---
    // Apply filters initially (shows all rows but updates count)
    filterTable();
    // Initialize sort icons (no column sorted initially)
    updateSortIcons(-1); // Pass invalid index
    // Check initial scroll position for Back to Top button
    handleScroll();

}); // End DOMContentLoaded wrapper
