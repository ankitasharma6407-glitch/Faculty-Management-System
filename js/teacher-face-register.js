(function () {
    "use strict";

    const API_BASE = "http://127.0.0.1:5000/api";

    const MODEL_URL =
        "https://justadudewhohacks.github.io/face-api.js/models";

    const ACCESS_TOKEN_KEY = "fmps_access_token";
    const REFRESH_TOKEN_KEY = "fmps_refresh_token";
    const USER_KEY = "fmps_user";
    const REQUIRED_SAMPLES = 3;

    const state = {
        cameraStream: null,
        samples: [],
        modelsPromise: null,
        capturing: false,
        profileLoaded: false,
        faceRegistered: false,
        teacher: null
    };

    document.addEventListener("DOMContentLoaded", init);

    function byId(id) {
        return document.getElementById(id);
    }

    function getToken() {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    }

    function clearSession() {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
    }

    function getCachedUser() {
        try {
            return JSON.parse(
                localStorage.getItem(USER_KEY) || "null"
            );
        } catch (error) {
            return null;
        }
    }

    async function apiRequest(path, options = {}) {
        const token = getToken();

        if (!token) {
            window.location.replace("teacher-login.html");
            throw new Error("Please log in again.");
        }

        const response = await fetch(API_BASE + path, {
            ...options,

            headers: {
                Accept: "application/json",

                Authorization:
                    "Bearer " + token,

                ...(options.body
                    ? {
                        "Content-Type":
                            "application/json"
                    }
                    : {}),

                ...(options.headers || {})
            }
        });

        const result = await response
            .json()
            .catch(function () {
                return {};
            });

        if (response.status === 401) {
            clearSession();

            window.location.replace(
                "teacher-login.html"
            );

            throw new Error(
                "Session expired. Please log in again."
            );
        }

        if (
            !response.ok ||
            result.success === false
        ) {
            const error = new Error(
                result.message ||
                result.error ||
                "Request failed."
            );

            error.status = response.status;

            throw error;
        }

        return result;
    }

    function valueFrom(
        sources,
        keys,
        fallback = "--"
    ) {
        for (const source of sources) {
            if (
                !source ||
                typeof source !== "object"
            ) {
                continue;
            }

            for (const key of keys) {
                const value = source[key];

                if (
                    value !== undefined &&
                    value !== null &&
                    value !== ""
                ) {
                    return value;
                }
            }
        }

        return fallback;
    }

    function getDepartmentName(value) {
        if (
            value &&
            typeof value === "object"
        ) {
            return (
                value.name ||
                value.department_name ||
                "--"
            );
        }

        return value || "--";
    }

    function setText(id, value) {
        const element = byId(id);

        if (element) {
            element.textContent = value;
        }
    }

    function setBadge(
        element,
        text,
        className
    ) {
        if (!element) {
            return;
        }

        element.textContent = text;
        element.className =
            "badge " + className;
    }

    function showModal(
        modalId,
        messageId,
        message
    ) {
        const messageElement =
            byId(messageId);

        if (messageElement) {
            messageElement.textContent =
                message;
        }

        const modalElement =
            byId(modalId);

        if (
            modalElement &&
            window.bootstrap
        ) {
            window.bootstrap.Modal
                .getOrCreateInstance(
                    modalElement
                )
                .show();
        } else {
            window.alert(message);
        }
    }

    function showError(message) {
        showModal(
            "formErrorModal",
            "formErrorMessage",
            message
        );
    }

    function showCameraError(message) {
        showModal(
            "cameraErrorModal",
            "cameraErrorMessage",
            message
        );
    }

    function initializeTheme() {
        const themeToggle =
            byId("themeToggle");

        if (!themeToggle) {
            return;
        }

        const savedTheme =
            localStorage.getItem(
                "teacherFaceRegisterTheme"
            );

        if (savedTheme === "dark") {
            document.body.classList.add(
                "dark"
            );
        }

        function updateIcon() {
            const icon =
                themeToggle.querySelector("i");

            if (!icon) {
                return;
            }

            icon.className =
                document.body.classList
                    .contains("dark")
                    ? "fa-solid fa-sun"
                    : "fa-solid fa-moon";
        }

        themeToggle.addEventListener(
            "click",
            function () {
                document.body.classList.toggle(
                    "dark"
                );

                localStorage.setItem(
                    "teacherFaceRegisterTheme",

                    document.body.classList
                        .contains("dark")
                        ? "dark"
                        : "light"
                );

                updateIcon();
            }
        );

        updateIcon();
    }

    async function loadTeacherAccount() {
        const startButton =
            byId("startCameraBtn");

        if (startButton) {
            startButton.disabled = true;
        }

        try {
            const results =
                await Promise.all([
                    apiRequest(
                        "/teachers/me/dashboard"
                    ),

                    apiRequest(
                        "/auth/face/status"
                    )
                ]);

            const dashboardResult =
                results[0];

            const faceStatusResult =
                results[1];

            const dashboardData =
                dashboardResult.data ||
                dashboardResult ||
                {};

            const faceData =
                faceStatusResult.data ||
                faceStatusResult ||
                {};

            const cachedUser =
                getCachedUser() || {};

            const teacher =
                dashboardData.teacher || {};

            const user =
                dashboardData.user ||
                cachedUser ||
                {};

            if (
                user.role &&
                String(user.role)
                    .toLowerCase() !==
                    "teacher"
            ) {
                throw new Error(
                    "Only a logged-in Teacher can register a Teacher face."
                );
            }

            const sources = [
                teacher,
                user,
                user.profile,
                user.teacher
            ];

            const department =
                getDepartmentName(
                    valueFrom(
                        sources,

                        [
                            "department",
                            "department_name",
                            "dept_name"
                        ],

                        "--"
                    )
                );

            state.teacher = {
                name: valueFrom(
                    sources,

                    [
                        "full_name",
                        "name",
                        "username"
                    ],

                    "Teacher"
                ),

                code: valueFrom(
                    sources,

                    [
                        "teacher_code",
                        "employee_id",
                        "username",
                        "id"
                    ],

                    "--"
                ),

                email: valueFrom(
                    sources,
                    ["email"],
                    "--"
                ),

                department: department
            };

            state.profileLoaded = true;

            state.faceRegistered =
                Boolean(faceData.registered);

            renderTeacherAccount();
            renderRegistrationStatus();

            if (startButton) {
                startButton.disabled = false;
            }
        } catch (error) {
            console.error(
                "Teacher account load error:",
                error
            );

            setText(
                "accountTeacherName",
                "Unable to load"
            );

            setText(
                "accountTeacherId",
                "--"
            );

            setText(
                "accountTeacherEmail",
                "--"
            );

            setText(
                "accountTeacherDepartment",
                "--"
            );

            if (error.status !== 401) {
                showError(
                    error.message ||
                    "Unable to load logged-in Teacher details."
                );
            }
        }
    }

    function renderTeacherAccount() {
        const teacher =
            state.teacher || {};

        setText(
            "accountTeacherName",
            teacher.name || "Teacher"
        );

        setText(
            "accountTeacherId",
            teacher.code || "--"
        );

        setText(
            "accountTeacherEmail",
            teacher.email || "--"
        );

        setText(
            "accountTeacherDepartment",
            teacher.department || "--"
        );

        setText(
            "successTeacherName",
            teacher.name || "Teacher"
        );

        setText(
            "successTeacherId",
            teacher.code || "--"
        );

        setText(
            "successDepartment",
            teacher.department || "--"
        );
    }

    function renderRegistrationStatus() {
        const status =
            byId("registrationStatus");

        if (
            state.samples.length ===
            REQUIRED_SAMPLES
        ) {
            setBadge(
                status,

                state.faceRegistered
                    ? "Ready to Update"
                    : "Ready to Register",

                "bg-primary"
            );

            return;
        }

        setBadge(
            status,

            state.faceRegistered
                ? "Registered"
                : "Not Registered",

            state.faceRegistered
                ? "bg-success"
                : "bg-danger"
        );
    }

    async function loadModels() {
        if (!window.faceapi) {
            throw new Error(
                "Face recognition library did not load. Check internet connection."
            );
        }

        if (!state.modelsPromise) {
            state.modelsPromise =
                Promise.all([
                    window.faceapi.nets
                        .tinyFaceDetector
                        .loadFromUri(
                            MODEL_URL
                        ),

                    window.faceapi.nets
                        .faceLandmark68Net
                        .loadFromUri(
                            MODEL_URL
                        ),

                    window.faceapi.nets
                        .faceRecognitionNet
                        .loadFromUri(
                            MODEL_URL
                        )
                ]);
        }

        return state.modelsPromise;
    }

    async function startCamera() {
        if (!state.profileLoaded) {
            showError(
                "Logged-in Teacher details are still loading."
            );

            return;
        }

        if (state.cameraStream) {
            return;
        }

        const video =
            byId("registerVideo");

        try {
            if (
                !navigator.mediaDevices ||
                !navigator.mediaDevices
                    .getUserMedia
            ) {
                throw new Error(
                    "This browser does not support camera access."
                );
            }

            setBadge(
                byId("cameraStatus"),
                "Loading AI...",
                "bg-warning text-dark"
            );

            byId(
                "startCameraBtn"
            ).disabled = true;

            await loadModels();

            state.cameraStream =
                await navigator.mediaDevices
                    .getUserMedia({
                        video: {
                            facingMode:
                                "user",

                            width: {
                                ideal: 1280
                            },

                            height: {
                                ideal: 720
                            }
                        },

                        audio: false
                    });

            video.srcObject =
                state.cameraStream;

            await video.play();

            video.style.display =
                "block";

            byId(
                "cameraPlaceholder"
            ).style.display = "none";

            byId(
                "faceGuide"
            ).style.display = "block";

            byId(
                "cameraLiveBadge"
            ).style.display = "flex";

            byId(
                "cameraMessage"
            ).style.display = "block";

            byId(
                "cameraMessage"
            ).textContent =
                "Position your face inside the frame";

            byId(
                "captureFaceBtn"
            ).disabled = false;

            byId(
                "stopCameraBtn"
            ).disabled = false;

            byId(
                "retakeBtn"
            ).disabled =
                state.samples.length === 0;

            setBadge(
                byId("cameraStatus"),
                "Online",
                "bg-success"
            );

            setBadge(
                byId(
                    "faceDetectionStatus"
                ),

                "Ready",

                "bg-info text-dark"
            );
        } catch (error) {
            console.error(
                "Camera/model error:",
                error
            );

            byId(
                "startCameraBtn"
            ).disabled = false;

            setBadge(
                byId("cameraStatus"),
                "Unavailable",
                "bg-danger"
            );

            showCameraError(
                error.message ||
                "Camera could not start."
            );
        }
    }

    function createPreview(video) {
        const canvas =
            byId("registerCanvas");

        canvas.width =
            video.videoWidth;

        canvas.height =
            video.videoHeight;

        const context =
            canvas.getContext("2d");

        context.save();

        context.translate(
            canvas.width,
            0
        );

        context.scale(-1, 1);

        context.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );

        context.restore();

        return canvas.toDataURL(
            "image/jpeg",
            0.88
        );
    }

    async function captureFace() {
        const video =
            byId("registerVideo");

        if (
            !state.cameraStream ||
            !video.videoWidth
        ) {
            showCameraError(
                "Please start the camera first."
            );

            return;
        }

        if (
            state.capturing ||
            state.samples.length >=
                REQUIRED_SAMPLES
        ) {
            return;
        }

        state.capturing = true;

        byId(
            "captureFaceBtn"
        ).disabled = true;

        byId(
            "scanLine"
        ).style.display = "block";

        byId(
            "cameraMessage"
        ).textContent =
            "AI is checking your face...";

        setBadge(
            byId(
                "faceDetectionStatus"
            ),

            "Detecting...",

            "bg-warning text-dark"
        );

        setBadge(
            byId(
                "imageQualityStatus"
            ),

            "Checking...",

            "bg-warning text-dark"
        );

        try {
            const detections =
                await window.faceapi
                    .detectAllFaces(
                        video,

                        new window.faceapi
                            .TinyFaceDetectorOptions({
                                inputSize: 320,
                                scoreThreshold:
                                    0.5
                            })
                    )
                    .withFaceLandmarks()
                    .withFaceDescriptors();

            if (!detections.length) {
                throw new Error(
                    "Face was not detected. Improve lighting and look straight."
                );
            }

            if (
                detections.length !== 1
            ) {
                throw new Error(
                    "Only one person should be visible in the camera."
                );
            }

            const descriptor =
                Array.from(
                    detections[0]
                        .descriptor
                );

            if (
                descriptor.length !== 128
            ) {
                throw new Error(
                    "A valid face descriptor could not be generated."
                );
            }

            state.samples.push({
                descriptor: descriptor,

                preview:
                    createPreview(video)
            });

            setBadge(
                byId(
                    "faceDetectionStatus"
                ),

                "Face Detected",

                "bg-success"
            );

            setBadge(
                byId(
                    "imageQualityStatus"
                ),

                "Good",

                "bg-success"
            );

            setQuality(
                "Good",
                "Good",
                "Clear",
                "Excellent"
            );

            byId(
                "cameraMessage"
            ).textContent =
                "Sample " +
                state.samples.length +
                " captured successfully";

            updateSampleUI();
        } catch (error) {
            console.error(
                "Face capture error:",
                error
            );

            setBadge(
                byId(
                    "faceDetectionStatus"
                ),

                "Try Again",

                "bg-danger"
            );

            setBadge(
                byId(
                    "imageQualityStatus"
                ),

                "Failed",

                "bg-danger"
            );

            showCameraError(
                error.message ||
                "Unable to capture face."
            );
        } finally {
            state.capturing = false;

            byId(
                "scanLine"
            ).style.display = "none";

            byId(
                "captureFaceBtn"
            ).disabled =
                !state.cameraStream ||
                state.samples.length >=
                    REQUIRED_SAMPLES;
        }
    }

    function setQuality(
        position,
        lighting,
        clarity,
        overall
    ) {
        const values = [
            [
                "facePositionQuality",
                position
            ],

            [
                "lightingQuality",
                lighting
            ],

            [
                "clarityQuality",
                clarity
            ],

            [
                "overallQuality",
                overall
            ]
        ];

        values.forEach(
            function (entry) {
                const element =
                    byId(entry[0]);

                if (!element) {
                    return;
                }

                element.textContent =
                    entry[1];

                element.className =
                    entry[1] ===
                    "Waiting"
                        ? "text-secondary"
                        : "text-success";
            }
        );
    }

    function updateSampleUI() {
        const total =
            state.samples.length;

        const progress =
            Math.round(
                (
                    total /
                    REQUIRED_SAMPLES
                ) * 100
            );

        setText(
            "sampleCount",
            total
        );

        setBadge(
            byId("sampleStatus"),

            total +
                " / " +
                REQUIRED_SAMPLES,

            total === REQUIRED_SAMPLES
                ? "bg-success"
                : total > 0
                    ? "bg-warning text-dark"
                    : "bg-secondary"
        );

        setText(
            "registrationProgressText",
            progress + "%"
        );

        const progressBar =
            byId(
                "registrationProgressBar"
            );

        progressBar.style.width =
            progress + "%";

        progressBar.className =
            "progress-bar " +
            (
                progress === 100
                    ? "bg-success"
                    : progress > 0
                        ? "bg-warning"
                        : ""
            );

        byId(
            "capturedPreview"
        ).style.display =
            total
                ? "block"
                : "none";

        for (
            let index = 0;
            index < REQUIRED_SAMPLES;
            index += 1
        ) {
            const image =
                byId(
                    "sampleImage" +
                    (index + 1)
                );

            if (!image) {
                continue;
            }

            if (state.samples[index]) {
                image.src =
                    state.samples[
                        index
                    ].preview;
            } else {
                image.removeAttribute(
                    "src"
                );
            }
        }

        byId(
            "retakeBtn"
        ).disabled =
            total === 0;

        byId(
            "registerFaceBtn"
        ).disabled =
            total !==
                REQUIRED_SAMPLES ||
            !state.profileLoaded;

        renderRegistrationStatus();
    }

    function retakeLastSample() {
        if (!state.samples.length) {
            return;
        }

        state.samples.pop();

        updateSampleUI();

        if (state.cameraStream) {
            byId(
                "captureFaceBtn"
            ).disabled = false;

            byId(
                "cameraMessage"
            ).textContent =
                "Capture a replacement face sample";
        }

        if (!state.samples.length) {
            setQuality(
                "Waiting",
                "Waiting",
                "Waiting",
                "Waiting"
            );

            setBadge(
                byId(
                    "imageQualityStatus"
                ),

                "Pending",

                "bg-secondary"
            );
        }
    }

    function stopCamera() {
        if (state.cameraStream) {
            state.cameraStream
                .getTracks()
                .forEach(
                    function (track) {
                        track.stop();
                    }
                );
        }

        state.cameraStream = null;

        const video =
            byId("registerVideo");

        video.pause();
        video.srcObject = null;
        video.style.display = "none";

        byId(
            "cameraPlaceholder"
        ).style.display = "block";

        byId(
            "faceGuide"
        ).style.display = "none";

        byId(
            "scanLine"
        ).style.display = "none";

        byId(
            "cameraLiveBadge"
        ).style.display = "none";

        byId(
            "cameraMessage"
        ).style.display = "none";

        byId(
            "startCameraBtn"
        ).disabled =
            !state.profileLoaded;

        byId(
            "captureFaceBtn"
        ).disabled = true;

        byId(
            "stopCameraBtn"
        ).disabled = true;

        setBadge(
            byId("cameraStatus"),
            "Offline",
            "bg-secondary"
        );

        setBadge(
            byId(
                "faceDetectionStatus"
            ),

            "Waiting...",

            "bg-warning text-dark"
        );
    }

    function averageDescriptors() {
        const average =
            new Array(128).fill(0);

        state.samples.forEach(
            function (sample) {
                sample.descriptor
                    .forEach(
                        function (
                            value,
                            index
                        ) {
                            average[index] +=
                                Number(value);
                        }
                    );
            }
        );

        return average.map(
            function (value) {
                return (
                    value /
                    state.samples.length
                );
            }
        );
    }

    async function registerFace() {
        if (!state.profileLoaded) {
            showError(
                "Logged-in Teacher details could not be verified."
            );

            return;
        }

        if (
            state.samples.length !==
            REQUIRED_SAMPLES
        ) {
            setText(
                "sampleModalCount",

                state.samples.length +
                    " / " +
                    REQUIRED_SAMPLES
            );

            const modal =
                byId(
                    "sampleErrorModal"
                );

            if (
                modal &&
                window.bootstrap
            ) {
                window.bootstrap.Modal
                    .getOrCreateInstance(
                        modal
                    )
                    .show();
            }

            return;
        }

        const button =
            byId("registerFaceBtn");

        button.disabled = true;

        button.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2"></span>' +
            (
                state.faceRegistered
                    ? "Updating Face..."
                    : "Registering Face..."
            );

        setBadge(
            byId(
                "registrationStatus"
            ),

            "Processing...",

            "bg-warning text-dark"
        );

        try {
            await apiRequest(
                "/auth/face/register",
                {
                    method: "POST",

                    body:
                        JSON.stringify({
                            descriptor:
                                averageDescriptors()
                        })
                }
            );

            state.faceRegistered =
                true;

            renderTeacherAccount();

            stopCamera();

            setBadge(
                byId(
                    "registrationStatus"
                ),

                "Registered",

                "bg-success"
            );

            setBadge(
                byId(
                    "faceDetectionStatus"
                ),

                "Completed",

                "bg-success"
            );

            button.innerHTML =
                '<i class="fa-solid fa-circle-check me-2"></i>' +
                "Face Registered";

            const successModal =
                byId(
                    "registrationSuccessModal"
                );

            if (
                successModal &&
                window.bootstrap
            ) {
                window.bootstrap.Modal
                    .getOrCreateInstance(
                        successModal
                    )
                    .show();
            }
        } catch (error) {
            console.error(
                "Face registration error:",
                error
            );

            setBadge(
                byId(
                    "registrationStatus"
                ),

                "Failed",

                "bg-danger"
            );

            button.disabled = false;

            button.innerHTML =
                '<i class="fa-solid fa-face-viewfinder me-2"></i>' +
                (
                    state.faceRegistered
                        ? "Update My Face"
                        : "Register My Face"
                );

            showError(
                error.message ||
                "Face registration failed."
            );
        }
    }

    function bindEvents() {
        const startButton =
            byId("startCameraBtn");

        const captureButton =
            byId("captureFaceBtn");

        const retakeButton =
            byId("retakeBtn");

        const stopButton =
            byId("stopCameraBtn");

        const registerButton =
            byId("registerFaceBtn");

        if (startButton) {
            startButton.addEventListener(
                "click",
                startCamera
            );
        }

        if (captureButton) {
            captureButton.addEventListener(
                "click",
                captureFace
            );
        }

        if (retakeButton) {
            retakeButton.addEventListener(
                "click",
                retakeLastSample
            );
        }

        if (stopButton) {
            stopButton.addEventListener(
                "click",
                stopCamera
            );
        }

        if (registerButton) {
            registerButton.addEventListener(
                "click",
                registerFace
            );
        }

        window.addEventListener(
            "beforeunload",
            function () {
                if (
                    state.cameraStream
                ) {
                    state.cameraStream
                        .getTracks()
                        .forEach(
                            function (
                                track
                            ) {
                                track.stop();
                            }
                        );
                }
            }
        );
    }

    function init() {
        initializeTheme();

        if (!getToken()) {
            window.location.replace(
                "teacher-login.html"
            );

            return;
        }

        bindEvents();
        updateSampleUI();
        loadTeacherAccount();
    }
})();