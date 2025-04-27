// Three.js background animation with dynamic lighting and aurora effects
let container;
let camera, scene, renderer;
let mesh, geometry, positions, innerMesh, smallMesh;
let pointLight, ambientLight;
// Define these at the top level so they're accessible in all functions
let blueLight, purpleLight;
let mouseX = 0, mouseY = 0;
let targetRotationX = 0, targetRotationY = 0;
let windowHalfX = window.innerWidth / 2;
let windowHalfY = window.innerHeight / 2;
let animationTime = 0;
let lightAnimationRadius = 25;
let lightIntensity = 1.5;
let auroraMeshes = [];

init();
animate();

function init() {
    // Create container
    container = document.createElement('div');
    container.id = 'background-canvas';
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.zIndex = '-1';
    document.body.insertBefore(container, document.body.firstChild);

    // Initialize camera
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 30;

    // Initialize scene with deeper black for better aurora contrast
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);

    // Reduce fog density for better visibility of auroras
    scene.fog = new THREE.FogExp2(0x000000, 0.003);
    
    // Add lighting - do this early so references are established
    setupLighting();
    
    // Create Aurora Effect
    try {
        createAuroraEffect();
    } catch (e) {
        console.error("Error creating aurora effect:", e);
    }
    
    // Create main sphere and meshes
    createMainMeshes();

    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Add event listeners
    document.addEventListener('mousemove', onDocumentMouseMove);
    window.addEventListener('resize', onWindowResize);
}

// Setup all lighting in a separate function
function setupLighting() {
    // Soft ambient light for base illumination
    ambientLight = new THREE.AmbientLight(0x222222);
    scene.add(ambientLight);

    // Dynamic point light that will move around
    pointLight = new THREE.PointLight(0xffffff, lightIntensity, 100);
    pointLight.position.set(15, 15, 15);
    scene.add(pointLight);

    // Optional light helper sphere to show light position
    const lightSphereGeometry = new THREE.SphereGeometry(0.5, 16, 16);
    const lightSphereMaterial = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.3
    });
    const lightSphere = new THREE.Mesh(lightSphereGeometry, lightSphereMaterial);
    pointLight.add(lightSphere); // Add to the light so it moves with it

    // Add subtle colored light for more depth
    blueLight = new THREE.PointLight(0x4466ff, 0.7, 80); // Increased intensity and range
    blueLight.position.set(-15, -10, 10);
    scene.add(blueLight);

    // Add a second colored light on the opposite side
    purpleLight = new THREE.PointLight(0xaa44ff, 0.5, 70); // Increased intensity and range
    purpleLight.position.set(15, -15, -10);
    scene.add(purpleLight);
    
    // Add a green light for the aurora
    const greenLight = new THREE.PointLight(0x44ff88, 0.6, 60);
    greenLight.position.set(0, 20, -30);
    scene.add(greenLight);
}

