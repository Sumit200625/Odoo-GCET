/* app/static/js/scanner.js - Mobile camera & USB scanner controller with audio & haptic feedback */

document.addEventListener('DOMContentLoaded', () => {
    const btnToggleCamera = document.getElementById('btnToggleCamera');
    const cameraContainer = document.getElementById('cameraContainer');
    const cameraVideo = document.getElementById('cameraVideo');
    const barcodeInput = document.getElementById('barcodeInput');
    let videoStream = null;
    let scanningActive = false;

    if (btnToggleCamera && cameraVideo) {
        btnToggleCamera.addEventListener('click', () => {
            if (scanningActive) {
                stopCameraScanner();
            } else {
                startCameraScanner();
            }
        });
    }

    function startCameraScanner() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Camera access is not supported by your browser or HTTPS connection.');
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => {
                videoStream = stream;
                cameraVideo.srcObject = stream;
                cameraContainer.classList.remove('d-none');
                btnToggleCamera.innerHTML = '<i class="bi bi-camera-video-off me-2"></i> Stop Camera Scanner';
                btnToggleCamera.classList.replace('btn-outline-dark', 'btn-danger');
                scanningActive = true;

                // If Browser supports BarcodeDetector API natively
                if ('BarcodeDetector' in window) {
                    const detector = new BarcodeDetector({ formats: ['qr_code', 'ean_13', 'upc_a', 'code_128'] });
                    const detectFrame = () => {
                        if (!scanningActive) return;
                        detector.detect(cameraVideo)
                            .then(barcodes => {
                                if (barcodes.length > 0) {
                                    const scannedCode = barcodes[0].rawValue;
                                    triggerScanFeedback();
                                    if (barcodeInput) {
                                        barcodeInput.value = scannedCode;
                                        document.getElementById('scanForm').submit();
                                    }
                                    stopCameraScanner();
                                } else {
                                    requestAnimationFrame(detectFrame);
                                }
                            })
                            .catch(err => {
                                requestAnimationFrame(detectFrame);
                            });
                    };
                    detectFrame();
                }
            })
            .catch(err => {
                alert('Could not access camera: ' + err.message);
            });
    }

    function stopCameraScanner() {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
            videoStream = null;
        }
        if (cameraContainer) cameraContainer.classList.add('d-none');
        if (btnToggleCamera) {
            btnToggleCamera.innerHTML = '<i class="bi bi-camera me-2"></i> Open Camera Scanner';
            btnToggleCamera.classList.replace('btn-danger', 'btn-outline-dark');
        }
        scanningActive = false;
    }

    // Audio & Haptic Feedback Synthesizer
    function triggerScanFeedback() {
        // Haptic Vibration feedback on supported mobile devices
        if (navigator.vibrate) {
            navigator.vibrate([100, 50, 100]);
        }

        // Web Audio API Beep Tone
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                const ctx = new AudioContext();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(880, ctx.currentTime); // 880Hz pitch (A5)
                gain.gain.setValueAtTime(0.1, ctx.currentTime);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.15);
            }
        } catch (e) {
            console.log('Audio feedback not available');
        }
    }
});
