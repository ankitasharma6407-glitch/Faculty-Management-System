

(function () {
    "use strict";

    const API_BASE = "http://127.0.0.1:5000/api";
    const SERVER_BASE = "http://127.0.0.1:5000";
    const MODEL_URL =
        "https://justadudewhohacks.github.io/face-api.js/models";

    const ACCESS_TOKEN_KEY = "fmps_access_token";
    const REFRESH_TOKEN_KEY = "fmps_refresh_token";
    const USER_KEY = "fmps_user";

    let cameraStream = null;
    let modelsPromise = null;
    let scanning = false;
    let authenticatedUser = null;

    function byId(id) {
        return document.getElementById(id);
    }

    function setStatus(element, text, className) {
        if (!element) return;
        element.textContent = text;
        element.className = "status-badge " + className;
    }

    async function loadModels() {
        if (!window.faceapi) {
            throw new Error(
                "Face recognition library load nahi hui. Internet connection check karo."
            );
        }

        if (!modelsPromise) {
            modelsPromise = Promise.all([
                window.faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                window.faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                window.faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
            ]);
        }

        return modelsPromise;
    }

    async function faceLogin(descriptor) {
        const response = await fetch(API_BASE + "/auth/face/login", {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                descriptor: descriptor,
                role: "teacher"
            })
        });

        const result = await response.json().catch(function () {
            return {};
        });

        if (!response.ok || result.success === false) {
            throw new Error(result.message || "Teacher face login failed");
        }

        const authData = result.data || result;
        const user = authData.user || {};

        if (String(user.role || "").toLowerCase() !== "teacher") {
            throw new Error(
                "Recognized face Teacher account ka nahi hai."
            );
        }

        if (!authData.access_token || !authData.refresh_token) {
            throw new Error("Backend se JWT tokens receive nahi hue.");
        }

        localStorage.setItem(ACCESS_TOKEN_KEY, authData.access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, authData.refresh_token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));

        return {
            user: user,
            distance: Number(authData.face_distance)
        };
    }

    function profileValue(user, keys) {
        const sources = [user, user?.profile, user?.teacher];

        for (const source of sources) {
            if (!source || typeof source !== "object") continue;

            for (const key of keys) {
                const value = source[key];
                if (value !== undefined && value !== null && value !== "") {
                    return value;
                }
            }
        }

        return "";
    }

    function photoUrl(value) {
        const path = String(value || "").replace(/\\/g, "/").trim();

        if (/^https?:\/\//i.test(path)) return path;

        const filename = path.replace(/^\/?uploads\//i, "");
        return SERVER_BASE + "/uploads/" + filename.replace(/^\/+/, "");
    }

    function showRecognizedTeacher(user, distance) {
        const waiting = byId("recognitionWaiting");
        const result = byId("recognizedResult");

        if (waiting) waiting.style.display = "none";
        if (result) result.style.display = "block";

        const name = profileValue(user, [
            "full_name", "name", "username"
        ]) || "Teacher";
        const teacherCode = profileValue(user, [
            "teacher_code", "employee_id", "username", "id"
        ]) || "-";
        const department = profileValue(user, [
            "department", "department_name"
        ]);
        const designation = profileValue(user, [
            "designation"
        ]) || "Faculty Member";
        const photo = profileValue(user, [
            "photo_url", "profile_photo", "image_url"
        ]);

        byId("recognizedTeacherName").textContent = name;
        byId("recognizedTeacherRole").textContent = designation;
        byId("recognizedTeacherId").textContent = teacherCode;
        byId("recognizedDepartment").textContent =
            typeof department === "object"
                ? department.name || "-"
                : department || "-";

        const image = byId("recognizedTeacherPhoto");
        if (image) {
            image.src = photo
                ? photoUrl(photo)
                : "../../images/default-profile.png";
            image.onerror = function () {
                image.onerror = null;
                image.src = "../../images/default-profile.png";
            };
        }

        const validDistance = Number.isFinite(distance) ? distance : 1;
        const confidence = Math.max(
            0,
            Math.min(100, (1 - validDistance) * 100)
        );

        byId("confidenceText").textContent = confidence.toFixed(1) + "%";
        byId("confidenceProgress").style.width = confidence + "%";
    }

    document.addEventListener("DOMContentLoaded", function () {
        const video = byId("faceLoginVideo");
        const placeholder = byId("scannerPlaceholder");
        const liveBadge = byId("liveCameraBadge");
        const faceFrame = byId("videoFaceFrame");
        const scanLine = byId("videoScanLine");

        const startButton = byId("startCameraBtn");
        const scanButton = byId("scanFaceBtn");
        const retryButton = byId("retryFaceBtn");
        const stopButton = byId("stopCameraBtn");
        const continueButton = byId("continueDashboardBtn");

        const cameraStatus = byId("cameraStatus");
        const faceStatus = byId("faceDetectionStatus");
        const recognitionStatus = byId("aiRecognitionStatus");
        const roleStatus = byId("roleVerificationStatus");
        const authenticationStatus = byId("authenticationStatus");

        function resetResult() {
            authenticatedUser = null;
            scanning = false;

            if (scanLine) scanLine.style.display = "none";
            if (byId("recognitionWaiting")) {
                byId("recognitionWaiting").style.display = "flex";
            }
            if (byId("recognizedResult")) {
                byId("recognizedResult").style.display = "none";
            }

            setStatus(
                faceStatus,
                cameraStream ? "Ready" : "Waiting...",
                cameraStream ? "status-waiting" : "status-offline"
            );
            setStatus(recognitionStatus, "Pending", "status-pending");
            setStatus(roleStatus, "Pending", "status-pending");
            setStatus(
                authenticationStatus,
                "Not Authenticated",
                "status-failed"
            );

            scanButton.disabled = !cameraStream;
        }

        function stopCamera() {
            if (cameraStream) {
                cameraStream.getTracks().forEach(function (track) {
                    track.stop();
                });
            }

            cameraStream = null;
            video.pause();
            video.srcObject = null;
            video.style.display = "none";

            if (placeholder) placeholder.style.display = "flex";
            if (liveBadge) liveBadge.style.display = "none";
            if (faceFrame) faceFrame.style.display = "none";
            if (scanLine) scanLine.style.display = "none";

            startButton.disabled = false;
            scanButton.disabled = true;
            retryButton.disabled = true;
            stopButton.disabled = true;

            setStatus(cameraStatus, "Offline", "status-offline");

            if (!authenticatedUser) resetResult();
        }

        async function startCamera() {
            if (cameraStream) return;

            try {
                if (!navigator.mediaDevices?.getUserMedia) {
                    throw new Error("Browser camera access support nahi karta.");
                }

                startButton.disabled = true;
                setStatus(cameraStatus, "Loading AI...", "status-waiting");

                await loadModels();

                cameraStream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: "user",
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    },
                    audio: false
                });

                video.srcObject = cameraStream;
                await video.play();
                video.style.display = "block";

                if (placeholder) placeholder.style.display = "none";
                if (liveBadge) liveBadge.style.display = "flex";
                if (faceFrame) faceFrame.style.display = "block";

                scanButton.disabled = false;
                retryButton.disabled = false;
                stopButton.disabled = false;

                setStatus(cameraStatus, "Online", "status-success");
                setStatus(faceStatus, "Ready", "status-waiting");
            } catch (error) {
                console.error("Teacher face camera error:", error);
                setStatus(cameraStatus, "Unavailable", "status-failed");
                startButton.disabled = false;
                window.alert(error.message || "Camera/model load failed.");
            }
        }

        async function scanFace() {
            if (!cameraStream || !video.videoWidth) {
                window.alert("Pehle camera start karo.");
                return;
            }

            if (scanning) return;

            scanning = true;
            scanButton.disabled = true;
            if (scanLine) scanLine.style.display = "block";

            setStatus(faceStatus, "Detecting...", "status-waiting");
            setStatus(recognitionStatus, "Matching...", "status-waiting");
            setStatus(roleStatus, "Waiting...", "status-waiting");
            setStatus(authenticationStatus, "Verifying...", "status-waiting");

            try {
                const detections = await window.faceapi
                    .detectAllFaces(
                        video,
                        new window.faceapi.TinyFaceDetectorOptions({
                            inputSize: 320,
                            scoreThreshold: 0.5
                        })
                    )
                    .withFaceLandmarks()
                    .withFaceDescriptors();

                if (!detections.length) {
                    throw new Error(
                        "Face detect nahi hua. Light improve karke seedha dekho."
                    );
                }

                if (detections.length !== 1) {
                    throw new Error(
                        "Camera frame mein sirf ek person hona chahiye."
                    );
                }

                setStatus(faceStatus, "Detected", "status-success");

                const descriptor = Array.from(detections[0].descriptor);
                const loginResult = await faceLogin(descriptor);

                authenticatedUser = loginResult.user;
                setStatus(recognitionStatus, "Recognized", "status-success");
                setStatus(roleStatus, "Teacher Verified", "status-success");
                setStatus(
                    authenticationStatus,
                    "Authenticated",
                    "status-success"
                );

                showRecognizedTeacher(
                    loginResult.user,
                    loginResult.distance
                );
                stopCamera();
            } catch (error) {
                console.error("Teacher face login error:", error);
                setStatus(
                    recognitionStatus,
                    "Not Recognized",
                    "status-failed"
                );
                setStatus(roleStatus, "Not Verified", "status-failed");
                setStatus(
                    authenticationStatus,
                    "Login Failed",
                    "status-failed"
                );
                window.alert(error.message || "Face login failed.");
            } finally {
                scanning = false;
                if (scanLine) scanLine.style.display = "none";
                if (cameraStream) scanButton.disabled = false;
            }
        }

        startButton.addEventListener("click", startCamera);
        scanButton.addEventListener("click", scanFace);
        retryButton.addEventListener("click", resetResult);
        stopButton.addEventListener("click", stopCamera);

        continueButton.addEventListener("click", function () {
            if (!authenticatedUser) {
                window.alert("Pehle Teacher face authentication complete karo.");
                return;
            }
            window.location.href = "teacher-dashboard.html";
        });

        const lightButton = byId("lightModeBtn");
        const darkButton = byId("darkModeBtn");

        function applyTheme(theme) {
            const light = theme === "light";
            document.body.classList.toggle("light-mode", light);
            lightButton?.classList.toggle("active", light);
            darkButton?.classList.toggle("active", !light);
            localStorage.setItem("teacherFaceLoginTheme", theme);
        }

        lightButton?.addEventListener("click", function () {
            applyTheme("light");
        });
        darkButton?.addEventListener("click", function () {
            applyTheme("dark");
        });

        applyTheme(
            localStorage.getItem("teacherFaceLoginTheme") || "dark"
        );

        resetResult();

        window.addEventListener("beforeunload", function () {
            if (cameraStream) {
                cameraStream.getTracks().forEach(function (track) {
                    track.stop();
                });
            }
        });
    });
})();
