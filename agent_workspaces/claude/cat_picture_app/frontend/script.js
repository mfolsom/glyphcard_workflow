// Cat Picture App - Main JavaScript functionality
// This is a basic implementation for the project kickoff phase

document.addEventListener('DOMContentLoaded', function() {
    const loadCatBtn = document.getElementById('load-cat-btn');
    const catContainer = document.getElementById('cat-container');
    
    // Demo cat images for initial implementation
    // Note: Card 003 will implement proper API integration
    const demoCatImages = [
        'https://placekitten.com/400/300',
        'https://placekitten.com/450/350',
        'https://placekitten.com/500/400',
        'https://placekitten.com/400/350',
        'https://placekitten.com/450/300'
    ];
    
    let currentImageIndex = 0;
    
    // Load cat picture function
    function loadCatPicture() {
        // Disable button and show loading
        loadCatBtn.disabled = true;
        loadCatBtn.textContent = 'Loading...';
        
        // Show loading spinner
        catContainer.innerHTML = '<div class="loading"></div>';
        
        // Simulate loading delay (realistic for API calls)
        setTimeout(() => {
            const imageUrl = demoCatImages[currentImageIndex];
            currentImageIndex = (currentImageIndex + 1) % demoCatImages.length;
            
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = 'Random cat picture';
            img.onerror = handleImageError;
            img.onload = handleImageLoad;
            
            catContainer.innerHTML = '';
            catContainer.appendChild(img);
        }, 800);
    }
    
    // Handle successful image load
    function handleImageLoad() {
        loadCatBtn.disabled = false;
        loadCatBtn.textContent = 'Load New Cat Picture';
    }
    
    // Handle image loading errors
    function handleImageError() {
        catContainer.innerHTML = `
            <div style="color: #e53e3e; text-align: center;">
                <p>😿 Oops! Couldn't load the cat picture.</p>
                <p>Please try again!</p>
            </div>
        `;
        loadCatBtn.disabled = false;
        loadCatBtn.textContent = 'Try Again';
    }
    
    // Event listeners
    loadCatBtn.addEventListener('click', loadCatPicture);
    
    // Load initial cat picture
    loadCatPicture();
    
    console.log('🐱 Cat Picture App initialized!');
    console.log('Note: This is a demo implementation. Card 003 will add proper API integration.');
});