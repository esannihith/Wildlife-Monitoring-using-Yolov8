// DOM Elements
const imageInput = document.getElementById('imageInput');
const videoInput = document.getElementById('videoInput'); // Added for video
const uploadedImage = document.getElementById('uploadedImage');
const uploadedVideoPreview = document.getElementById('uploadedVideoPreview'); // Added for video
const instructions = document.getElementById('instructions');
const videoInstructions = document.getElementById('videoInstructions'); // Added for video
const dropzone = document.getElementById('dropzone');
const videoDropzone = document.getElementById('videoDropzone'); // Added for video
const loadingOverlay = document.getElementById('loadingOverlay');
const inputSpinner = document.getElementById('inputSpinner');
const videoInputSpinner = document.getElementById('videoInputSpinner'); // Added for video
const analyzeBtn = document.getElementById('analyzeBtn');
const resetBtn = document.getElementById('resetBtn');
const modeSelection = document.getElementById('modeSelection');
const analysisSection = document.getElementById('analysisSection');
const analysisTitle = document.getElementById('analysisTitle');
const analysisDescription = document.getElementById('analysisDescription');
const resultTitle = document.getElementById('resultTitle');
const resultContainer = document.getElementById('resultContainer');
const placeholderMessage = document.getElementById('placeholder-message');
const resultLoadingOverlay = document.getElementById('resultLoadingOverlay');
const resultImageContainer = document.getElementById('resultImageContainer');
const resultVideoContainer = document.getElementById('resultVideoContainer'); // Added for video
const detectionResult = document.getElementById('detectionResult');
const detectionResultVideo = document.getElementById('detectionResultVideo'); // Added for video
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');

// Current detection mode
let currentMode = null;
let currentImageSrc = null;
let currentVideoSrc = null; // Added for video

// Detection mode information
const modeInfo = {
    'animal': {
        title: 'Animal & Human Detection',
        description: 'Upload an image to detect animals and humans.',
        resultTitle: 'Animal Detection Results',
        endpoint: '/detect/animal',
        inputType: 'image'
    },
    'ppe': {
        title: 'PPE Compliance Detection',
        description: 'Upload an image to detect personal protective equipment (PPE).',
        resultTitle: 'PPE Detection Results',
        endpoint: '/detect/ppe',
        inputType: 'image'
    },
    'weapon': {
        title: 'Weapon Detection',
        description: 'Upload an image to detect weapons like guns, rifles, and knives.',
        resultTitle: 'Weapon Detection Results',
        endpoint: '/detect/weapon',
        inputType: 'image'
    },
    'multi': {
        title: 'Multi-Model Image Detection',
        description: 'Upload an image to detect animals, humans, PPE, and weapons in a single analysis.',
        resultTitle: 'Combined Image Detection Results',
        endpoint: '/detect/multi',
        inputType: 'image'
    },
    'video-multi': { // New mode for video
        title: 'Multi-Model Video Detection',
        description: 'Upload a video to detect animals, humans, PPE, and weapons. Processing may take some time.',
        resultTitle: 'Combined Video Detection Results',
        endpoint: '/detect/video-multi',
        inputType: 'video'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    loadingOverlay.classList.add('hidden');
    
    analyzeBtn.disabled = true;
    
    if (detectionResult) {
        detectionResult.onclick = function() {
            openModal(this);
        };
    }
    
    if (uploadedImage) {
        uploadedImage.onclick = function() {
            openModal(this);
        };
    }
    
    const closeBtn = document.querySelector('.close-modal');
    if (closeBtn) {
        closeBtn.onclick = closeModal;
    }
    
    window.onclick = function(event) {
        if (event.target === imageModal) {
            closeModal();
        }
    };

    // Event listeners for video input and dropzone
    if (videoInput) {
        videoInput.addEventListener('change', previewVideo);
    }
    if (videoDropzone) {
        videoDropzone.addEventListener('dragover', handleDragOver);
        videoDropzone.addEventListener('dragleave', handleDragLeaveVideo);
        videoDropzone.addEventListener('drop', handleDropVideo);
    }
     // Event listeners for image input and dropzone
    if (imageInput) {
        imageInput.addEventListener('change', previewImage);
    }
    if (dropzone) {
        dropzone.addEventListener('dragover', handleDragOver);
        dropzone.addEventListener('dragleave', handleDragLeaveImage);
        dropzone.addEventListener('drop', handleDropImage);
    }

    // Add event listener for the analyze button
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', runAnalysis);
    }
});

