// Card Spotlight Effect
document.addEventListener('DOMContentLoaded', function() {
  // Find all card-spotlight elements
  const cards = document.querySelectorAll('.card-spotlight');
  
  // Early return if no cards found
  if (cards.length === 0) return;
  
  // Prepare dots for the dot matrix effect
  function createDots(container) {
    const dotsContainer = container.querySelector('.dots-overlay');
    if (!dotsContainer) return;
    
    // Clear existing dots
    dotsContainer.innerHTML = '';
    
    // Calculate how many dots we need based on container size
    const containerWidth = container.offsetWidth;
    const containerHeight = container.offsetHeight;
    
    // Create a grid of dots
    const spacing = 15; // Space between dots (smaller for denser pattern)
    const rows = Math.ceil(containerHeight / spacing);
    const cols = Math.ceil(containerWidth / spacing);
    
    // Create dots with variable sizes and opacities
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const dot = document.createElement('div');
        dot.classList.add('dot');
        
        // Position dots in a grid with slight random offset
        const randomOffsetX = Math.random() * 5 - 2.5;
        const randomOffsetY = Math.random() * 5 - 2.5;
        const xPos = c * spacing + randomOffsetX;
        const yPos = r * spacing + randomOffsetY;
        
        // Set dot position
        dot.style.left = `${xPos}px`;
        dot.style.top = `${yPos}px`;
        
        // Randomize dot appearance
        const size = 2 + Math.random() * 2; // Random size between 2-4px
        dot.style.width = `${size}px`;
        dot.style.height = `${size}px`;
        
        // Randomize opacity between 0.2 and 0.8
        const opacity = 0.2 + Math.random() * 0.6;
        dot.style.opacity = opacity;
        
        // Add animation delay based on position
        const delay = (r * 0.01) + (c * 0.01); 
        dot.style.transitionDelay = `${delay}s`;
        
        // Add dot to container
        dotsContainer.appendChild(dot);
      }
    }
  }
  
  // Animate dots on hover
  function animateDots(container, mouseX, mouseY) {
    const dots = container.querySelectorAll('.dot');
    const rect = container.getBoundingClientRect();
    
    dots.forEach(dot => {
      // Get dot position
      const dotLeft = parseFloat(dot.style.left);
      const dotTop = parseFloat(dot.style.top);
      
      // Calculate distance from mouse to dot
      const distX = mouseX - dotLeft;
      const distY = mouseY - dotTop;
      const distance = Math.sqrt(distX * distX + distY * distY);
      
      // Effect decreases with distance
      const effect = Math.max(0, 1 - distance / 100);
      
      // Apply subtle movement
      if (effect > 0) {
        const moveX = distX * effect * 0.05;
        const moveY = distY * effect * 0.05;
        
        dot.style.transform = `translate(calc(-50% + ${moveX}px), calc(-50% + ${moveY}px))`;
        
        // Increase brightness for dots closer to mouse
        dot.style.opacity = 0.2 + effect * 0.8;
      } else {
        dot.style.transform = 'translate(-50%, -50%)';
      }
    });
  }
  
  // For each card, add mouse move listener
  cards.forEach(card => {
    // Create the dot matrix
    createDots(card);
    
    // Initialize variables at the center
    const width = card.offsetWidth;
    const height = card.offsetHeight;
    card.style.setProperty('--mouse-x', `${width/2}px`);
    card.style.setProperty('--mouse-y', `${height/2}px`);
    
    // Handle mouse movement
    card.addEventListener('mousemove', (e) => {
      // Get position relative to the card
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      // Set CSS variables for the position
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
      
      // Animate dots based on mouse position
      animateDots(card, x, y);
      
      // Scale effect for better interaction
      if (!card.classList.contains('card-active')) {
        card.classList.add('card-active');
      }
    });
    
    // Handle mouse enter
    card.addEventListener('mouseenter', () => {
      card.classList.add('card-active');
    });
    
    // Handle mouse leave
    card.addEventListener('mouseleave', () => {
      card.classList.remove('card-active');
      
      // Reset position to center when mouse leaves
      const width = card.offsetWidth;
      const height = card.offsetHeight;
      card.style.setProperty('--mouse-x', `${width/2}px`);
      card.style.setProperty('--mouse-y', `${height/2}px`);
      
      // Reset dots
      const dots = card.querySelectorAll('.dot');
      dots.forEach(dot => {
        dot.style.transform = 'translate(-50%, -50%)';
        // Return to original opacity
        dot.style.opacity = 0.2 + Math.random() * 0.6;
      });
    });
  });
  
  // Handle window resize to recreate dots
  window.addEventListener('resize', () => {
    cards.forEach(card => {
      createDots(card);
    });
  });
}); 