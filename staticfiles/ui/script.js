let currentPage = 1;
const productList = document.getElementById('product-list');
const loadingIndicator = document.getElementById('loading');
const loadMoreButton = document.getElementById('load-more');

// Helper function to set loading state
function setLoading(isLoading) {
    if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
    if (loadMoreButton) {
        loadMoreButton.disabled = isLoading;
    }
}

// Function to check if an image exists (asynchronous)
async function imageExists(imagePath) {
    try {
        const response = await fetch(imagePath, { method: 'HEAD' });
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Function to fetch products from the API
async function fetchProducts(page) {
    setLoading(true); // Show loading indicator and disable button
////////////////////////////////////////////////
    try {
        const response = await fetch(`http://localhost:8000/api/product/allproducts/?page=${page}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();

        // Create product cards
        for (const product of data.results) {
            const productDiv = document.createElement('div');
            productDiv.classList.add('product');

            const productImage = document.createElement('img');
            const imagePath = `/static/images/${product.product_name_en}.jpg`;

            // Use default image if the product image doesn't exist
            productImage.src = (await imageExists(imagePath)) ? imagePath : '/static/images/drug.png';
            productImage.alt = product.product_name_en;

            productDiv.innerHTML = `
                <h3>${product.product_name_en}</h3>
                <p>Product Code: ${product.product_code}</p>
                <p>Price: $${parseFloat(product.sell_price).toFixed(2)}</p>
                <p>Group ID: ${parseFloat(product.group_id).toFixed(0)}</p>
            `;
            productDiv.prepend(productImage); // Add image at the top
            productList.appendChild(productDiv);
        }

        // Show/hide "Load More" button based on pagination
        if (loadMoreButton) {
            loadMoreButton.style.display = data.next ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error fetching products:', error);
        // Display error message in the DOM
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error';
        errorMessage.textContent = 'Failed to load products. Please try again later.';
        productList.appendChild(errorMessage);
    } finally {
        setLoading(false); // Hide loading indicator and re-enable button
    }
}

// Event listener for "Load More" button
document.addEventListener('DOMContentLoaded', () => {
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', () => {
            currentPage++;
            fetchProducts(currentPage);
        });
    } else {
        console.error('Load more button not found!');
    }

    // Initial fetch of products
    fetchProducts(currentPage);
});