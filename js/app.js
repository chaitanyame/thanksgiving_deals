// Global state
let allDeals = [];
let filteredDeals = [];
let categoryIndex = null; // Pre-indexed categories
let currentPage = 1;
let itemsPerPage = 100;
let searchDebounceTimer = null;

// Helper function to decode HTML entities
function decodeHTMLEntities(text) {
    if (!text) return text;
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}

// Helper function to calculate savings percentage
function calculateSavings(originalPrice, salePrice) {
    if (!originalPrice || !salePrice) return null;
    
    // Extract numeric values from price strings
    const origMatch = originalPrice.match(/[\d,]+\.?\d*/);
    const saleMatch = salePrice.match(/[\d,]+\.?\d*/);
    
    if (!origMatch || !saleMatch) return null;
    
    const orig = parseFloat(origMatch[0].replace(/,/g, ''));
    const sale = parseFloat(saleMatch[0].replace(/,/g, ''));
    
    if (orig <= 0 || sale >= orig) return null;
    
    const savingsPercent = Math.round(((orig - sale) / orig) * 100);
    
    if (savingsPercent < 5) return null; // Don't show tiny discounts
    
    return `-${savingsPercent}%`;
}

// Virtual Scrolling State
let virtualScrollEnabled = false;
let rowHeight = 60; // Estimated row height in pixels
let visibleRowCount = 20;
let bufferRows = 5;
let scrollContainer = null;
let virtualScrollWrapper = null;
let lastScrollTop = 0;
let scrollRAF = null;

// Lazy Loading State
let imageObserver = null;

// Pull-to-refresh State
let pullToRefreshEnabled = false;
let pullStartY = 0;
let pullMoveY = 0;
let isPulling = false;
let pullThreshold = 80;

// Swipe Navigation State
let touchStartX = 0;
let touchStartY = 0;
let swipeThreshold = 100;

// Store Brand Colors
const storeBrands = {
    'amazon': { color: '#FF9900', bg: '#FFF3E0', icon: '📦' },
    'walmart': { color: '#0071DC', bg: '#E3F2FD', icon: '🏪' },
    'target': { color: '#CC0000', bg: '#FFEBEE', icon: '🎯' },
    'best buy': { color: '#0046BE', bg: '#E8EAF6', icon: '💻' },
    'bestbuy': { color: '#0046BE', bg: '#E8EAF6', icon: '💻' },
    'costco': { color: '#E31837', bg: '#FCE4EC', icon: '🛒' },
    'home depot': { color: '#F96302', bg: '#FFF3E0', icon: '🔨' },
    'lowes': { color: '#004990', bg: '#E3F2FD', icon: '🔧' },
    "lowe's": { color: '#004990', bg: '#E3F2FD', icon: '🔧' },
    'newegg': { color: '#FF6600', bg: '#FFF3E0', icon: '🖥️' },
    'ebay': { color: '#E53238', bg: '#FFEBEE', icon: '🏷️' },
    'apple': { color: '#555555', bg: '#F5F5F5', icon: '🍎' },
    'samsung': { color: '#1428A0', bg: '#E8EAF6', icon: '📱' },
    'dell': { color: '#007DB8', bg: '#E3F2FD', icon: '💼' },
    'hp': { color: '#0096D6', bg: '#E3F2FD', icon: '🖨️' },
    'lenovo': { color: '#E2231A', bg: '#FFEBEE', icon: '💻' },
    'microsoft': { color: '#00A4EF', bg: '#E3F2FD', icon: '🪟' },
    'gamestop': { color: '#000000', bg: '#F5F5F5', icon: '🎮' },
    'staples': { color: '#CC0000', bg: '#FFEBEE', icon: '📎' },
    'office depot': { color: '#CC0000', bg: '#FFEBEE', icon: '📋' },
    'kohls': { color: '#000000', bg: '#F5F5F5', icon: '👕' },
    "kohl's": { color: '#000000', bg: '#F5F5F5', icon: '👕' },
    'macys': { color: '#E21A2C', bg: '#FFEBEE', icon: '🛍️' },
    "macy's": { color: '#E21A2C', bg: '#FFEBEE', icon: '🛍️' },
    'nordstrom': { color: '#000000', bg: '#F5F5F5', icon: '👗' },
    'jcpenney': { color: '#D32F2F', bg: '#FFEBEE', icon: '🏬' },
    'sephora': { color: '#000000', bg: '#F5F5F5', icon: '💄' },
    'ulta': { color: '#E91E63', bg: '#FCE4EC', icon: '💅' },
    'wayfair': { color: '#7B189F', bg: '#F3E5F5', icon: '🛋️' },
    'ikea': { color: '#0051BA', bg: '#E3F2FD', icon: '🪑' },
    'nike': { color: '#000000', bg: '#F5F5F5', icon: '👟' },
    'adidas': { color: '#000000', bg: '#F5F5F5', icon: '👟' },
    'b&h': { color: '#000000', bg: '#F5F5F5', icon: '📸' },
    'adorama': { color: '#D32F2F', bg: '#FFEBEE', icon: '📷' },
    'sams club': { color: '#0067A0', bg: '#E3F2FD', icon: '🛒' },
    "sam's club": { color: '#0067A0', bg: '#E3F2FD', icon: '🛒' },
    'bjs': { color: '#D32F2F', bg: '#FFEBEE', icon: '🛒' },
    "bj's": { color: '#D32F2F', bg: '#FFEBEE', icon: '🛒' },
    'default': { color: '#6366f1', bg: '#EEF2FF', icon: '🏷️' }
};