// Create main meshes in a separate function
function createMainMeshes() {
    // Create geometry - using BufferGeometry for modern Three.js
    geometry = new THREE.IcosahedronGeometry(12, 4);
    
    // Store the initial positions of vertices
    positions = geometry.getAttribute('position').array.slice();

    // Create material for main mesh - now using MeshPhongMaterial to respond to lighting
    const material = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        wireframe: true,
        transparent: true,
        opacity: 0.15,
        emissive: 0x222222,
        shininess: 50,
        specular: 0x666666
    });

    // Create mesh
    mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(0, 0, 0);
    scene.add(mesh);

    // Create a solid version with very low opacity to catch light
    const solidGeometry = new THREE.IcosahedronGeometry(11.9, 4);
    const solidMaterial = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        wireframe: false,
        transparent: true,
        opacity: 0.02,
        emissive: 0x000000,
        shininess: 100,
        specular: 0xffffff,
        side: THREE.DoubleSide
    });

    const solidMesh = new THREE.Mesh(solidGeometry, solidMaterial);
    solidMesh.position.set(0, 0, 0);
    scene.add(solidMesh);

    // Create inner wireframe with lighting properties
    const innerGeometry = new THREE.IcosahedronGeometry(8, 3);
    const innerMaterial = new THREE.MeshPhongMaterial({
        color: 0x888888,
        wireframe: true,
        transparent: true,
        opacity: 0.2,
        emissive: 0x111111,
        shininess: 70,
        specular: 0x555555
    });
    
    innerMesh = new THREE.Mesh(innerGeometry, innerMaterial);
    innerMesh.position.set(0, 0, 0);
    scene.add(innerMesh);
    
    // Add solid inner version
    const innerSolidGeometry = new THREE.IcosahedronGeometry(7.9, 3);
    const innerSolidMaterial = new THREE.MeshPhongMaterial({
        color: 0x333333,
        wireframe: false,
        transparent: true,
        opacity: 0.03,
        emissive: 0x000000, 
        shininess: 90,
        specular: 0xaaaaaa,
        side: THREE.DoubleSide
    });

    const innerSolidMesh = new THREE.Mesh(innerSolidGeometry, innerSolidMaterial);
    innerSolidMesh.position.set(0, 0, 0);
    scene.add(innerSolidMesh);

    // Create smallest mesh with different lighting properties
    const smallGeometry = new THREE.IcosahedronGeometry(5, 2);
    const smallMaterial = new THREE.MeshPhongMaterial({
        color: 0xcccccc,
        wireframe: true,
        transparent: true,
        opacity: 0.1,
        emissive: 0x050505,
        shininess: 90,
        specular: 0x444444
    });
    
    smallMesh = new THREE.Mesh(smallGeometry, smallMaterial);
    smallMesh.position.set(0, 0, -5);
    scene.add(smallMesh);

    // Add solid inner core
    const coreGeometry = new THREE.SphereGeometry(2, 32, 32);
    const coreMaterial = new THREE.MeshPhongMaterial({
        color: 0xffffff,
        wireframe: false,
        transparent: true,
        opacity: 0.05,
        emissive: 0x222222,
        shininess: 150,
        specular: 0xffffff
    });

    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    coreMesh.position.set(0, 0, 0);
    scene.add(coreMesh);
}

// Function to create aurora effect using simple plane meshes
function createAuroraEffect() {
    // Create several aurora curtains with different properties
    createAuroraCurtain(0, 80, 0x66ffaa, -60); // Green aurora - larger and closer
    createAuroraCurtain(-30, 70, 0x4488ff, -80); // Blue aurora - moved more to the side and closer
    createAuroraCurtain(30, 65, 0xcc55ff, -90); // Purple aurora - brighter and closer
    
    // Add an extra curtain for more effect
    createAuroraCurtain(-10, 60, 0x55ffcc, -70); // Teal aurora
}

