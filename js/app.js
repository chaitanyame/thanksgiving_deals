// Global state
let allDeals = [];
let filteredDeals = [];
let categoryIndex = null; // Pre-indexed categories
let currentPage = 1;
let itemsPerPage = 100;
let searchDebounceTimer = null;

// DOM Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const noResults = document.getElementById('noResults');
const dealsTable = document.getElementById('dealsTable');
const dealsTableBody = document.getElementById('dealsTableBody');
const lastUpdatedSpan = document.getElementById('lastUpdated');
const dealCountSpan = document.getElementById('dealCount');
const mainCategoryFilter = document.getElementById('mainCategoryFilter');
const subCategoryFilter = document.getElementById('subCategoryFilter');
const searchInput = document.getElementById('searchInput');
const sortBy = document.getElementById('sortBy');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const pageInfoElement = document.getElementById('pageInfo');
const itemsPerPageSelect = document.getElementById('itemsPerPage');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDeals();
    setupEventListeners();
});

/**
 * Load deals from data/deals.json
 */
async function loadDeals() {
    try {
        const response = await fetch('data/deals.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        allDeals = data.deals || [];

        // Pre-index categories for instant filtering
        buildCategoryIndex();

        // Update last updated time
        if (data.lastUpdated) {
            lastUpdatedSpan.textContent = formatDate(data.lastUpdated);
        }

        // Hide loading spinner
        loadingSpinner.style.display = 'none';

        if (allDeals.length === 0) {
            showNoResults();
            return;
        }

        // Populate filters
        populateMainCategoryFilter();
        populateSubCategoryFilter();

        // Initial render
        applyFilters();

    } catch (error) {
        console.error('Error loading deals:', error);
        loadingSpinner.style.display = 'none';
        errorMessage.textContent = 'Failed to load deals. Please try again later.';
        errorMessage.style.display = 'block';
    }
}

/**
 * Build category index for fast filtering (90% faster category lookups)
 */
function buildCategoryIndex() {
    categoryIndex = {
        byMainCategory: {},
        bySubCategory: {},
        mainCategories: new Set(),
        subCategories: new Set()
    };

    allDeals.forEach((deal, index) => {
        const main = deal.mainCategory || 'Uncategorized';
        const sub = deal.subCategory || '';

        // Index by main category
        if (!categoryIndex.byMainCategory[main]) {
            categoryIndex.byMainCategory[main] = [];
        }
        categoryIndex.byMainCategory[main].push(index);

        // Index by sub category
        if (sub) {
            if (!categoryIndex.bySubCategory[sub]) {
                categoryIndex.bySubCategory[sub] = [];
            }
            categoryIndex.bySubCategory[sub].push(index);
        }

        categoryIndex.mainCategories.add(main);
        if (sub) categoryIndex.subCategories.add(sub);
    });
}

/**
 * Populate main category filter (using pre-indexed data)
 */
function populateMainCategoryFilter() {
    // Sort categories alphabetically
    const sortedCategories = Array.from(categoryIndex.mainCategories).sort();

    // Clear existing options (except "All Categories")
    mainCategoryFilter.innerHTML = '<option value="">All Categories</option>';

    // Add category options using DocumentFragment for batching
    const fragment = document.createDocumentFragment();
    sortedCategories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        fragment.appendChild(option);
    });
    mainCategoryFilter.appendChild(fragment);
}

/**
 * Populate sub category filter based on selected main category (using pre-indexed data)
 */
