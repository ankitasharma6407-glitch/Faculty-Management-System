"use strict";

/* ============================================================
   HOD ATTENDANCE REPORT
   GET /api/faculty-attendance/hod
============================================================ */

let hodAttendanceRecords = [];
let attendanceDepartment = "";
let attendanceSearchTimer = null;

document.addEventListener("DOMContentLoaded", async function () {
    if (typeof API === "undefined" || typeof API.request !== "function") {
        showAttendanceMessage("Unable to connect with backend.", true);
        return;
    }

    bindAttendanceFilters();
    bindAttendanceTableActions();
    bindAttendanceExports();
    await loadHodAttendanceReport();
});

async function loadHodAttendanceReport() {
    showAttendanceMessage("Loading attendance records...");
    setAttendanceButtonsDisabled(true);

    try {
        const params = getAttendanceFilterParams();

        if (params.from_date && params.to_date && params.from_date > params.to_date) {
            throw new Error("From Date cannot be after To Date.");
        }

        const response = await API.request(
            "GET",
            "/faculty-attendance/hod",
            null,
            params
        );

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to load attendance report.");
        }

        hodAttendanceRecords = Array.isArray(response.data) ? response.data : [];
        attendanceDepartment = response.department || "Department";

        setText(
            "departmentLabel",
            `Showing teacher attendance for ${attendanceDepartment}.`
        );

        updateAttendanceStatistics(response.summary || {});
        renderAttendanceRecords();
    }
    catch (error) {
        console.error("HOD Attendance Report Error:", error);
        hodAttendanceRecords = [];
        updateAttendanceStatistics({});
        showAttendanceMessage(error.message || "Unable to load attendance report.", true);
        setText("recordCountLabel", "0 records");
    }
    finally {
        setAttendanceButtonsDisabled(false);
    }
}

function getAttendanceFilterParams() {
    const params = {};
    const search = String(document.getElementById("attendanceSearch")?.value || "").trim();
    const fromDate = String(document.getElementById("fromDate")?.value || "").trim();
    const toDate = String(document.getElementById("toDate")?.value || "").trim();
    const status = String(document.getElementById("statusFilter")?.value || "").trim();

    if (search) params.search = search;
    if (fromDate) params.from_date = fromDate;
    if (toDate) params.to_date = toDate;
    if (status) params.status = status;

    return params;
}

function bindAttendanceFilters() {
    document.getElementById("applyFilterBtn")?.addEventListener(
        "click",
        loadHodAttendanceReport
    );

    document.getElementById("resetFilterBtn")?.addEventListener("click", async function () {
        ["attendanceSearch", "topSearch", "fromDate", "toDate", "statusFilter"]
            .forEach(function (id) {
                const element = document.getElementById(id);
                if (element) element.value = "";
            });

        await loadHodAttendanceReport();
    });

    const attendanceSearch = document.getElementById("attendanceSearch");
    const topSearch = document.getElementById("topSearch");

    attendanceSearch?.addEventListener("input", function () {
        if (topSearch) topSearch.value = attendanceSearch.value;
        scheduleAttendanceSearch();
    });

    topSearch?.addEventListener("input", function () {
        if (attendanceSearch) attendanceSearch.value = topSearch.value;
        scheduleAttendanceSearch();
    });

    document.getElementById("statusFilter")?.addEventListener(
        "change",
        loadHodAttendanceReport
    );
}

function scheduleAttendanceSearch() {
    clearTimeout(attendanceSearchTimer);
    attendanceSearchTimer = setTimeout(loadHodAttendanceReport, 350);
}

function updateAttendanceStatistics(summary) {
    const total = Number(summary.total || 0);
    const present = Number(summary.present || 0);
    const absent = Number(summary.absent || 0);
    const leave = Number(summary.leave || 0);
    const percentage = total > 0 ? ((present / total) * 100).toFixed(1) : "0.0";

    setText("totalRecords", total);
    setText("presentRecords", present);
    setText("absentRecords", absent);
    setText("leaveRecords", leave);
    setText("attendancePercentage", `${percentage}%`);
    setText("recordCountLabel", `${total} record${total === 1 ? "" : "s"}`);
}