// Function to create a single aurora curtain
function createAuroraCurtain(offsetX, width, color, zPosition) {
    // Create a plane geometry for the aurora
    const geometry = new THREE.PlaneGeometry(width, 80, 20, 20);
    
    // Create a custom aurora material with additive blending for glow effect
    const material = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.5,  // Increased from 0.3 for more visibility
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
    });
    
    // Create the aurora mesh
    const auroraMesh = new THREE.Mesh(geometry, material);
    auroraMesh.position.set(offsetX, 0, zPosition);
    auroraMesh.rotation.x = Math.PI / 4; // Tilt slightly
    auroraMesh.rotation.y = Math.PI / 6; // Rotate slightly
    
    // Store original vertex positions for animation
    auroraMesh.userData.originalPositions = [];
    const positionAttribute = geometry.getAttribute('position');
    for (let i = 0; i < positionAttribute.count; i++) {
        auroraMesh.userData.originalPositions.push({
            x: positionAttribute.getX(i),
            y: positionAttribute.getY(i),
            z: positionAttribute.getZ(i)
        });
    }
    
    // Store mesh and properties for animation
    auroraMeshes.push({
        mesh: auroraMesh,
        width: width,
        color: color,
        speed: 0.5 + Math.random() * 0.5, // Random speed factor
        offset: Math.random() * 1000 // Random animation offset
    });
    
    scene.add(auroraMesh);

    // Add a second, slightly different aurora for more depth
    const geometry2 = new THREE.PlaneGeometry(width * 0.8, 70, 15, 15);
    const material2 = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.4,  // Increased from 0.2 for more visibility
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
    });
    
    const auroraMesh2 = new THREE.Mesh(geometry2, material2);
    auroraMesh2.position.set(offsetX - 5, -5, zPosition + 10);
    auroraMesh2.rotation.x = Math.PI / 3.5;
    auroraMesh2.rotation.y = Math.PI / 5;
    
    // Store original vertex positions for animation
    auroraMesh2.userData.originalPositions = [];
    const positionAttribute2 = geometry2.getAttribute('position');
    for (let i = 0; i < positionAttribute2.count; i++) {
        auroraMesh2.userData.originalPositions.push({
            x: positionAttribute2.getX(i),
            y: positionAttribute2.getY(i),
            z: positionAttribute2.getZ(i)
        });
    }
    
    auroraMeshes.push({
        mesh: auroraMesh2,
        width: width * 0.8,
        color: color,
        speed: 0.3 + Math.random() * 0.5,
        offset: Math.random() * 1000
    });
    
    scene.add(auroraMesh2);
}

function onWindowResize() {
    windowHalfX = window.innerWidth / 2;
    windowHalfY = window.innerHeight / 2;

    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
}

