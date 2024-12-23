let currentPage = 1;
const productList = document.getElementById('product-list');
const loadingIndicator = document.getElementById('loading');
const loadMoreButton = document.getElementById('load-more');

// Function to fetch products from the API
function fetchProducts(page) {
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';  // Show loading indicator
    }

    fetch(`http://localhost:8000/api/allproducts/?page=${page}`)
    .then(response => response.json())
    .then(data => {
        data.results.forEach(product => {
            const productDiv = document.createElement('div');
            productDiv.classList.add('product');
            
            // Dynamically set the image path
            const productImage = document.createElement('img');
            const imagePath = `/static/images/${product.product_name_en}.jpg`;

            // Check if the image exists; if not, use the default image
            productImage.src = imageExists(imagePath) ? imagePath : '/static/images/drug.png'; 
            productImage.alt = product.product_name_en;

            productDiv.innerHTML = `
                <h3>${product.product_name_en}</h3>
                <p>Product Code: ${product.product_code}</p>
                <p>Price: $${parseFloat(product.sell_price).toFixed(2)}</p>
                <p>Group ID: ${parseFloat(product.group_id).toFixed(0)}</p>
            `;
            productDiv.prepend(productImage);  // Add image at the top
            productList.appendChild(productDiv);
        });

        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';  // Hide loading indicator after data is loaded
        }

        // Show the "Load More" button if more products are available
        if (data.next) {
            loadMoreButton.style.display = 'block';  // Show "Load More" button
        } else {
            loadMoreButton.style.display = 'none';  // Hide if no more products
        }
    })
    .catch(error => {
        console.error('Error fetching products:', error);
    });
}

// Function to check if an image exists
function imageExists(imagePath) {
    const xhr = new XMLHttpRequest();
    xhr.open('HEAD', imagePath, false);  // Synchronous request
    xhr.send();
    return xhr.status !== 404;  // Returns true if the image exists
}

// Load more products when the "Load More" button is clicked
document.addEventListener("DOMContentLoaded", function() {
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', function() {
            // Handle the button click
            console.log("Load more clicked!");
            currentPage++;
            fetchProducts(currentPage);  // Load more products
        });
    } else {
        console.error('Load more button not found!');
    }
});

// Initial fetch of products
fetchProducts(currentPage);