function renderAttendanceRecords() {
    const body = document.getElementById("attendanceTableBody");
    if (!body) return;

    if (hodAttendanceRecords.length === 0) {
        showAttendanceMessage("No attendance records found.");
        return;
    }

    body.innerHTML = hodAttendanceRecords.map(function (record, index) {
        const status = String(record.status || "").trim().toLowerCase();

        return `
            <tr>
                <td>${index + 1}</td>
                <td>${escapeHtml(record.faculty_code || "-")}</td>
                <td>
                    <div class="faculty-box">
                        <div class="faculty-avatar"><i class="fa-solid fa-chalkboard-user"></i></div>
                        <div>
                            <div class="faculty-name">${escapeHtml(record.faculty_name || "-")}</div>
                            <div class="faculty-code">Teacher</div>
                        </div>
                    </div>
                </td>
                <td>${escapeHtml(record.department || "-")}</td>
                <td>${escapeHtml(formatAttendanceDate(record.date))}</td>
                <td>${getAttendanceStatusBadge(status)}</td>
                <td>${escapeHtml(record.remarks || "-")}</td>
                <td>${escapeHtml(record.marked_by_name || "-")}</td>
                <td>
                    <button type="button"
                            class="btn btn-sm btn-info viewAttendanceBtn"
                            data-attendance-id="${Number(record.id)}"
                            title="View Details">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function showAttendanceMessage(message, isError = false) {
    const body = document.getElementById("attendanceTableBody");
    if (!body) return;

    body.innerHTML = `
        <tr>
            <td colspan="9" class="text-center py-4 ${isError ? "text-danger" : "text-muted"}">
                ${escapeHtml(message)}
            </td>
        </tr>
    `;
}

function getAttendanceStatusBadge(status) {
    const safeStatus = ["present", "absent", "leave"].includes(status)
        ? status
        : "absent";
    const icons = {
        present: "fa-circle-check",
        absent: "fa-circle-xmark",
        leave: "fa-calendar-minus"
    };

    return `
        <span class="attendance-status ${safeStatus}">
            <i class="fa-solid ${icons[safeStatus]}"></i>
            ${escapeHtml(safeStatus)}
        </span>
    `;
}

function bindAttendanceTableActions() {
    document.getElementById("attendanceTable")?.addEventListener("click", function (event) {
        const button = event.target.closest(".viewAttendanceBtn");
        if (!button) return;

        const record = hodAttendanceRecords.find(
            item => Number(item.id) === Number(button.dataset.attendanceId)
        );
        if (!record) return;

        setInputValue("modalFacultyCode", record.faculty_code || "-");
        setInputValue("modalFacultyName", record.faculty_name || "-");
        setInputValue("modalDepartment", record.department || "-");
        setInputValue("modalDate", formatAttendanceDate(record.date));
        setInputValue("modalStatus", formatLabel(record.status || "-"));
        setInputValue("modalMarkedBy", record.marked_by_name || "-");
        setInputValue("modalRemarks", record.remarks || "-");

        const modal = document.getElementById("attendanceDetailsModal");
        if (modal && typeof bootstrap !== "undefined") {
            bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    });
}

function bindAttendanceExports() {
    document.getElementById("exportExcelBtn")?.addEventListener(
        "click",
        exportAttendanceExcel
    );
    document.getElementById("exportPdfBtn")?.addEventListener(
        "click",
        exportAttendancePdf
    );
    document.getElementById("printAttendanceBtn")?.addEventListener("click", function () {
        window.print();
    });
}

function getAttendanceExportRows() {
    return hodAttendanceRecords.map(function (record, index) {
        return {
            "S.No.": index + 1,
            "Faculty ID": record.faculty_code || "",
            "Teacher": record.faculty_name || "",
            "Department": record.department || "",
            "Date": formatAttendanceDate(record.date),
            "Status": formatLabel(record.status || ""),
            "Remarks": record.remarks || "",
            "Marked By": record.marked_by_name || ""
        };
    });
}

function exportAttendanceExcel() {
    if (hodAttendanceRecords.length === 0) {
        alert("No attendance records available to export.");
        return;
    }

    if (typeof XLSX === "undefined") {
        alert("Excel export library is unavailable.");
        return;
    }

    const worksheet = XLSX.utils.json_to_sheet(getAttendanceExportRows());
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Attendance");
    XLSX.writeFile(workbook, "HOD_Attendance_Report.xlsx");
}

function exportAttendancePdf() {
    if (hodAttendanceRecords.length === 0) {
        alert("No attendance records available to export.");
        return;
    }

    if (!window.jspdf?.jsPDF) {
        alert("PDF export library is unavailable.");
        return;
    }

    const {jsPDF} = window.jspdf;
    const documentPdf = new jsPDF({orientation: "landscape"});

    documentPdf.setFontSize(16);
    documentPdf.text("HOD Department Attendance Report", 14, 16);
    documentPdf.setFontSize(10);
    documentPdf.text(`Department: ${attendanceDepartment || "-"}`, 14, 23);

    documentPdf.autoTable({
        startY: 29,
        head: [["#", "Faculty ID", "Teacher", "Department", "Date", "Status", "Remarks", "Marked By"]],
        body: hodAttendanceRecords.map(function (record, index) {
            return [
                index + 1,
                record.faculty_code || "",
                record.faculty_name || "",
                record.department || "",
                formatAttendanceDate(record.date),
                formatLabel(record.status || ""),
                record.remarks || "",
                record.marked_by_name || ""
            ];
        }),
        styles: {fontSize: 8},
        headStyles: {fillColor: [109, 74, 255]}
    });

    documentPdf.save("HOD_Attendance_Report.pdf");
}

function setAttendanceButtonsDisabled(disabled) {
    ["applyFilterBtn", "resetFilterBtn", "exportExcelBtn", "exportPdfBtn"]
        .forEach(function (id) {
            const button = document.getElementById(id);
            if (button) button.disabled = Boolean(disabled);
        });
}

function formatAttendanceDate(value) {
    if (!value) return "-";
    const date = /^\d{4}-\d{2}-\d{2}$/.test(value)
        ? new Date(`${value}T00:00:00`)
        : new Date(value);

    if (Number.isNaN(date.getTime())) return String(value);

    return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}

function formatLabel(value) {
    const text = String(value || "").trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1).toLowerCase() : "-";
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = String(value ?? "");
}

function setInputValue(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.value = String(value ?? "");
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}