function onDocumentMouseMove(event) {
    // Calculate normalized mouse position (-1 to 1)
    mouseX = (event.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
    
    // Set target rotation based on mouse position, but with reduced intensity
    targetRotationX = mouseY * 0.3;
    targetRotationY = mouseX * 0.3;
    
    // Adjust point light intensity based on mouse movement
    // Moving the mouse increases light intensity slightly
    const distanceFromCenter = Math.sqrt(mouseX * mouseX + mouseY * mouseY);
    pointLight.intensity = lightIntensity + distanceFromCenter * 0.5;
}

function animate() {
    requestAnimationFrame(animate);
    animationTime += 0.01; // Increment time for continuous animation
    render();
}

function render() {
    try {
    // Make mesh vertices "breathe" using modern approach with continuous animation
    const time = animationTime;
    const positionAttribute = geometry.getAttribute('position');
    
    for (let i = 0; i < positionAttribute.count; i++) {
        const x = positions[i * 3];
        const y = positions[i * 3 + 1];
        const z = positions[i * 3 + 2];
        
        // Apply gentler distortion to z-coordinate with constant animation
        const distortion = 0.1 * Math.sin(x * 0.03 + time);
        positionAttribute.setZ(i, z + distortion);
    }
    
    positionAttribute.needsUpdate = true;
        
        // Update all light positions and colors
        updateLightEffects(time);
        
        // Update aurora animations
        updateAurora(time);
    
    // Constant rotation regardless of mouse movement - ensures continuous animation
    const baseRotationSpeed = 0.01;
    
    // Always apply constant base rotation
    mesh.rotation.x += baseRotationSpeed;
    mesh.rotation.y += baseRotationSpeed * 1.2;
    
    innerMesh.rotation.x += baseRotationSpeed * 0.8;
    innerMesh.rotation.y += baseRotationSpeed * 0.6;
    
    smallMesh.rotation.x += baseRotationSpeed * 1.1;
    smallMesh.rotation.y += baseRotationSpeed * 0.9;
    
    // Also apply rotation based on mouse movement - for interactive effect
    mesh.rotation.x += (targetRotationX - mesh.rotation.x) * 0.01;
    mesh.rotation.y += (targetRotationY - mesh.rotation.y) * 0.01;
    
    innerMesh.rotation.x += (targetRotationX * 0.7 - innerMesh.rotation.x) * 0.008;
    innerMesh.rotation.y += (targetRotationY * 0.7 - innerMesh.rotation.y) * 0.008;
    
    smallMesh.rotation.x += (targetRotationX * 0.5 - smallMesh.rotation.x) * 0.006;
    smallMesh.rotation.y += (targetRotationY * 0.5 - smallMesh.rotation.y) * 0.006;

    renderer.render(scene, camera);
    } catch (e) {
        console.error("Error in render loop:", e);
    }
}

// Function to update aurora effect
function updateAurora(time) {
    try {
        auroraMeshes.forEach(aurora => {
            const mesh = aurora.mesh;
            const positionAttribute = mesh.geometry.getAttribute('position');
            const originalPositions = mesh.userData.originalPositions;
            
            // Animate each vertex to create flowing wave effect
            for (let i = 0; i < positionAttribute.count; i++) {
                const origPos = originalPositions[i];
                
                // Create wave-like motion in x and y directions
                // Increased amplitude from 2 to 3-4 for more dramatic movement
                const waveX = Math.sin((origPos.x + time * aurora.speed) * 0.1 + aurora.offset) * 4;
                const waveY = Math.cos((origPos.y + time * aurora.speed * 0.5) * 0.1 + aurora.offset) * 3;
                
                positionAttribute.setX(i, origPos.x + waveX);
                positionAttribute.setY(i, origPos.y + waveY);
                positionAttribute.setZ(i, origPos.z + Math.sin(time * 0.5 + i * 0.05) * 1.5); // Increased z-movement
            }
            
            positionAttribute.needsUpdate = true;
            
            // Slowly change opacity for breathing effect - increased range for more visibility
            mesh.material.opacity = 0.3 + 0.25 * Math.sin(time * 0.5 + aurora.offset);
        });
    } catch (e) {
        console.error("Error updating aurora:", e);
    }
}

// Function to update the dynamic light effects
function updateLightEffects(time) {
    try {
        // Move the point light in a circular path with oscillating height
        const lightX = Math.sin(time * 0.5) * lightAnimationRadius;
        const lightY = Math.cos(time * 0.3) * lightAnimationRadius;
        const lightZ = Math.sin(time * 0.2) * 10 + 20; // Oscillate between 10 and 30
        
        pointLight.position.set(lightX, lightY, lightZ);
        
        // Slowly change light color over time with more vibrant colors
        const r = 0.6 + 0.4 * Math.sin(time * 0.1);
        const g = 0.6 + 0.4 * Math.sin(time * 0.1 + 2);
        const b = 0.6 + 0.4 * Math.sin(time * 0.1 + 4);
        pointLight.color.setRGB(r, g, b);
        
        // Pulse the light intensity
        pointLight.intensity = lightIntensity + 0.5 * Math.sin(time * 0.8);
        
        // Update the secondary lights - only if they exist
        if (blueLight && blueLight.position) {
            const blueX = Math.sin(time * 0.2 + 1) * lightAnimationRadius * 0.7;
            const blueY = Math.cos(time * 0.3 + 2) * lightAnimationRadius * 0.7;
            blueLight.position.set(blueX, blueY, 5);
            // Pulse blue light intensity
            blueLight.intensity = 0.7 + 0.3 * Math.sin(time * 0.6);
        }
        
        if (purpleLight && purpleLight.position) {
            const purpleX = Math.sin(time * 0.15 + 3) * lightAnimationRadius * 0.6;
            const purpleY = Math.cos(time * 0.25 + 4) * lightAnimationRadius * 0.6;
            purpleLight.position.set(purpleX, purpleY, -10);
            // Pulse purple light intensity
            purpleLight.intensity = 0.5 + 0.3 * Math.sin(time * 0.7 + 2);
        }
    } catch (e) {
        console.error("Error updating light effects:", e);
    }
} 