// Open modal with the clicked image
function openModal(imgElement) {
    console.log("Opening modal with image:", imgElement.src);
    if (imageModal && modalImage) {
        imageModal.style.display = "block";
        modalImage.src = imgElement.src;
    }
}

// Close modal
function closeModal() {
    if (imageModal) {
        imageModal.style.display = "none";
    }
}

// Select detection mode
function selectDetectionMode(mode) {
    currentMode = mode;
    
    modeSelection.classList.add('hidden');
    analysisSection.classList.remove('hidden');
    
    analysisTitle.textContent = modeInfo[mode].title;
    analysisDescription.textContent = modeInfo[mode].description;
    resultTitle.textContent = modeInfo[mode].resultTitle;
    
    const uploadColumnTitleElement = document.getElementById('uploadColumnTitle'); // Get the element

    resetUpload(); 
    
    if (modeInfo[mode].inputType === 'video') {
        if (uploadColumnTitleElement) uploadColumnTitleElement.textContent = 'Upload Video'; // Change title for video
        document.getElementById('dropzone').classList.add('hidden');
        document.getElementById('videoUploadSection').classList.remove('hidden');
        // Ensure image-specific UI parts are hidden and video-specific are shown
        document.getElementById('imageUploadSpecifics').classList.add('hidden');
        document.getElementById('videoUploadSpecifics').classList.remove('hidden');
        resultImageContainer.classList.add('hidden');
        resultVideoContainer.classList.remove('hidden'); 
        placeholderMessage.textContent = 'Upload a video to begin analysis.';
    } else {
        if (uploadColumnTitleElement) uploadColumnTitleElement.textContent = 'Upload Image'; // Change title for image
        document.getElementById('dropzone').classList.remove('hidden');
        document.getElementById('videoUploadSection').classList.add('hidden');
        // Ensure video-specific UI parts are hidden and image-specific are shown
        document.getElementById('imageUploadSpecifics').classList.remove('hidden');
        document.getElementById('videoUploadSpecifics').classList.add('hidden');
        resultImageContainer.classList.remove('hidden'); 
        resultVideoContainer.classList.add('hidden');
        placeholderMessage.textContent = 'Upload an image to begin analysis.';
    }
    
    lucide.createIcons();
}

// Go back to mode selection
function backToModeSelection() {
    modeSelection.classList.remove('hidden');
    analysisSection.classList.add('hidden');
    currentMode = null;
    resetUpload(); // Reset everything when going back
}

// Preview uploaded image
function previewImage(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
            currentImageSrc = e.target.result;
            uploadedImage.src = currentImageSrc;
            uploadedImage.classList.remove('hidden');
            instructions.classList.add('hidden');
            analyzeBtn.disabled = false;
            
            uploadedImage.style.opacity = 0;
            setTimeout(() => {
                uploadedImage.style.opacity = 1;
                uploadedImage.style.transition = 'opacity 0.5s';
            }, 50);
            
            placeholderMessage.classList.remove('hidden');
            resultImageContainer.classList.add('hidden'); // Hide image result
            resultVideoContainer.classList.add('hidden'); // Also hide video result
            detectionResult.src = ''; // Clear previous image result
            detectionResultVideo.src = ''; // Clear previous video result
        };
        reader.readAsDataURL(file);
    } else if (file) {
        alert("Please upload a valid image file.");
        imageInput.value = ''; // Clear the invalid file
    }
}

