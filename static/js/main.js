// DOM Elements
const fpsValEl = document.getElementById('fps-val');
const videoFeedEl = document.getElementById('video-feed');
const videoContainerEl = document.getElementById('video-container');
const speedValEl = document.getElementById('speed-val');
const curvatureValEl = document.getElementById('curvature-val');

// LDW Elements
const ldwStatusEl = document.getElementById('ldw-status');
const ldwOffsetEl = document.getElementById('ldw-offset');
const steeringWheel = document.getElementById('steering-wheel');
const ldwCard = document.getElementById('ldw-card');

// FCW Elements
const fcwStatusEl = document.getElementById('fcw-status');
const leadTtcSecEl = document.getElementById('lead-ttc-sec');
const leadDistEl = document.getElementById('lead-dist');
const fcwCard = document.getElementById('fcw-card');

// Objects Badges
const objCar = document.getElementById('obj-car');
const objMoto = document.getElementById('obj-motorcycle');
const objTruck = document.getElementById('obj-truck');
const objBus = document.getElementById('obj-bus');
const objPerson = document.getElementById('obj-person');
const objSign = document.getElementById('obj-traffic-sign');
const objLight = document.getElementById('obj-traffic-light');

// Sliders and Config
const safeDistSlider = document.getElementById('safe-distance-input');
const safeDistVal = document.getElementById('safe-dist-val');
const ttcSlider = document.getElementById('ttc-input');
const ttcVal = document.getElementById('ttc-val');
const volumeSlider = document.getElementById('volume-input');
const volumeVal = document.getElementById('volume-val');

// Buttons
const btnPause = document.getElementById('btn-pause');
const btnToggleLane = document.getElementById('btn-toggle-lane');
const btnToggleBrowserAudio = document.getElementById('btn-toggle-browser-audio');

// Audio Cache and Configuration
let browserAudioEnabled = false;
let currentAudio = null;
let lastPlayedTime = {};

const audioCache = {
    startup: new Audio('/static/audio/he_thong_khoi_dong.mp3'),
    fcw_danger: new Audio('/static/audio/khoang_cach_nguy_hiem.mp3'),
    fcw_warning: new Audio('/static/audio/chu_y_giu_khoang_cach.mp3'),
    ldw_left: new Audio('/static/audio/lech_lan_trai.mp3'),
    ldw_right: new Audio('/static/audio/lech_lan_phai.mp3')
};

// Console Log System Variables
let consoleLines = [];
let rawLogsCache = new Set();
let isPaused = false;
let lastFcw = "SAFE";
let lastLdw = "BÌNH THƯỜNG";

// Initialize Console and Seed Server Logs
appendLogLine("[SYSTEM] Giao diện Dashboard đã sẵn sàng.", "system");
fetchServerLogs();
setInterval(fetchServerLogs, 1500);

// Slider Value Updates
if (safeDistSlider) {
    safeDistSlider.addEventListener('input', (e) => safeDistVal.textContent = e.target.value);
}
if (ttcSlider) {
    ttcSlider.addEventListener('input', (e) => ttcVal.textContent = parseFloat(e.target.value).toFixed(1));
}
if (volumeSlider) {
    volumeSlider.addEventListener('input', (e) => {
        const pct = Math.round(e.target.value * 100);
        volumeVal.textContent = pct;
        // Cập nhật âm lượng cho toàn bộ các file audio đang tải
        Object.values(audioCache).forEach(audio => {
            audio.volume = parseFloat(e.target.value);
        });
    });
}

// Config Form Submit (Save Dynamic Parameters)
const configForm = document.getElementById('config-form');
if (configForm) {
    configForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;

        const vol = volumeSlider ? parseFloat(volumeSlider.value) : 1.0;

        fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                safe_distance: parseFloat(safeDistSlider.value),
                ttc_threshold: parseFloat(ttcSlider.value),
                volume: vol
            })
        }).then(res => res.json()).then(data => {
            if (data.status === "success") {
                appendLogLine(`Cập nhật tham số: SafeDist=${safeDistSlider.value}m, TTC=${parseFloat(ttcSlider.value).toFixed(1)}s, Vol=${Math.round(vol * 100)}%`, "success");

                // Button effect
                btn.innerHTML = '<i class="fa-solid fa-check"></i> ĐÃ LƯU';
                btn.style.backgroundColor = 'var(--safe-green)';
                btn.style.borderColor = 'var(--safe-green)';
                btn.style.color = '#000';
                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.style.backgroundColor = '';
                    btn.style.borderColor = '';
                    btn.style.color = '';
                }, 2000);
            }
        }).catch(err => {
            appendLogLine("Lỗi lưu cấu hình: Không kết nối được server", "danger");
        });
    });
}