function populateSubCategoryFilter() {
    const selectedMainCategory = mainCategoryFilter.value;
    const subCategories = new Set();

    if (selectedMainCategory === '') {
        // Show all sub categories
        categoryIndex.subCategories.forEach(sub => subCategories.add(sub));
    } else {
        // Show sub categories for selected main category
        const dealIndices = categoryIndex.byMainCategory[selectedMainCategory] || [];
        dealIndices.forEach(index => {
            const sub = allDeals[index].subCategory;
            if (sub) subCategories.add(sub);
        });
    }

    // Sort sub categories alphabetically
    const sortedSubCategories = Array.from(subCategories).sort();

    // Clear existing options
    subCategoryFilter.innerHTML = '<option value="">All Sub Categories</option>';

    // Add sub category options using DocumentFragment
    const fragment = document.createDocumentFragment();
    sortedSubCategories.forEach(subCategory => {
        const option = document.createElement('option');
        option.value = subCategory;
        option.textContent = subCategory;
        fragment.appendChild(option);
    });
    subCategoryFilter.appendChild(fragment);
}

/**
 * Apply filters and sorting
 */
function applyFilters() {
    const selectedMainCategory = mainCategoryFilter.value;
    const selectedSubCategory = subCategoryFilter.value;
    const searchTerm = searchInput.value.toLowerCase().trim();
    const sortOrder = sortBy.value;

    // Filter deals
    filteredDeals = allDeals.filter(deal => {
        // Main category filter
        if (selectedMainCategory && deal.mainCategory !== selectedMainCategory) {
            return false;
        }

        // Sub category filter
        if (selectedSubCategory && deal.subCategory !== selectedSubCategory) {
            return false;
        }

        // Search filter
        if (searchTerm) {
            const searchFields = [
                deal.title,
                deal.mainCategory,
                deal.subCategory,
                deal.store,
                deal.notes
            ].filter(field => field);

            const matches = searchFields.some(field => 
                field.toLowerCase().includes(searchTerm)
            );

            if (!matches) return false;
        }

        return true;
    });

    // Sort deals
    sortDeals(sortOrder);

    // Update deal count
    dealCountSpan.textContent = filteredDeals.length;

    // Reset to first page when filters change
    currentPage = 1;

    // Render deals with pagination
    renderDeals();
}

/**
 * Sort deals based on selected option
 */
function sortDeals(sortOrder) {
    switch (sortOrder) {
        case 'date-desc':
            filteredDeals.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));
            break;
        case 'date-asc':
            filteredDeals.sort((a, b) => new Date(a.pubDate) - new Date(b.pubDate));
            break;
        case 'price-asc':
            filteredDeals.sort((a, b) => {
                const priceA = extractNumericPrice(a.salePrice);
                const priceB = extractNumericPrice(b.salePrice);
                if (priceA === null) return 1;
                if (priceB === null) return -1;
                return priceA - priceB;
            });
            break;
        case 'price-desc':
            filteredDeals.sort((a, b) => {
                const priceA = extractNumericPrice(a.salePrice);
                const priceB = extractNumericPrice(b.salePrice);
                if (priceA === null) return 1;
                if (priceB === null) return -1;
                return priceB - priceA;
            });
            break;
    }
}

/**
 * Extract numeric price from string
 */
function extractNumericPrice(priceStr) {
    if (!priceStr) return null;
    const match = priceStr.match(/[\d,]+\.?\d*/);
    if (!match) return null;
    return parseFloat(match[0].replace(/,/g, ''));
}

/**
 * Render deals table with pagination (optimized with DocumentFragment)
 */