// Preview uploaded video
function previewVideo(event) {
    const file = event.target.files[0];
    if (file && file.type.startsWith('video/')) {
        currentVideoSrc = URL.createObjectURL(file);
        uploadedVideoPreview.src = currentVideoSrc;
        uploadedVideoPreview.classList.remove('hidden');
        videoInstructions.classList.add('hidden');
        analyzeBtn.disabled = false;

        uploadedVideoPreview.style.opacity = 0;
        setTimeout(() => {
            uploadedVideoPreview.style.opacity = 1;
            uploadedVideoPreview.style.transition = 'opacity 0.5s';
        }, 50);

        placeholderMessage.classList.remove('hidden');
        resultImageContainer.classList.add('hidden'); // Hide image result
        resultVideoContainer.classList.add('hidden'); // Also hide video result
        detectionResult.src = ''; // Clear previous image result
        detectionResultVideo.src = ''; // Clear previous video result
    } else if (file) {
        alert("Please upload a valid video file.");
        videoInput.value = ''; // Clear the invalid file
    }
}

// Reset the upload area
function resetUpload() {
    imageInput.value = '';
    uploadedImage.src = '';
    uploadedImage.classList.add('hidden');
    instructions.classList.remove('hidden');
    
    videoInput.value = '';
    if (uploadedVideoPreview.src) { // Revoke object URL to free resources
        URL.revokeObjectURL(uploadedVideoPreview.src);
    }
    uploadedVideoPreview.src = '';
    uploadedVideoPreview.classList.add('hidden');
    videoInstructions.classList.remove('hidden');

    placeholderMessage.classList.remove('hidden');
    resultImageContainer.classList.add('hidden');
    resultVideoContainer.classList.add('hidden');
    detectionResult.src = '';
    detectionResultVideo.src = '';
    
    analyzeBtn.disabled = true;
    currentImageSrc = null;
    currentVideoSrc = null;
}

// Run analysis based on selected mode
function runAnalysis() {
    if (!currentMode) {
        alert("Please select a detection mode first.");
        return;
    }

    const modeDetails = modeInfo[currentMode];
    if (!modeDetails) {
        alert("Invalid detection mode selected.");
        return;
    }

    if (modeDetails.inputType === 'image') {
        if (!imageInput.files[0]) {
            alert("Please upload an image.");
            return;
        }
        runImageAnalysis(modeDetails.endpoint);
    } else if (modeDetails.inputType === 'video') {
        if (!videoInput.files[0]) {
            alert("Please upload a video.");
            return;
        }
        runVideoAnalysis(modeDetails.endpoint);
    }
}

function runImageAnalysis(endpoint) {
    const formData = new FormData();
    formData.append('image', imageInput.files[0]);

    showLoading(true, 'image');
    resultImageContainer.classList.add('hidden');
    placeholderMessage.classList.add('hidden');
    resultLoadingOverlay.classList.remove('hidden');

    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false, 'image');
        resultLoadingOverlay.classList.add('hidden');
        if (data.error) {
            alert(`Error: ${data.error}`);
            placeholderMessage.textContent = `Error: ${data.error}`;
            placeholderMessage.classList.remove('hidden');
            resultImageContainer.classList.add('hidden');
        } else {
            detectionResult.src = data.detection_result + '?t=' + new Date().getTime(); // Cache buster
            resultImageContainer.classList.remove('hidden');
            placeholderMessage.classList.add('hidden');
        }
    })
    .catch(error => {
        showLoading(false, 'image');
        resultLoadingOverlay.classList.add('hidden');
        alert(`Request failed: ${error}`);
        console.error('Error:', error);
        placeholderMessage.textContent = `Request failed: ${error}`;
        placeholderMessage.classList.remove('hidden');
        resultImageContainer.classList.add('hidden');
    });
}