// Demo Videos Trigger
['btn-demo-saigon', 'btn-demo-highway'].forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener('click', () => {
        const filename = id === 'btn-demo-saigon' ? 'demo10.mp4' : '7802285753135.mp4';
        const displayName = id === 'btn-demo-saigon' ? 'Nội Đô (Sài Gòn)' : 'Cao Tốc';
        appendLogLine(`Đang yêu cầu chạy video demo: ${displayName}...`, "info");

        fetch('/api/select_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: filename })
        }).then(res => res.json()).then(data => {
            if (data.status === "success") {
                appendLogLine(`Khởi động video demo thành công: ${displayName}`, "success");
                videoFeedEl.src = '';
                setTimeout(() => videoFeedEl.src = '/video_feed?t=' + Date.now(), 200);
            } else {
                appendLogLine(`Lỗi tải video demo: ${data.message}`, "danger");
            }
        }).catch(err => {
            appendLogLine("Lỗi kết nối khi chọn video demo", "danger");
        });
    });
});

// Pause / Resume System
if (btnPause) {
    btnPause.addEventListener('click', () => {
        isPaused = !isPaused;
        fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: isPaused ? 'pause' : 'resume' })
        }).then(res => res.json()).then(data => {
            if (isPaused) {
                appendLogLine("[CONTROL] Đã tạm dừng luồng xử lý ADAS & cảnh báo âm thanh.", "warning");
                btnPause.innerHTML = '<i class="fa-solid fa-play"></i> BẮT ĐẦU LẠI';
                btnPause.className = 'btn-control btn-pause-system paused';
                if (currentAudio) {
                    currentAudio.pause();
                }
            } else {
                appendLogLine("[CONTROL] Kích hoạt chạy tiếp luồng xử lý ADAS.", "success");
                btnPause.innerHTML = '<i class="fa-solid fa-pause"></i> TẠM DỪNG';
                btnPause.className = 'btn-control btn-pause-system';
                videoFeedEl.src = '/video_feed?t=' + Date.now();
            }
        });
    });
}

// Toggle Lane Drawing
let isLaneVisible = true;
if (btnToggleLane) {
    btnToggleLane.addEventListener('click', () => {
        isLaneVisible = !isLaneVisible;
        if (isLaneVisible) {
            btnToggleLane.innerHTML = '<i class="fa-solid fa-eye-slash"></i> <span>TẮT KẺ LANE</span>';
            btnToggleLane.classList.remove('active');
            appendLogLine("[CONFIG] Đã BẬT nhận diện và vẽ làn đường.", "info");
        } else {
            btnToggleLane.innerHTML = '<i class="fa-solid fa-eye"></i> <span>BẬT KẺ LANE</span>';
            btnToggleLane.classList.add('active');
            appendLogLine("[CONFIG] Đã TẮT nhận diện làn đường (Tiết kiệm CPU).", "warning");
        }

        fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ show_lane: isLaneVisible })
        });
    });
}

// Toggle Browser-side Audio Warnings
if (btnToggleBrowserAudio) {
    btnToggleBrowserAudio.addEventListener('click', () => {
        browserAudioEnabled = !browserAudioEnabled;
        if (browserAudioEnabled) {
            btnToggleBrowserAudio.innerHTML = '<i class="fa-solid fa-volume-high"></i> <span>TẮT LOA WEB</span>';
            btnToggleBrowserAudio.classList.add('active');
            appendLogLine("[AUDIO] Đã BẬT âm thanh cảnh báo trực tiếp trên trình duyệt.", "success");

            // Phát thử âm thanh khởi động để kích hoạt audio context trong trình duyệt
            playBrowserAudio("startup");
        } else {
            btnToggleBrowserAudio.innerHTML = '<i class="fa-solid fa-volume-xmark"></i> <span>BẬT LOA WEB</span>';
            btnToggleBrowserAudio.classList.remove('active');
            appendLogLine("[AUDIO] Đã TẮT âm thanh trình duyệt (chỉ dùng loa máy chủ).", "info");
            if (currentAudio) {
                currentAudio.pause();
            }
        }
    });
}

// Video File Upload Input
const videoUpload = document.getElementById('video-upload');
if (videoUpload) {
    videoUpload.addEventListener('change', (e) => {
        if (!e.target.files.length) return;
        const file = e.target.files[0];

        const formData = new FormData();
        formData.append('file', file);

        appendLogLine(`Đang tải tệp video lên máy chủ: ${file.name}...`, "info");

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        }).then(res => res.json()).then(data => {
            if (data.status === "success") {
                appendLogLine(`Đã tải lên và chuyển sang xử lý tệp: ${file.name}`, "success");
                videoFeedEl.src = '';
                setTimeout(() => videoFeedEl.src = '/video_feed?t=' + Date.now(), 200);
            } else {
                appendLogLine(`Lỗi tải video lên: ${data.message}`, "danger");
            }
        }).catch(err => {
            appendLogLine("Lỗi kết nối mạng khi tải video", "danger");
        });
    });
}