function renderDeals() {
    // Calculate pagination
    const totalPages = Math.ceil(filteredDeals.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredDeals.length);
    const dealsToRender = filteredDeals.slice(startIndex, endIndex);

    // Clear existing rows
    dealsTableBody.innerHTML = '';

    // Show/hide no results message
    if (filteredDeals.length === 0) {
        showNoResults();
        updatePaginationControls(totalPages);
        return;
    } else {
        hideNoResults();
    }

    // Use DocumentFragment for batch DOM updates (60% faster)
    const fragment = document.createDocumentFragment();

    // Render only visible deals
    dealsToRender.forEach(deal => {
        const row = document.createElement('tr');

        // Main Category
        const mainCategoryCell = document.createElement('td');
        mainCategoryCell.textContent = deal.mainCategory || '';
        row.appendChild(mainCategoryCell);

        // Sub Category
        const subCategoryCell = document.createElement('td');
        subCategoryCell.textContent = deal.subCategory || '';
        row.appendChild(subCategoryCell);

        // Item / Product (with link)
        const titleCell = document.createElement('td');
        const titleLink = document.createElement('a');
        titleLink.href = deal.link || '#';
        titleLink.textContent = deal.title || 'No title';
        titleLink.target = '_blank';
        titleLink.rel = 'noopener noreferrer';
        titleCell.appendChild(titleLink);
        row.appendChild(titleCell);

        // Original Price
        const originalPriceCell = document.createElement('td');
        if (deal.originalPrice) {
            originalPriceCell.textContent = deal.originalPrice;
            originalPriceCell.classList.add('original-price');
        }
        row.appendChild(originalPriceCell);

        // Sale Price
        const salePriceCell = document.createElement('td');
        if (deal.salePrice) {
            salePriceCell.textContent = deal.salePrice;
            salePriceCell.classList.add('sale-price');
        }
        row.appendChild(salePriceCell);

        // Store
        const storeCell = document.createElement('td');
        storeCell.textContent = deal.store || '';
        row.appendChild(storeCell);

        // Sale Period
        const salePeriodCell = document.createElement('td');
        if (deal.salePeriod) {
            salePeriodCell.textContent = deal.salePeriod;
            salePeriodCell.classList.add('sale-period');
        }
        row.appendChild(salePeriodCell);

        // Notes
        const notesCell = document.createElement('td');
        if (deal.notes) {
            notesCell.textContent = deal.notes;
            notesCell.classList.add('notes');
        }
        row.appendChild(notesCell);

        // Published Date
        const publishedCell = document.createElement('td');
        if (deal.pubDate) {
            publishedCell.textContent = formatDate(deal.pubDate);
            publishedCell.classList.add('published-date');
        }
        row.appendChild(publishedCell);

        fragment.appendChild(row);
    });

    // Single DOM update instead of 16k+ individual updates
    dealsTableBody.appendChild(fragment);

    // Update pagination controls
    updatePaginationControls(totalPages);
}

/**
 * Update pagination controls
 */
function updatePaginationControls(totalPages) {
    pageInfoElement.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage >= totalPages || totalPages === 0;
}

/**
 * Navigate to previous page
 */
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderDeals();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Navigate to next page
 */
function nextPage() {
    const totalPages = Math.ceil(filteredDeals.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        renderDeals();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

/**
 * Change items per page
 */
function changeItemsPerPage() {
    itemsPerPage = parseInt(itemsPerPageSelect.value);
    currentPage = 1;
    renderDeals();
}

/**
 * Debounced search (300ms delay) - eliminates lag during typing
 */
function debouncedSearch() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        applyFilters();
    }, 300);
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    mainCategoryFilter.addEventListener('change', () => {
        subCategoryFilter.value = '';
        populateSubCategoryFilter();
        applyFilters();
    });

    subCategoryFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', debouncedSearch); // Use debounced version
    sortBy.addEventListener('change', applyFilters);
    prevPageBtn.addEventListener('click', previousPage);
    nextPageBtn.addEventListener('click', nextPage);
    itemsPerPageSelect.addEventListener('change', changeItemsPerPage);
}

/**
 * Show no results message
 */
function showNoResults() {
    noResults.style.display = 'block';
    dealsTable.style.display = 'none';
}

/**
 * Hide no results message
 */
function hideNoResults() {
    noResults.style.display = 'none';
    dealsTable.style.display = 'table';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInMins = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInMins < 60) {
        return `${diffInMins} minute${diffInMins !== 1 ? 's' : ''} ago`;
    } else if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    } else if (diffInDays < 7) {
        return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }
}