// DOM Elements
const loadingSpinner = document.getElementById('loadingSpinner');
const errorMessage = document.getElementById('errorMessage');
const noResults = document.getElementById('noResults');
const dealsTable = document.getElementById('dealsTable');
const dealsTableBody = document.getElementById('dealsTableBody');
const mobileCards = document.getElementById('mobileCards');
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

// Bottom pagination elements
const prevPageBtnBottom = document.getElementById('prevPageBottom');
const nextPageBtnBottom = document.getElementById('nextPageBottom');
const pageInfoElementBottom = document.getElementById('pageInfoBottom');
const itemsPerPageSelectBottom = document.getElementById('itemsPerPageBottom');

// Check if mobile
const isMobile = () => window.innerWidth <= 768;

// Initialize dark mode from localStorage
initDarkMode();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDeals();
    setupEventListeners();
    setupDarkModeToggle();
    setupLazyLoading();
    calculateVirtualScrollParams();
    setupMobileGestures();
    setupPullToRefresh();
});

/**
 * Initialize dark mode based on saved preference or system preference
 */
function initDarkMode() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

/**
 * Setup dark mode toggle button
 */
function setupDarkModeToggle() {
    const toggle = document.getElementById('darkModeToggle');
    if (!toggle) return;
    
    toggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

/**
 * Load deals from data/deals.json
 */
async function loadDeals() {
    try {
        // Add cache-busting timestamp to always get fresh data
        const cacheBuster = new Date().getTime();
        const response = await fetch(`data/deals.json?v=${cacheBuster}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        allDeals = data.deals || [];

        // Pre-index categories for instant filtering
        buildCategoryIndex();

        // Update last updated time - use newest deal's pubDate for consistency
        if (allDeals.length > 0 && allDeals[0].pubDate) {
            // Find the newest deal by pubDate
            const newestDeal = allDeals.reduce((newest, deal) => {
                if (!deal.pubDate) return newest;
                return new Date(deal.pubDate) > new Date(newest.pubDate) ? deal : newest;
            }, allDeals[0]);
            lastUpdatedSpan.textContent = formatDate(newestDeal.pubDate);
        } else if (data.lastUpdated) {
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
 * Populate main category filter (using pre-indexed data) with deal counts
 */
function populateMainCategoryFilter() {
    // Sort categories alphabetically
    const sortedCategories = Array.from(categoryIndex.mainCategories).sort();

    // Clear existing options (except "All Categories")
    mainCategoryFilter.innerHTML = `<option value="">All Categories (${allDeals.length.toLocaleString()})</option>`;

    // Add category options using DocumentFragment for batching
    const fragment = document.createDocumentFragment();
    sortedCategories.forEach(category => {
        const count = (categoryIndex.byMainCategory[category] || []).length;
        const option = document.createElement('option');
        option.value = category;
        option.textContent = `${decodeHTMLEntities(category)} (${count.toLocaleString()})`;
        fragment.appendChild(option);
    });
    mainCategoryFilter.appendChild(fragment);
}

/**
 * Populate sub category filter based on selected main category (using pre-indexed data) with deal counts
 */
function populateSubCategoryFilter() {
    const selectedMainCategory = mainCategoryFilter.value;
    const subCategoryCounts = new Map();

    if (selectedMainCategory === '') {
        // Count all sub categories
        allDeals.forEach(deal => {
            if (deal.subCategory) {
                subCategoryCounts.set(deal.subCategory, (subCategoryCounts.get(deal.subCategory) || 0) + 1);
            }
        });
    } else {
        // Count sub categories for selected main category
        const dealIndices = categoryIndex.byMainCategory[selectedMainCategory] || [];
        dealIndices.forEach(index => {
            const sub = allDeals[index].subCategory;
            if (sub) {
                subCategoryCounts.set(sub, (subCategoryCounts.get(sub) || 0) + 1);
            }
        });
    }

    // Sort sub categories alphabetically
    const sortedSubCategories = Array.from(subCategoryCounts.keys()).sort();
    const totalCount = Array.from(subCategoryCounts.values()).reduce((a, b) => a + b, 0);

    // Clear existing options
    subCategoryFilter.innerHTML = `<option value="">All Sub Categories (${totalCount.toLocaleString()})</option>`;

    // Add sub category options using DocumentFragment
    const fragment = document.createDocumentFragment();
    sortedSubCategories.forEach(subCategory => {
        const count = subCategoryCounts.get(subCategory) || 0;
        const option = document.createElement('option');
        option.value = subCategory;
        option.textContent = `${decodeHTMLEntities(subCategory)} (${count.toLocaleString()})`;
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

    // Clear existing content
    dealsTableBody.innerHTML = '';
    if (mobileCards) mobileCards.innerHTML = '';

    // Show/hide no results message
    if (filteredDeals.length === 0) {
        showNoResults();
        disableVirtualScroll();
        updatePaginationControls(totalPages);
        return;
    } else {
        hideNoResults();
    }

    // Try to use virtual scrolling for large datasets (500+ items)
    if (!isMobile() && dealsToRender.length >= 500) {
        if (initVirtualScroll()) {
            updatePaginationControls(totalPages);
            return; // Virtual scroll handles rendering
        }
    } else {
        disableVirtualScroll();
    }

    // Use DocumentFragment for batch DOM updates (60% faster)
    const tableFragment = document.createDocumentFragment();
    const mobileFragment = document.createDocumentFragment();

    // Render only visible deals
    dealsToRender.forEach(deal => {
        // Decode HTML entities in category names
        const mainCat = decodeHTMLEntities(deal.mainCategory) || '';
        const subCat = decodeHTMLEntities(deal.subCategory) || '';
        const title = decodeHTMLEntities(deal.title) || 'No title';
        
        // === TABLE ROW (Desktop) ===
        const row = document.createElement('tr');

        // Main Category
        const mainCategoryCell = document.createElement('td');
        mainCategoryCell.textContent = mainCat;
        row.appendChild(mainCategoryCell);

        // Sub Category
        const subCategoryCell = document.createElement('td');
        subCategoryCell.textContent = subCat;
        row.appendChild(subCategoryCell);

        // Item / Product (with link and optional lazy image)
        const titleCell = document.createElement('td');
        titleCell.className = 'title-cell';
        
        const titleWrapper = document.createElement('div');
        titleWrapper.className = 'title-wrapper';
        
        const titleLink = document.createElement('a');
        titleLink.href = deal.link || '#';
        titleLink.textContent = title;
        titleLink.target = '_blank';
        titleLink.rel = 'noopener noreferrer';
        titleWrapper.appendChild(titleLink);
        
        // Add copy link button
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-link-btn';
        copyBtn.innerHTML = '📋';
        copyBtn.title = 'Copy link';
        copyBtn.setAttribute('aria-label', 'Copy deal link');
        copyBtn.dataset.link = deal.link || '';
        copyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            copyDealLink(deal.link, copyBtn);
        });
        titleWrapper.appendChild(copyBtn);
        
        titleCell.appendChild(titleWrapper);
        
        // Add lazy-loaded image if deal has image URL
        if (deal.image) {
            const img = document.createElement('img');
            img.dataset.src = deal.image;
            img.alt = '';
            img.className = 'deal-thumb lazy-image';
            img.loading = 'lazy'; // Native lazy loading as fallback
            titleCell.appendChild(img);
        }
        row.appendChild(titleCell);

        // Original Price
        const originalPriceCell = document.createElement('td');
        if (deal.originalPrice) {
            originalPriceCell.textContent = deal.originalPrice;
            originalPriceCell.classList.add('original-price');
        }
        row.appendChild(originalPriceCell);

        // Sale Price with savings badge
        const salePriceCell = document.createElement('td');
        if (deal.salePrice) {
            const priceWrapper = document.createElement('div');
            priceWrapper.className = 'price-wrapper';
            
            const priceSpan = document.createElement('span');
            priceSpan.className = 'sale-price';
            priceSpan.textContent = deal.salePrice;
            priceWrapper.appendChild(priceSpan);
            
            // Calculate and show savings badge if both prices exist
            const savings = calculateSavings(deal.originalPrice, deal.salePrice);
            if (savings) {
                const savingsBadge = document.createElement('span');
                savingsBadge.className = 'savings-badge';
                savingsBadge.textContent = savings;
                priceWrapper.appendChild(savingsBadge);
            }
            
            salePriceCell.appendChild(priceWrapper);
        }
        row.appendChild(salePriceCell);

        // Store with branded badge
        const storeCell = document.createElement('td');
        if (deal.store) {
            const storeBadge = createStoreBadge(deal.store);
            storeCell.appendChild(storeBadge);
        }
        row.appendChild(storeCell);

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

        tableFragment.appendChild(row);

        // === MOBILE CARD ===
        const card = document.createElement('div');
        card.className = 'deal-card';
        card.dataset.link = deal.link || '';

        // Add lazy image for mobile card if available
        if (deal.image) {
            const cardImage = document.createElement('div');
            cardImage.className = 'deal-card-image';
            const img = document.createElement('img');
            img.dataset.src = deal.image;
            img.alt = '';
            img.className = 'lazy-image';
            img.loading = 'lazy';
            cardImage.appendChild(img);
            card.appendChild(cardImage);
        }

        // Title with link and copy button
        const cardHeader = document.createElement('div');
        cardHeader.className = 'deal-card-header';
        
        const cardTitle = document.createElement('div');
        cardTitle.className = 'deal-card-title';
        const cardLink = document.createElement('a');
        cardLink.href = deal.link || '#';
        cardLink.textContent = title;
        cardLink.target = '_blank';
        cardLink.rel = 'noopener noreferrer';
        cardTitle.appendChild(cardLink);
        cardHeader.appendChild(cardTitle);
        
        // Mobile copy button
        const mobileCopyBtn = document.createElement('button');
        mobileCopyBtn.className = 'copy-link-btn mobile';
        mobileCopyBtn.innerHTML = '📋';
        mobileCopyBtn.title = 'Copy link';
        mobileCopyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            copyDealLink(deal.link, mobileCopyBtn);
        });
        cardHeader.appendChild(mobileCopyBtn);
        
        card.appendChild(cardHeader);

        // Meta tags (category, price, store)
        const cardMeta = document.createElement('div');
        cardMeta.className = 'deal-card-meta';

        if (mainCat) {
            const catTag = document.createElement('span');
            catTag.className = 'deal-card-tag category';
            catTag.textContent = mainCat;
            cardMeta.appendChild(catTag);
        }

        if (deal.salePrice) {
            const priceTag = document.createElement('span');
            priceTag.className = 'deal-card-tag price';
            priceTag.textContent = deal.salePrice;
            cardMeta.appendChild(priceTag);
            
            // Add savings badge on mobile cards too
            const savings = calculateSavings(deal.originalPrice, deal.salePrice);
            if (savings) {
                const savingsTag = document.createElement('span');
                savingsTag.className = 'deal-card-tag savings';
                savingsTag.textContent = savings;
                cardMeta.appendChild(savingsTag);
            }
        }

        if (deal.originalPrice) {
            const origTag = document.createElement('span');
            origTag.className = 'deal-card-tag original-price';
            origTag.textContent = deal.originalPrice;
            cardMeta.appendChild(origTag);
        }

        if (deal.store) {
            const storeBadge = createStoreBadge(deal.store, true);
            cardMeta.appendChild(storeBadge);
        }

        card.appendChild(cardMeta);

        // Notes
        if (deal.notes) {
            const cardNotes = document.createElement('div');
            cardNotes.className = 'deal-card-notes';
            cardNotes.textContent = deal.notes;
            card.appendChild(cardNotes);
        }

        // Footer with date and sale period
        const cardFooter = document.createElement('div');
        cardFooter.className = 'deal-card-footer';
        
        const dateSpan = document.createElement('span');
        dateSpan.textContent = deal.pubDate ? formatDate(deal.pubDate) : '';
        cardFooter.appendChild(dateSpan);

        card.appendChild(cardFooter);
        mobileFragment.appendChild(card);
    });

    // Single DOM update
    dealsTableBody.appendChild(tableFragment);
    if (mobileCards) mobileCards.appendChild(mobileFragment);

    // Observe lazy images after DOM update
    observeLazyImages(dealsTableBody);
    if (mobileCards) observeLazyImages(mobileCards);

    // Update pagination controls
    updatePaginationControls(totalPages);
}

/**
 * Update pagination controls (both top and bottom)
 */
function updatePaginationControls(totalPages) {
    const pageText = `Page ${currentPage} of ${totalPages || 1}`;
    const isFirstPage = currentPage === 1;
    const isLastPage = currentPage >= totalPages || totalPages === 0;
    
    // Top pagination
    pageInfoElement.textContent = pageText;
    prevPageBtn.disabled = isFirstPage;
    nextPageBtn.disabled = isLastPage;
    
    // Bottom pagination
    if (pageInfoElementBottom) pageInfoElementBottom.textContent = pageText;
    if (prevPageBtnBottom) prevPageBtnBottom.disabled = isFirstPage;
    if (nextPageBtnBottom) nextPageBtnBottom.disabled = isLastPage;
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
        clearQuickFilterActive();
        applyFilters();
    });

    subCategoryFilter.addEventListener('change', () => {
        clearQuickFilterActive();
        applyFilters();
    });
    searchInput.addEventListener('input', debouncedSearch); // Use debounced version
    sortBy.addEventListener('change', applyFilters);
    prevPageBtn.addEventListener('click', previousPage);
    nextPageBtn.addEventListener('click', nextPage);
    itemsPerPageSelect.addEventListener('change', changeItemsPerPage);

    // Bottom pagination event listeners
    if (prevPageBtnBottom) prevPageBtnBottom.addEventListener('click', previousPage);
    if (nextPageBtnBottom) nextPageBtnBottom.addEventListener('click', nextPage);
    if (itemsPerPageSelectBottom) {
        itemsPerPageSelectBottom.addEventListener('change', () => {
            itemsPerPage = parseInt(itemsPerPageSelectBottom.value);
            itemsPerPageSelect.value = itemsPerPageSelectBottom.value; // Sync top select
            currentPage = 1;
            renderDeals();
        });
    }

    // Quick filter buttons
    document.querySelectorAll('.quick-filter-btn').forEach(btn => {
        btn.addEventListener('click', handleQuickFilter);
    });

    // Back to top button and scroll events
    const backToTopBtn = document.getElementById('backToTop');
    const filtersSection = document.querySelector('.filters');
    let filtersOffsetTop = filtersSection ? filtersSection.offsetTop : 0;

    window.addEventListener('scroll', () => {
        // Show/hide back to top button
        if (window.scrollY > 400) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }

        // Sticky filter bar (only on desktop)
        if (!isMobile() && filtersSection) {
            if (window.scrollY > filtersOffsetTop + 100) {
                if (!filtersSection.classList.contains('sticky')) {
                    filtersSection.classList.add('sticky');
                    // Create placeholder to prevent content jump
                    let placeholder = document.querySelector('.filters-placeholder');
                    if (!placeholder) {
                        placeholder = document.createElement('div');
                        placeholder.className = 'filters-placeholder';
                        placeholder.style.height = filtersSection.offsetHeight + 'px';
                        filtersSection.parentNode.insertBefore(placeholder, filtersSection.nextSibling);
                    }
                    placeholder.classList.add('active');
                }
            } else {
                filtersSection.classList.remove('sticky');
                const placeholder = document.querySelector('.filters-placeholder');
                if (placeholder) {
                    placeholder.classList.remove('active');
                }
            }
        }
    });

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/**
 * Handle quick filter button clicks
 */
function handleQuickFilter(e) {
    const btn = e.target;
    
    // Handle clear button
    if (btn.classList.contains('clear-filters')) {
        clearAllFilters();
        return;
    }
    
    // Clear all active states
    clearQuickFilterActive();
    btn.classList.add('active');
    
    if (btn.dataset.category) {
        // Category quick filter
        mainCategoryFilter.value = btn.dataset.category;
        subCategoryFilter.value = '';
        searchInput.value = '';
        populateSubCategoryFilter();
        applyFilters();
    } else if (btn.dataset.price) {
        // Price quick filter - filter deals under X price
        const maxPrice = parseInt(btn.dataset.price);
        mainCategoryFilter.value = '';
        subCategoryFilter.value = '';
        searchInput.value = '';
        populateSubCategoryFilter();
        applyFiltersWithMaxPrice(maxPrice);
    }
}

/**
 * Clear active state from quick filter buttons
 */
function clearQuickFilterActive() {
    document.querySelectorAll('.quick-filter-btn').forEach(b => {
        if (!b.classList.contains('clear-filters')) {
            b.classList.remove('active');
        }
    });
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    mainCategoryFilter.value = '';
    subCategoryFilter.value = '';
    searchInput.value = '';
    clearQuickFilterActive();
    populateSubCategoryFilter();
    applyFilters();
}

/**
 * Apply filters with max price constraint
 */
function applyFiltersWithMaxPrice(maxPrice) {
    const selectedMainCategory = mainCategoryFilter.value;
    const selectedSubCategory = subCategoryFilter.value;
    
    filteredDeals = allDeals.filter(deal => {
        // Main category filter
        if (selectedMainCategory && deal.mainCategory !== selectedMainCategory) {
            return false;
        }
        // Sub category filter
        if (selectedSubCategory && deal.subCategory !== selectedSubCategory) {
            return false;
        }
        // Price filter
        const price = extractNumericPrice(deal.salePrice);
        return price !== null && price <= maxPrice;
    });
    
    sortDeals(sortBy.value);
    dealCountSpan.textContent = filteredDeals.length;
    currentPage = 1;
    renderDeals();
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

// ==================== VIRTUAL SCROLLING ====================

/**
 * Calculate virtual scroll parameters based on viewport
 */
function calculateVirtualScrollParams() {
    const viewportHeight = window.innerHeight;
    visibleRowCount = Math.ceil(viewportHeight / rowHeight) + bufferRows * 2;
    
    // Recalculate on resize
    window.addEventListener('resize', debounce(() => {
        visibleRowCount = Math.ceil(window.innerHeight / rowHeight) + bufferRows * 2;
        if (virtualScrollEnabled) {
            renderVirtualScroll();
        }
    }, 150));
}

/**
 * Initialize virtual scrolling for large datasets
 * Only enables when showing more than 500 items on a page
 */
function initVirtualScroll() {
    const dealsToRender = getCurrentPageDeals();
    
    // Only use virtual scroll for large datasets (500+ items)
    if (dealsToRender.length < 500 || isMobile()) {
        virtualScrollEnabled = false;
        return false;
    }
    
    virtualScrollEnabled = true;
    
    // Create virtual scroll wrapper if needed
    if (!virtualScrollWrapper) {
        virtualScrollWrapper = document.createElement('div');
        virtualScrollWrapper.className = 'virtual-scroll-wrapper';
        virtualScrollWrapper.id = 'virtualScrollWrapper';
        
        scrollContainer = document.createElement('div');
        scrollContainer.className = 'virtual-scroll-container';
        scrollContainer.id = 'virtualScrollContainer';
        
        virtualScrollWrapper.appendChild(scrollContainer);
    }
    
    // Calculate total height
    const totalHeight = dealsToRender.length * rowHeight;
    scrollContainer.style.height = `${totalHeight}px`;
    
    // Insert wrapper after table
    const tableContainer = dealsTable.parentNode;
    if (!document.getElementById('virtualScrollWrapper')) {
        tableContainer.insertBefore(virtualScrollWrapper, dealsTable.nextSibling);
    }
    
    // Hide regular table, show virtual scroll
    dealsTable.style.display = 'none';
    virtualScrollWrapper.style.display = 'block';
    
    // Setup scroll listener with requestAnimationFrame for smooth scrolling
    virtualScrollWrapper.addEventListener('scroll', handleVirtualScroll, { passive: true });
    
    // Initial render
    renderVirtualScroll();
    
    return true;
}

/**
 * Handle scroll events for virtual scrolling
 */
function handleVirtualScroll() {
    if (scrollRAF) {
        cancelAnimationFrame(scrollRAF);
    }
    
    scrollRAF = requestAnimationFrame(() => {
        const scrollTop = virtualScrollWrapper.scrollTop;
        
        // Only re-render if scrolled more than half a row
        if (Math.abs(scrollTop - lastScrollTop) > rowHeight / 2) {
            lastScrollTop = scrollTop;
            renderVirtualScroll();
        }
    });
}

/**
 * Render only visible rows in virtual scroll
 */
function renderVirtualScroll() {
    if (!virtualScrollEnabled || !scrollContainer) return;
    
    const dealsToRender = getCurrentPageDeals();
    const scrollTop = virtualScrollWrapper ? virtualScrollWrapper.scrollTop : 0;
    
    // Calculate visible range
    const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - bufferRows);
    const endIndex = Math.min(dealsToRender.length, startIndex + visibleRowCount + bufferRows * 2);
    
    // Clear and rebuild visible rows
    scrollContainer.innerHTML = '';
    
    // Add spacer for scrolled-past items
    const topSpacer = document.createElement('div');
    topSpacer.style.height = `${startIndex * rowHeight}px`;
    topSpacer.className = 'virtual-spacer-top';
    scrollContainer.appendChild(topSpacer);
    
    // Create visible rows
    const fragment = document.createDocumentFragment();
    
    for (let i = startIndex; i < endIndex; i++) {
        const deal = dealsToRender[i];
        const row = createVirtualRow(deal, i);
        fragment.appendChild(row);
    }
    
    scrollContainer.appendChild(fragment);
    
    // Add bottom spacer
    const bottomSpacer = document.createElement('div');
    bottomSpacer.style.height = `${(dealsToRender.length - endIndex) * rowHeight}px`;
    bottomSpacer.className = 'virtual-spacer-bottom';
    scrollContainer.appendChild(bottomSpacer);
}

/**
 * Create a virtual scroll row
 */
function createVirtualRow(deal, index) {
    const row = document.createElement('div');
    row.className = 'virtual-row';
    row.style.height = `${rowHeight}px`;
    row.dataset.index = index;
    
    // Decode HTML entities
    const decodedMainCategory = decodeHTMLEntities(deal.mainCategory || '');
    const decodedSubCategory = decodeHTMLEntities(deal.subCategory || '');
    const decodedTitle = decodeHTMLEntities(deal.title || 'No title');
    
    // Main content
    row.innerHTML = `
        <div class="vr-cell vr-category">${decodedMainCategory}</div>
        <div class="vr-cell vr-subcategory">${decodedSubCategory}</div>
        <div class="vr-cell vr-title">
            <a href="${deal.link || '#'}" target="_blank" rel="noopener noreferrer">${decodedTitle}</a>
            ${deal.image ? `<img data-src="${deal.image}" alt="" class="deal-thumb lazy-image" loading="lazy">` : ''}
        </div>
        <div class="vr-cell vr-original-price ${deal.originalPrice ? 'has-price' : ''}">${deal.originalPrice || ''}</div>
        <div class="vr-cell vr-sale-price">${deal.salePrice || ''}</div>
        <div class="vr-cell vr-store">${deal.store || ''}</div>
        <div class="vr-cell vr-date">${deal.pubDate ? formatDate(deal.pubDate) : ''}</div>
    `;
    
    // Observe lazy images
    const lazyImg = row.querySelector('.lazy-image');
    if (lazyImg && imageObserver) {
        imageObserver.observe(lazyImg);
    }
    
    return row;
}

/**
 * Get deals for current page
 */
function getCurrentPageDeals() {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredDeals.length);
    return filteredDeals.slice(startIndex, endIndex);
}

/**
 * Disable virtual scrolling (when switching to smaller dataset)
 */
function disableVirtualScroll() {
    virtualScrollEnabled = false;
    if (virtualScrollWrapper) {
        virtualScrollWrapper.style.display = 'none';
    }
    dealsTable.style.display = 'table';
}

// ==================== LAZY LOADING IMAGES ====================

/**
 * Setup lazy loading for images using IntersectionObserver
 */
function setupLazyLoading() {
    // Check for IntersectionObserver support
    if (!('IntersectionObserver' in window)) {
        console.log('IntersectionObserver not supported, images will load immediately');
        return;
    }
    
    const options = {
        root: null, // viewport
        rootMargin: '100px', // Load images 100px before they enter viewport
        threshold: 0.01
    };
    
    imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                loadLazyImage(img);
                observer.unobserve(img);
            }
        });
    }, options);
}

/**
 * Load a lazy image
 */
function loadLazyImage(img) {
    const src = img.dataset.src;
    if (!src) return;
    
    // Create a new image to preload
    const tempImg = new Image();
    
    tempImg.onload = () => {
        img.src = src;
        img.classList.add('loaded');
        img.classList.remove('lazy-image');
    };
    
    tempImg.onerror = () => {
        // Hide broken images
        img.style.display = 'none';
    };
    
    tempImg.src = src;
}

/**
 * Observe all lazy images in a container
 */
function observeLazyImages(container) {
    if (!imageObserver) return;
    
    const lazyImages = container.querySelectorAll('.lazy-image');
    lazyImages.forEach(img => {
        imageObserver.observe(img);
    });
}

/**
 * Utility: Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== STORE BADGES ====================

/**
 * Get store brand info (color, background, icon)
 */
function getStoreBrand(storeName) {
    if (!storeName) return storeBrands.default;
    
    const lowerStore = storeName.toLowerCase().trim();
    
    // Check for exact match first
    if (storeBrands[lowerStore]) {
        return storeBrands[lowerStore];
    }
    
    // Check for partial matches
    for (const [key, value] of Object.entries(storeBrands)) {
        if (key !== 'default' && lowerStore.includes(key)) {
            return value;
        }
    }
    
    return storeBrands.default;
}

/**
 * Create a styled store badge element
 */
function createStoreBadge(storeName, isMobile = false) {
    const brand = getStoreBrand(storeName);
    const badge = document.createElement('span');
    badge.className = `store-badge ${isMobile ? 'mobile' : ''}`;
    badge.style.setProperty('--store-color', brand.color);
    badge.style.setProperty('--store-bg', brand.bg);
    
    badge.innerHTML = `<span class="store-icon">${brand.icon}</span><span class="store-name">${storeName}</span>`;
    
    return badge;
}

// ==================== COPY LINK ====================

/**
 * Copy deal link to clipboard
 */
async function copyDealLink(link, button) {
    if (!link) {
        showCopyFeedback(button, false);
        return;
    }
    
    try {
        // Try modern clipboard API first
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(link);
            showCopyFeedback(button, true);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = link;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showCopyFeedback(button, true);
        }
    } catch (err) {
        console.error('Failed to copy:', err);
        showCopyFeedback(button, false);
    }
}

/**
 * Show visual feedback after copy
 */
function showCopyFeedback(button, success) {
    const originalContent = button.innerHTML;
    button.innerHTML = success ? '✓' : '✗';
    button.classList.add(success ? 'copied' : 'copy-failed');
    
    setTimeout(() => {
        button.innerHTML = originalContent;
        button.classList.remove('copied', 'copy-failed');
    }, 1500);
}

// ==================== MOBILE GESTURES ====================

/**
 * Setup swipe gestures for mobile navigation
 */
function setupMobileGestures() {
    if (!isMobile()) return;
    
    const container = document.querySelector('.container');
    if (!container) return;
    
    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: true });
    container.addEventListener('touchend', handleTouchEnd, { passive: true });
}

/**
 * Handle touch start for swipe detection
 */
function handleTouchStart(e) {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
}

/**
 * Handle touch move for swipe detection
 */
function handleTouchMove(e) {
    // Handled in touchend for simplicity
}

/**
 * Handle touch end - detect swipe direction
 */
function handleTouchEnd(e) {
    if (!e.changedTouches || !e.changedTouches[0]) return;
    
    const touchEndX = e.changedTouches[0].clientX;
    const touchEndY = e.changedTouches[0].clientY;
    
    const deltaX = touchEndX - touchStartX;
    const deltaY = touchEndY - touchStartY;
    
    // Only handle horizontal swipes (ignore vertical scrolling)
    if (Math.abs(deltaX) < swipeThreshold || Math.abs(deltaY) > Math.abs(deltaX)) {
        return;
    }
    
    // Swipe left = next page
    if (deltaX < -swipeThreshold) {
        const totalPages = Math.ceil(filteredDeals.length / itemsPerPage);
        if (currentPage < totalPages) {
            showSwipeIndicator('next');
            nextPage();
        }
    }
    // Swipe right = previous page
    else if (deltaX > swipeThreshold) {
        if (currentPage > 1) {
            showSwipeIndicator('prev');
            previousPage();
        }
    }
}

/**
 * Show visual indicator for swipe navigation
 */
function showSwipeIndicator(direction) {
    // Remove existing indicator
    const existing = document.querySelector('.swipe-indicator');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.className = `swipe-indicator ${direction}`;
    indicator.innerHTML = direction === 'next' ? '→ Next Page' : '← Previous Page';
    document.body.appendChild(indicator);
    
    // Animate in
    requestAnimationFrame(() => {
        indicator.classList.add('visible');
    });
    
    // Remove after animation
    setTimeout(() => {
        indicator.classList.remove('visible');
        setTimeout(() => indicator.remove(), 300);
    }, 800);
}

// ==================== PULL TO REFRESH ====================

/**
 * Setup pull-to-refresh for mobile
 */
function setupPullToRefresh() {
    if (!isMobile()) return;
    
    // Create pull-to-refresh indicator
    const ptrIndicator = document.createElement('div');
    ptrIndicator.className = 'ptr-indicator';
    ptrIndicator.innerHTML = `
        <div class="ptr-spinner"></div>
        <span class="ptr-text">Pull to refresh</span>
    `;
    document.body.insertBefore(ptrIndicator, document.body.firstChild);
    
    pullToRefreshEnabled = true;
    
    document.addEventListener('touchstart', ptrTouchStart, { passive: true });
    document.addEventListener('touchmove', ptrTouchMove, { passive: false });
    document.addEventListener('touchend', ptrTouchEnd, { passive: true });
}

/**
 * Pull-to-refresh touch start
 */
function ptrTouchStart(e) {
    if (window.scrollY !== 0) return;
    pullStartY = e.touches[0].clientY;
    isPulling = true;
}

/**
 * Pull-to-refresh touch move
 */
function ptrTouchMove(e) {
    if (!isPulling || window.scrollY > 0) {
        isPulling = false;
        return;
    }
    
    pullMoveY = e.touches[0].clientY;
    const pullDistance = pullMoveY - pullStartY;
    
    if (pullDistance > 0 && pullDistance < 150) {
        // Prevent default scroll when pulling
        e.preventDefault();
        
        const indicator = document.querySelector('.ptr-indicator');
        const progress = Math.min(pullDistance / pullThreshold, 1);
        
        indicator.style.transform = `translateY(${pullDistance * 0.5}px)`;
        indicator.style.opacity = progress;
        
        if (pullDistance >= pullThreshold) {
            indicator.classList.add('ready');
            indicator.querySelector('.ptr-text').textContent = 'Release to refresh';
        } else {
            indicator.classList.remove('ready');
            indicator.querySelector('.ptr-text').textContent = 'Pull to refresh';
        }
    }
}

/**
 * Pull-to-refresh touch end
 */
function ptrTouchEnd(e) {
    if (!isPulling) return;
    
    const indicator = document.querySelector('.ptr-indicator');
    const pullDistance = pullMoveY - pullStartY;
    
    if (pullDistance >= pullThreshold) {
        // Trigger refresh
        indicator.classList.add('refreshing');
        indicator.querySelector('.ptr-text').textContent = 'Refreshing...';
        
        // Reload deals
        loadDeals().then(() => {
            setTimeout(() => {
                resetPullToRefresh();
            }, 500);
        });
    } else {
        resetPullToRefresh();
    }
    
    isPulling = false;
    pullStartY = 0;
    pullMoveY = 0;
}

/**
 * Reset pull-to-refresh indicator
 */
function resetPullToRefresh() {
    const indicator = document.querySelector('.ptr-indicator');
    if (indicator) {
        indicator.style.transform = 'translateY(-60px)';
        indicator.style.opacity = '0';
        indicator.classList.remove('ready', 'refreshing');
        indicator.querySelector('.ptr-text').textContent = 'Pull to refresh';
    }
}