// Telemetry Stream Event Listener (SSE)
let evtSource = new EventSource('/api/alerts');

evtSource.onmessage = function (e) {
    if (isPaused) return;
    const data = JSON.parse(e.data);

    // Update FPS
    const fps = Math.round(data.fps);
    if (fpsValEl.textContent != fps) fpsValEl.textContent = fps;

    // Auto-calculate speed based on tracking target vehicle or defaults
    const speedBase = data.target_vehicle && data.target_vehicle.distance < 50 ? 55 : 65;
    const speed = speedBase + Math.floor(Math.random() * 3 - 1);
    speedValEl.textContent = speed;

    // Update curvature if present
    if (curvatureValEl && data.curvature !== undefined) {
        curvatureValEl.textContent = data.curvature.toFixed(1);
    }

    // Update LDW Vẹt làn Offset
    const offset = data.ldw_offset.toFixed(2);
    if (ldwOffsetEl.textContent !== offset) ldwOffsetEl.textContent = offset;

    // LDW warning handling
    if (data.ldw_status !== lastLdw) {
        ldwStatusEl.textContent = data.ldw_status;

        if (data.ldw_status.includes("LỆCH")) {
            ldwStatusEl.className = "status-indicator status-danger";
            steeringWheel.style.color = "var(--danger-red)";
            steeringWheel.style.filter = "drop-shadow(0 0 8px rgba(255, 51, 102, 0.6))";

            if (data.ldw_status.includes("TRÁI")) {
                steeringWheel.style.transform = "rotate(-35deg)";
                appendLogLine("CẢNH BÁO: Xe chệch vạch làn đường bên TRÁI!", "danger");
                playBrowserAudio("ldw_left");
            } else if (data.ldw_status.includes("PHẢI")) {
                steeringWheel.style.transform = "rotate(35deg)";
                appendLogLine("CẢNH BÁO: Xe chệch vạch làn đường bên PHẢI!", "danger");
                playBrowserAudio("ldw_right");
            }
        } else {
            ldwStatusEl.className = "status-indicator status-safe";
            steeringWheel.style.transform = "rotate(0deg)";
            steeringWheel.style.color = "var(--safe-green)";
            steeringWheel.style.filter = "drop-shadow(0 0 5px rgba(0, 240, 139, 0.3))";
        }
        lastLdw = data.ldw_status;
    }

    // FCW warning handling
    if (data.fcw_status !== lastFcw) {
        if (data.fcw_status === "SAFE") {
            fcwStatusEl.textContent = "AN TOÀN";
            fcwStatusEl.className = "status-indicator status-safe";
            fcwCard.style.borderColor = "";
        }
        else if (data.fcw_status === "WARNING") {
            fcwStatusEl.textContent = "CHÚ Ý";
            fcwStatusEl.className = "status-indicator status-warning";
            fcwCard.style.borderColor = "var(--warn-yellow)";
            appendLogLine("CHÚ Ý: Xe phía trước đi chậm. Hãy chú ý giữ cự ly an toàn!", "warning");
            playBrowserAudio("fcw_warning");
        } else {
            fcwStatusEl.textContent = "NGUY HIỂM";
            fcwStatusEl.className = "status-indicator status-danger";
            fcwCard.style.borderColor = "var(--danger-red)";
            appendLogLine("CẢNH BÁO KHẨN CẤP: Nguy cơ va chạm phía trước! PHANH GẤP!", "danger");
            playBrowserAudio("fcw_danger");
        }
        lastFcw = data.fcw_status;
    }

    // Trigger visual glowing container borders based on status
    if (data.fcw_status === "DANGER") {
        videoContainerEl.className = "video-container danger-active";
    } else if (data.fcw_status === "WARNING" || data.ldw_status.includes("LỆCH")) {
        videoContainerEl.className = "video-container warning-active";
    } else {
        videoContainerEl.className = "video-container";
    }

    // Update Lead Vehicle Metrics
    if (data.target_vehicle) {
        leadDistEl.textContent = data.target_vehicle.distance.toFixed(1);
        leadTtcSecEl.textContent = data.target_vehicle.ttc === 99.0 ? "∞" : data.target_vehicle.ttc.toFixed(1);
    } else {
        leadDistEl.textContent = "--.-";
        leadTtcSecEl.textContent = "--.-";
    }

    // Update Objects Counter Badges
    const counts = data.objects_detected || {};
    if (objCar && objCar.textContent != (counts.car || 0)) objCar.textContent = counts.car || 0;
    if (objMoto && objMoto.textContent != (counts.motorcycle || 0)) objMoto.textContent = counts.motorcycle || 0;
    if (objTruck && objTruck.textContent != (counts.truck || 0)) objTruck.textContent = counts.truck || 0;
    if (objBus && objBus.textContent != (counts.bus || 0)) objBus.textContent = counts.bus || 0;
    if (objPerson && objPerson.textContent != (counts.person || 0)) objPerson.textContent = counts.person || 0;
    if (objSign && objSign.textContent != (counts['traffic sign'] || 0)) objSign.textContent = counts['traffic sign'] || 0;
    if (objLight && objLight.textContent != (counts['traffic light'] || 0)) objLight.textContent = counts['traffic light'] || 0;
};

