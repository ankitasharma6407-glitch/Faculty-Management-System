// ============================================================
// FMPS - Teacher Leave Request
// ============================================================

(() => {
    "use strict";

    const API_BASE = "http://127.0.0.1:5000/api";
    const TOKEN_KEYS = [
        "fmps_access_token",
        "access_token",
        "token"
    ];

    const state = {
        leaves: []
    };

    function getToken() {
        for (const key of TOKEN_KEYS) {
            const token = localStorage.getItem(key);
            if (token) return token;
        }
        return null;
    }

    async function apiRequest(path, options = {}) {
        const token = getToken();

        if (!token) {
            window.location.href = "teacher-login.html";
            throw new Error("Please log in again");
        }

        const isFormData = options.body instanceof FormData;

        const response = await fetch(API_BASE + path, {
            ...options,
            headers: {
                ...(
                    isFormData
                        ? {}
                        : { "Content-Type": "application/json" }
                ),
                Authorization: `Bearer ${token}`,
                ...(options.headers || {})
            }
        });

        let result = {};

        try {
            result = await response.json();
        } catch (error) {
            result = {};
        }

        if (response.status === 401) {
            TOKEN_KEYS.forEach(key => localStorage.removeItem(key));
            window.location.href = "teacher-login.html";
            throw new Error("Session expired. Please log in again.");
        }

        if (!response.ok || result.success === false) {
            throw new Error(
                result.message || "Unable to complete the request"
            );
        }

        return result;
    }

    function formatDate(value) {
        if (!value) return "--";

        const date = new Date(`${value.slice(0, 10)}T00:00:00`);

        return date.toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric"
        });
    }

    function calculateDays(startValue, endValue) {
        if (!startValue || !endValue) return 0;

        const start = new Date(`${startValue}T00:00:00`);
        const end = new Date(`${endValue}T00:00:00`);

        if (end < start) return -1;

        return Math.floor(
            (end.getTime() - start.getTime()) / 86400000
        ) + 1;
    }

    function requestNumber(leave) {
        const year = leave.created_at
            ? new Date(leave.created_at).getFullYear()
            : new Date().getFullYear();

        return `LV-${year}-${String(leave.id).padStart(3, "0")}`;
    }

    function statusLabel(status) {
        const labels = {
            pending: "Pending",
            approved: "Approved",
            rejected: "Rejected",
            cancelled: "Cancelled"
        };

        return labels[status] || status || "Pending";
    }

    function statusIcon(status) {
        const icons = {
            pending: "fa-clock",
            approved: "fa-circle-check",
            rejected: "fa-circle-xmark",
            cancelled: "fa-ban"
        };

        return icons[status] || "fa-clock";
    }

    function leaveTypeIcon(type) {
        const icons = {
            "Casual Leave": "fa-mug-hot",
            "Medical Leave": "fa-kit-medical",
            "Earned Leave": "fa-umbrella-beach",
            Other: "fa-ellipsis"
        };

        return icons[type] || "fa-calendar-day";
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }

    function showAlert(message) {
        window.alert(message);
    }

    function getUploadStatusElement() {
        const uploadBox = document.getElementById("leaveUploadBox");
        if (!uploadBox) return null;

        let status = document.getElementById("leaveUploadStatus");

        if (!status) {
            status = document.createElement("div");
            status.id = "leaveUploadStatus";
            status.setAttribute("role", "status");
            status.style.marginTop = "10px";
            status.style.fontSize = "13px";
            status.style.fontWeight = "600";
            status.style.textAlign = "center";
            uploadBox.insertAdjacentElement("afterend", status);
        }

        return status;
    }

    function setUploadStatus(type, message) {
        const uploadBox = document.getElementById("leaveUploadBox");
        const status = getUploadStatusElement();
        if (!uploadBox || !status) return;

        const styles = {
            idle: {
                color: "#73788a",
                border: "",
                background: ""
            },
            selected: {
                color: "#2563eb",
                border: "2px solid #3b82f6",
                background: "rgba(59, 130, 246, .08)"
            },
            uploading: {
                color: "#d97706",
                border: "2px solid #f59e0b",
                background: "rgba(245, 158, 11, .08)"
            },
            success: {
                color: "#16a34a",
                border: "2px solid #22c55e",
                background: "rgba(34, 197, 94, .08)"
            },
            error: {
                color: "#dc2626",
                border: "2px solid #ef4444",
                background: "rgba(239, 68, 68, .08)"
            }
        };

        const style = styles[type] || styles.idle;
        status.style.color = style.color;
        status.innerHTML = message;
        uploadBox.style.border = style.border;
        uploadBox.style.background = style.background;
    }

    function updateDateSummary() {
        const startInput = document.getElementById("leaveStartDate");
        const endInput = document.getElementById("leaveEndDate");

        if (!startInput || !endInput) return 0;

        const days = calculateDays(startInput.value, endInput.value);

        setText("summaryStartDate", formatDate(startInput.value));
        setText("summaryEndDate", formatDate(endInput.value));
        setText(
            "summaryTotalDays",
            days < 0
                ? "Invalid"
                : `${days} ${days === 1 ? "Day" : "Days"}`
        );

        return days;
    }

    function resetFormSummary() {
        setText("summaryStartDate", "--");
        setText("summaryEndDate", "--");
        setText("summaryTotalDays", "0 Days");
        setText("reasonCharacterCount", "0 / 500");
        setText("uploadFileName", "Upload Supporting Document");
        setUploadStatus("idle", "");
    }

    function renderSummary(summary = {}) {
        setText("totalLeaveCount", summary.total_requests ?? 0);
        setText("usedLeaveCount", summary.approved_requests ?? 0);
        setText("remainingLeaveCount", summary.rejected_requests ?? 0);
        setText("pendingLeaveCount", summary.pending_requests ?? 0);

        renderLeaveBalances();
    }

    function renderLeaveBalances() {
        const items = document.querySelectorAll(".balance-item");
        const statuses = [
            { key: "pending", label: "Pending Requests" },
            { key: "approved", label: "Approved Requests" },
            { key: "rejected", label: "Rejected Requests" }
        ];
        const total = state.leaves.length;

        items.forEach((item, index) => {
            const status = statuses[index];
            if (!status) return;

            const count = state.leaves.filter(
                leave => leave.status === status.key
            ).length;
            const percentage = total
                ? Math.round((count / total) * 100)
                : 0;

            const heading = item.querySelector(".balance-header span");
            const text = item.querySelector(".balance-header small");
            const bar = item.querySelector(".progress-bar");

            if (heading) heading.textContent = status.label;
            if (text) {
                text.textContent = `${count} request${count === 1 ? "" : "s"}`;
            }

            if (bar) {
                bar.style.width = `${percentage}%`;
            }
        });
    }

    function renderHistory() {
        const tbody = document.getElementById("leaveHistoryBody");
        const filter = document.getElementById("leaveStatusFilter");

        if (!tbody) return;

        const selectedStatus = filter?.value || "all";
        const visibleLeaves = state.leaves.filter(leave => (
            selectedStatus === "all" || leave.status === selectedStatus
        ));

        if (!visibleLeaves.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        No leave requests found.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = visibleLeaves.map(leave => {
            const days = calculateDays(
                leave.start_date,
                leave.end_date
            );
            const status = leave.status || "pending";

            return `
                <tr data-status="${escapeHtml(status)}">
                    <td>
                        <strong>#${requestNumber(leave)}</strong>
                    </td>
                    <td>
                        <i class="fa-solid ${leaveTypeIcon(leave.leave_type)} me-2"
                           style="color:#6c4cff;"></i>
                        ${escapeHtml(leave.leave_type)}
                    </td>
                    <td>
                        ${formatDate(leave.start_date)}
                        <br>
                        <small class="text-muted">
                            to ${formatDate(leave.end_date)}
                        </small>
                    </td>
                    <td>${days}</td>
                    <td>${formatDate(leave.created_at)}</td>
                    <td>
                        <span class="leave-status ${escapeHtml(status)}">
                            <i class="fa-solid ${statusIcon(status)}"></i>
                            ${statusLabel(status)}
                        </span>
                    </td>
                    <td>
                        <button type="button"
                                class="table-action-btn view"
                                data-action="view"
                                data-id="${leave.id}"
                                title="View Details">
                            <i class="fa-solid fa-eye"></i>
                        </button>
                        ${status === "pending" ? `
                            <button type="button"
                                    class="table-action-btn cancel"
                                    data-action="cancel"
                                    data-id="${leave.id}"
                                    title="Cancel Request">
                                <i class="fa-solid fa-xmark"></i>
                            </button>
                        ` : ""}
                    </td>
                </tr>
            `;
        }).join("");
    }

    function openDetails(leaveId) {
        const leave = state.leaves.find(
            item => Number(item.id) === Number(leaveId)
        );

        if (!leave) return;

        const days = calculateDays(
            leave.start_date,
            leave.end_date
        );

        setText("detailRequestId", `#${requestNumber(leave)}`);
        setText("detailLeaveType", leave.leave_type);
        setText("detailStartDate", formatDate(leave.start_date));
        setText("detailEndDate", formatDate(leave.end_date));
        setText("detailTotalDays", `${days} ${days === 1 ? "Day" : "Days"}`);
        setText("detailLeaveStatus", statusLabel(leave.status));
        setText("detailReason", leave.reason || "--");
        setText("detailContactNumber", leave.contact_number || "--");
        setText("detailAlternateEmail", leave.alternate_email || "--");
        setText(
            "detailResponsibilityNote",
            leave.responsibility_note || "--"
        );
        setText(
            "detailRemark",
            leave.hod_remarks || (
                leave.status === "pending"
                    ? "Request is currently under review."
                    : "No remarks provided."
            )
        );

        const documentLink = document.getElementById("detailDocumentLink");

        if (documentLink) {
            if (leave.supporting_document_url) {
                documentLink.href = (
                    `http://127.0.0.1:5000${leave.supporting_document_url}`
                );
                documentLink.style.display = "inline-flex";
            } else {
                documentLink.removeAttribute("href");
                documentLink.style.display = "none";
            }
        }

        const modalElement = document.getElementById("leaveDetailsModal");
        if (modalElement && window.bootstrap) {
            bootstrap.Modal.getOrCreateInstance(modalElement).show();
        }
    }

    function openCancelModal(leaveId) {
        const leave = state.leaves.find(
            item => Number(item.id) === Number(leaveId)
        );

        if (!leave || leave.status !== "pending") return;

        const hiddenInput = document.getElementById("cancelLeaveId");
        if (hiddenInput) hiddenInput.value = leave.id;

        setText("cancelRequestId", `#${requestNumber(leave)}`);

        const modalElement = document.getElementById("cancelLeaveModal");
        if (modalElement && window.bootstrap) {
            bootstrap.Modal.getOrCreateInstance(modalElement).show();
        }
    }

    async function cancelLeave() {
        const hiddenInput = document.getElementById("cancelLeaveId");
        const button = document.getElementById("confirmCancelLeaveBtn");
        const leaveId = hiddenInput?.value;

        if (!leaveId) return;

        if (button) button.disabled = true;

        try {
            const result = await apiRequest(
                `/leave-requests/${leaveId}/cancel`,
                { method: "PATCH", body: JSON.stringify({}) }
            );

            const modalElement = document.getElementById("cancelLeaveModal");
            if (modalElement && window.bootstrap) {
                bootstrap.Modal.getOrCreateInstance(modalElement).hide();
            }

            showAlert(result.message || "Leave request cancelled successfully");
            await loadLeaves();
        } catch (error) {
            showAlert(error.message);
        } finally {
            if (button) button.disabled = false;
        }
    }

    async function submitLeave(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const selectedType = form.querySelector(
            'input[name="leaveType"]:checked'
        );
        const startDate = document.getElementById("leaveStartDate")?.value;
        const endDate = document.getElementById("leaveEndDate")?.value;
        const reason = document.getElementById("leaveReason")?.value.trim();
        const contactNumber = document.getElementById("contactNumber")?.value.trim();
        const alternateEmail = document.getElementById("alternateEmail")?.value.trim();
        const responsibilityNote = document.getElementById("responsibilityNote")?.value.trim();
        const documentInput = document.getElementById("leaveDocument");
        const selectedDocument = documentInput?.files?.[0] || null;
        const selectedDocumentName = selectedDocument?.name || "";
        const declaration = document.getElementById("leaveDeclaration");
        const submitButton = document.getElementById("submitLeaveBtn");

        if (!selectedType) {
            showAlert("Please select a leave type.");
            return;
        }

        if (!startDate || !endDate || calculateDays(startDate, endDate) <= 0) {
            showAlert("Please select valid leave dates.");
            return;
        }

        if (!reason || reason.length < 10) {
            showAlert("Please enter a proper reason for leave.");
            return;
        }

        if (!declaration?.checked) {
            showAlert("Please confirm the declaration.");
            return;
        }

        if (submitButton) submitButton.disabled = true;

        if (selectedDocument) {
            setUploadStatus(
                "uploading",
                '<i class="fa-solid fa-spinner fa-spin me-1"></i> Uploading document...'
            );
        }

        try {
            const formData = new FormData();

            formData.append("leave_type", selectedType.value);
            formData.append("start_date", startDate);
            formData.append("end_date", endDate);
            formData.append("reason", reason);

            if (contactNumber) {
                formData.append("contact_number", contactNumber);
            }

            if (alternateEmail) {
                formData.append("alternate_email", alternateEmail);
            }

            if (responsibilityNote) {
                formData.append("responsibility_note", responsibilityNote);
            }

            if (selectedDocument) {
                formData.append(
                    "supporting_document",
                    selectedDocument
                );
            }

            const result = await apiRequest("/leave-requests", {
                method: "POST",
                body: formData
            });

            setText(
                "generatedRequestId",
                `#${requestNumber(result.data)}`
            );

            const successModal = document.getElementById("leaveSuccessModal");
            let documentConfirmation = document.getElementById(
                "uploadedDocumentConfirmation"
            );

            if (successModal && !documentConfirmation) {
                documentConfirmation = document.createElement("div");
                documentConfirmation.id = "uploadedDocumentConfirmation";
                documentConfirmation.className = "alert alert-success mt-3 mb-0";

                const requestCard = successModal.querySelector(
                    "#generatedRequestId"
                )?.parentElement;
                requestCard?.insertAdjacentElement(
                    "afterend",
                    documentConfirmation
                );
            }

            if (documentConfirmation) {
                if (selectedDocumentName) {
                    documentConfirmation.style.display = "block";
                    documentConfirmation.innerHTML = `
                        <i class="fa-solid fa-file-circle-check me-2"></i>
                        Document uploaded: <strong>${escapeHtml(selectedDocumentName)}</strong>
                    `;
                } else {
                    documentConfirmation.style.display = "none";
                    documentConfirmation.innerHTML = "";
                }
            }

            if (successModal && window.bootstrap) {
                bootstrap.Modal.getOrCreateInstance(successModal).show();
            }

            form.reset();
            resetFormSummary();

            if (selectedDocumentName) {
                setText("uploadFileName", selectedDocumentName);
                setUploadStatus(
                    "success",
                    '<i class="fa-solid fa-circle-check me-1"></i> Document uploaded successfully'
                );
            }

            await loadLeaves();
        } catch (error) {
            if (selectedDocument) {
                setUploadStatus(
                    "error",
                    '<i class="fa-solid fa-circle-xmark me-1"></i> Document upload failed'
                );
            }
            showAlert(error.message);
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    }

    async function loadLeaves() {
        const tbody = document.getElementById("leaveHistoryBody");

        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted">
                        Loading leave requests...
                    </td>
                </tr>
            `;
        }

        try {
            const result = await apiRequest("/leave-requests/me");
            state.leaves = Array.isArray(result.data) ? result.data : [];
            renderSummary(result.summary || {});
            renderHistory();
        } catch (error) {
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-4 text-danger">
                            ${escapeHtml(error.message)}
                        </td>
                    </tr>
                `;
            }
        }
    }

    async function loadTeacherProfile() {
        try {
            const result = await apiRequest("/teachers/me/dashboard");
            const data = result.data || {};
            const teacher = data.teacher || data.profile || data;

            const name = teacher.full_name || teacher.name || "Teacher";
            const designation = teacher.designation || "Faculty Member";
            const photo = teacher.photo_url || teacher.photo;

            const nameElement = document.querySelector(
                ".topbar-user-text strong"
            );
            const designationElement = document.querySelector(
                ".topbar-user-text small"
            );
            const avatar = document.querySelector(".teacher-avatar");

            if (nameElement) nameElement.textContent = name;
            if (designationElement) designationElement.textContent = designation;

            if (avatar && photo) {
                avatar.src = photo.startsWith("http")
                    ? photo
                    : `http://127.0.0.1:5000/${photo.replace(/^\//, "")}`;
            }
        } catch (error) {
            console.warn("Teacher profile could not be loaded:", error.message);
        }
    }

    function setupTheme() {
        const button = document.getElementById("themeToggle");
        if (!button) return;

        const applyTheme = theme => {
            document.body.classList.toggle("dark", theme === "dark");
            const icon = button.querySelector("i");
            if (icon) {
                icon.className = theme === "dark"
                    ? "fa-solid fa-sun"
                    : "fa-solid fa-moon";
            }
            localStorage.setItem("teacherTheme", theme);
        };

        applyTheme(localStorage.getItem("teacherTheme") || "light");

        button.addEventListener("click", () => {
            applyTheme(
                document.body.classList.contains("dark")
                    ? "light"
                    : "dark"
            );
        });
    }

    function setupPage() {
        const form = document.getElementById("leaveRequestForm");
        const startDate = document.getElementById("leaveStartDate");
        const endDate = document.getElementById("leaveEndDate");
        const reason = document.getElementById("leaveReason");
        const documentInput = document.getElementById("leaveDocument");
        const uploadFileName = document.getElementById("uploadFileName");
        const resetButton = document.getElementById("resetLeaveBtn");
        const filter = document.getElementById("leaveStatusFilter");
        const history = document.getElementById("leaveHistoryBody");
        const cancelButton = document.getElementById("confirmCancelLeaveBtn");
        const mobileButton = document.getElementById("mobileMenuBtn");
        const sidebar = document.getElementById("teacherSidebar");

        const today = new Date();
        const minimumDate = [
            today.getFullYear(),
            String(today.getMonth() + 1).padStart(2, "0"),
            String(today.getDate()).padStart(2, "0")
        ].join("-");

        if (startDate) {
            startDate.min = minimumDate;
            startDate.addEventListener("change", () => {
                if (endDate) {
                    endDate.min = startDate.value || minimumDate;
                    if (endDate.value && endDate.value < startDate.value) {
                        endDate.value = startDate.value;
                    }
                }
                updateDateSummary();
            });
        }

        if (endDate) {
            endDate.min = minimumDate;
            endDate.addEventListener("change", updateDateSummary);
        }

        if (reason) {
            reason.addEventListener("input", () => {
                setText("reasonCharacterCount", `${reason.value.length} / 500`);
            });
        }

        if (documentInput) {
            documentInput.addEventListener("change", () => {
                const file = documentInput.files?.[0];

                if (!file) {
                    if (uploadFileName) {
                        uploadFileName.textContent = "Upload Supporting Document";
                    }
                    setUploadStatus("idle", "");
                    return;
                }

                const allowedTypes = [
                    "application/pdf",
                    "image/jpeg",
                    "image/png"
                ];

                if (!allowedTypes.includes(file.type)) {
                    showAlert("Only PDF, JPG, JPEG and PNG files are allowed.");
                    documentInput.value = "";
                    if (uploadFileName) {
                        uploadFileName.textContent = "Upload Supporting Document";
                    }
                    setUploadStatus(
                        "error",
                        '<i class="fa-solid fa-circle-xmark me-1"></i> Invalid file type'
                    );
                    return;
                }

                if (file.size > 5 * 1024 * 1024) {
                    showAlert("Supporting document must be 5 MB or smaller.");
                    documentInput.value = "";
                    if (uploadFileName) {
                        uploadFileName.textContent = "Upload Supporting Document";
                    }
                    setUploadStatus(
                        "error",
                        '<i class="fa-solid fa-circle-xmark me-1"></i> File exceeds 5 MB'
                    );
                    return;
                }

                if (uploadFileName) {
                    uploadFileName.textContent = file.name;
                }

                setUploadStatus(
                    "selected",
                    `<i class="fa-solid fa-file-circle-check me-1"></i> Selected: ${escapeHtml(file.name)} (${(file.size / 1024).toFixed(1)} KB)`
                );
            });
        }

        if (form) form.addEventListener("submit", submitLeave);
        if (resetButton) {
            resetButton.addEventListener("click", () => {
                window.setTimeout(resetFormSummary, 0);
            });
        }
        if (filter) filter.addEventListener("change", renderHistory);
        if (cancelButton) cancelButton.addEventListener("click", cancelLeave);

        if (history) {
            history.addEventListener("click", event => {
                const button = event.target.closest("button[data-action]");
                if (!button) return;

                if (button.dataset.action === "view") {
                    openDetails(button.dataset.id);
                }

                if (button.dataset.action === "cancel") {
                    openCancelModal(button.dataset.id);
                }
            });
        }

        if (mobileButton && sidebar) {
            mobileButton.addEventListener("click", () => {
                sidebar.classList.toggle("show");
            });
        }

        setupTheme();
        loadTeacherProfile();
        loadLeaves();
    }

    document.addEventListener("DOMContentLoaded", setupPage);
})();