function runVideoAnalysis(endpoint) {
    const formData = new FormData();
    formData.append('video', videoInput.files[0]);

    showLoading(true, 'video');
    resultVideoContainer.classList.add('hidden'); // Hide previous video result if any
    placeholderMessage.classList.add('hidden');
    resultLoadingOverlay.classList.remove('hidden'); // Show loading overlay for results area

    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showLoading(false, 'video');
        resultLoadingOverlay.classList.add('hidden');
        if (data.error) {
            alert(`Error: ${data.error}`);
            placeholderMessage.textContent = `Error: ${data.error}`;
            placeholderMessage.classList.remove('hidden');
            resultVideoContainer.classList.add('hidden');
        } else {
            detectionResultVideo.src = data.detection_result_video + '?t=' + new Date().getTime(); // Cache buster
            resultVideoContainer.classList.remove('hidden');
            placeholderMessage.classList.add('hidden');
        }
    })
    .catch(error => {
        showLoading(false, 'video');
        resultLoadingOverlay.classList.add('hidden');
        alert(`Request failed: ${error}`);
        console.error('Error:', error);
        placeholderMessage.textContent = `Request failed: ${error}`;
        placeholderMessage.classList.remove('hidden');
        resultVideoContainer.classList.add('hidden');
    });
}

// Show or hide loading indicators
function showLoading(isLoading, type) {
    if (isLoading) {
        if (type === 'image') {
            inputSpinner.classList.remove('hidden');
            uploadedImage.classList.add('hidden');
        } else if (type === 'video') {
            videoInputSpinner.classList.remove('hidden');
            uploadedVideoPreview.classList.add('hidden');
        }
        resultLoadingOverlay.classList.remove('hidden');
    } else {
        if (type === 'image') {
            inputSpinner.classList.add('hidden');
        } else if (type === 'video') {
            videoInputSpinner.classList.add('hidden');
        }
        resultLoadingOverlay.classList.add('hidden');
    }
}

// Generic drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    // Check if the target is videoDropzone or dropzone and apply styles accordingly
    if (e.currentTarget.id === 'videoDropzone') {
        videoDropzone.style.borderColor = '#166534'; 
        videoDropzone.style.backgroundColor = '#f0fdf4';
    } else if (e.currentTarget.id === 'dropzone') {
        dropzone.style.borderColor = '#166534';
        dropzone.style.backgroundColor = '#f0fdf4';
    }
}

function handleDragLeaveImage(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.style.borderColor = '#d1d5db'; // Reset to default border
    dropzone.style.backgroundColor = '#fff';
}

function handleDragLeaveVideo(e) {
    e.preventDefault();
    e.stopPropagation();
    videoDropzone.style.borderColor = '#d1d5db'; // Reset to default border
    videoDropzone.style.backgroundColor = '#fff';
}

function handleDropImage(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.style.borderColor = '#d1d5db';
    dropzone.style.backgroundColor = '#fff';
    
    if (e.dataTransfer.files.length) {
        const file = e.dataTransfer.files[0];
        if (file.type.startsWith('image/')) {
            imageInput.files = e.dataTransfer.files;
            previewImage({ target: { files: e.dataTransfer.files } });
        } else {
            alert("Please drop an image file.");
        }
    }
}

function handleDropVideo(e) {
    e.preventDefault();
    e.stopPropagation();
    videoDropzone.style.borderColor = '#d1d5db';
    videoDropzone.style.backgroundColor = '#fff';

    if (e.dataTransfer.files.length) {
        const file = e.dataTransfer.files[0];
        if (file.type.startsWith('video/')) {
            videoInput.files = e.dataTransfer.files;
            previewVideo({ target: { files: e.dataTransfer.files } });
        } else {
            alert("Please drop a video file.");
        }
    }
}

// Add ESC key support to close modal
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Ensure Lucide icons are created on initial load and when modes change
if (typeof lucide !== 'undefined') {
    lucide.createIcons();
}