// Console Log Management Helper Functions
function appendLogLine(text, type = "normal") {
    const timeStr = new Date().toLocaleTimeString('vi-VN', { hour12: false });
    const formattedLine = `[${timeStr}] ${text}`;

    // Avoid double consecutive alerts
    if (consoleLines.length > 0 && consoleLines[consoleLines.length - 1].text.endsWith(text)) {
        return;
    }

    consoleLines.push({ text: formattedLine, type: type });
    if (consoleLines.length > 50) {
        consoleLines.shift();
    }
    renderConsole();
}

function renderConsole() {
    const track = document.getElementById('timeline-track');
    if (!track) return;

    track.innerHTML = consoleLines.map(line => {
        let cssClass = "log-line";
        if (line.type === "info") cssClass += " info-line";
        else if (line.type === "success") cssClass += " success-line";
        else if (line.type === "warning") cssClass += " warning-line";
        else if (line.type === "danger") cssClass += " danger-line";
        else if (line.type === "system") cssClass += " system-line";

        // Auto classing based on backend log prefixes if type is generic
        if (line.type === "normal") {
            if (line.text.includes("[INFO]") || line.text.includes("[SUCCESS]")) cssClass += " info-line";
            else if (line.text.includes("[WARNING]") || line.text.includes("[CẢNH BÁO]") || line.text.includes("[CONFIG]")) cssClass += " warning-line";
            else if (line.text.includes("[ERROR]") || line.text.includes("[CRITICAL]")) cssClass += " danger-line";
            else if (line.text.includes("[CONTROL]")) cssClass += " info-line";
            else if (line.text.includes("[START]") || line.text.includes("====")) cssClass += " system-line";
        }

        return `<div class="${cssClass}">${line.text}</div>`;
    }).join('');

    // Scroll logs down to bottom
    track.scrollTop = track.scrollHeight;
}

// Fetch Server Logs and Append Unseen Lines
function fetchServerLogs() {
    fetch('/api/logs')
        .then(res => res.json())
        .then(lines => {
            let addedNew = false;
            lines.forEach(line => {
                if (!rawLogsCache.has(line)) {
                    rawLogsCache.add(line);

                    // Prevent duplicate entries already printed locally
                    const cleanMsg = line.replace(/^\[.*?\]\s*/, ''); // strip prefix if exists
                    const alreadyExists = consoleLines.some(l => l.text.includes(cleanMsg));
                    if (!alreadyExists) {
                        consoleLines.push({ text: line, type: "normal" });
                        addedNew = true;
                    }
                }
            });

            if (addedNew) {
                if (consoleLines.length > 50) {
                    consoleLines = consoleLines.slice(-50);
                }
                renderConsole();
            }
        })
        .catch(err => console.error("Lỗi fetch log từ server:", err));
}

// Client-side Web Audio Trigger
function playBrowserAudio(type) {
    if (!browserAudioEnabled) return;
    const now = Date.now();

    // Cooldown 5 seconds for same alert type
    if (lastPlayedTime[type] && (now - lastPlayedTime[type] < 5000)) {
        return;
    }

    // If playing startup or danger, we stop previous track immediately
    if (type === "startup" || type === "fcw_danger") {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }
    }

    const audio = audioCache[type];
    if (audio) {
        currentAudio = audio;
        audio.currentTime = 0;

        // Update volume on track play
        const vol = volumeSlider ? parseFloat(volumeSlider.value) : 1.0;
        audio.volume = vol;

        audio.play().catch(err => {
            console.log("Browser blocked auto-play sound: ", err);
        });
        lastPlayedTime[type] = now;
    }
}
