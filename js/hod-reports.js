"use strict";

/* HOD REPORTS - ORIGINAL UI + LIVE BACKEND */

(function () {
    let reportSummary = null;
    let generatedReports = [];
    let nextReportId = 1;
    const REPORT_HISTORY_KEY = "fmps_hod_report_history_v2";

    document.addEventListener("DOMContentLoaded", async function () {
        prepareOriginalReportsUi();
        bindReportEvents();

        if (typeof API === "undefined" || typeof API.request !== "function") {
            showEmptyTable("Backend connection nahi mila. api.js check karein.", true);
            return;
        }

        await Promise.all([loadReportSummary(), loadNotificationPreview()]);
    });

    function prepareOriginalReportsUi() {
        ensurePermanentActionButtons();
        generatedReports = loadReportHistory();
        nextReportId = generatedReports.reduce((maximum, report) => Math.max(maximum, Number(report.id) || 0), 0) + 1;
        renderGeneratedReports();

        const cards = document.querySelectorAll(".report-stat-card h3");
        setNodeText(cards[0], "0");
        setNodeText(cards[1], "0%");
        setNodeText(cards[2], "0%");
        setNodeText(cards[3], "0");

        const badge = document.getElementById("notificationCount");
        if (badge) {
            badge.textContent = "0";
            badge.style.display = "none";
        }

        const menu = document.querySelector(".notification-menu");
        if (menu) {
            menu.innerHTML = `
                <li class="dropdown-header">Notifications</li>
                <li><div class="dropdown-item text-muted text-center">Loading...</div></li>
            `;
        }
    }

    function ensurePermanentActionButtons() {
        if (
            document.getElementById("viewLatestReportBtn") &&
            document.getElementById("downloadLatestReportBtn")
        ) {
            return;
        }

        const header = document.querySelector(".report-table-header");
        const refreshButton = document.getElementById("refreshReportsBtn");
        if (!header) return;

        const controls = document.createElement("div");
        controls.className = "report-action-bar";
        controls.innerHTML = `
            <span class="report-action-label"><i class="fa-solid fa-bolt me-1"></i>Report Actions</span>
            <button class="btn btn-sm btn-primary" style="display:inline-flex !important; visibility:visible !important; opacity:1 !important; align-items:center;" type="button" id="viewLatestReportBtn">
                <i class="fa-solid fa-eye me-1"></i>View Report
            </button>
            <button class="btn btn-sm btn-success" style="display:inline-flex !important; visibility:visible !important; opacity:1 !important; align-items:center;" type="button" id="downloadLatestReportBtn">
                <i class="fa-solid fa-download me-1"></i>Download CSV
            </button>
        `;

        if (refreshButton) {
            refreshButton.remove();
            controls.appendChild(refreshButton);
        }

        header.appendChild(controls);
    }

    function bindReportEvents() {
        document.getElementById("generateReportBtn")?.addEventListener("click", function () {
            generateSelectedReport(false);
        });

        document.getElementById("applyFilterBtn")?.addEventListener("click", function () {
            if (validateDates()) renderGeneratedReports();
        });

        document.getElementById("resetFilterBtn")?.addEventListener("click", function () {
            setInputValue("reportType", "all");
            setInputValue("fromDate", "");
            setInputValue("toDate", "");
            setInputValue("searchBox", "");
            const year = document.getElementById("academicYear");
            if (year) year.selectedIndex = 0;
            renderGeneratedReports();
        });

        document.getElementById("searchBox")?.addEventListener("input", renderGeneratedReports);
        document.getElementById("reportType")?.addEventListener("change", renderGeneratedReports);

        document.getElementById("refreshReportsBtn")?.addEventListener("click", async function () {
            const icon = this.querySelector("i");
            icon?.classList.add("fa-spin");
            await loadReportSummary();
            renderGeneratedReports();
            icon?.classList.remove("fa-spin");
        });

        document.getElementById("viewLatestReportBtn")?.addEventListener("click", function () {
            const report = generatedReports[0];
            if (!report) {
                window.alert("Pehle report generate karein.");
                return;
            }
            openReportModal(report);
        });

        document.getElementById("downloadLatestReportBtn")?.addEventListener("click", function () {
            const report = generatedReports[0];
            if (!report) {
                window.alert("Pehle report generate karein.");
                return;
            }
            downloadReportCsv(report);
        });

        document.querySelectorAll(".quickViewBtn").forEach(function (button) {
            const cleanButton = button.cloneNode(true);
            cleanButton.type = "button";
            button.replaceWith(cleanButton);
            cleanButton.addEventListener("click", async function (event) {
                event.preventDefault();
                event.stopImmediatePropagation();
                await previewQuickReport(reportTypeFromName(cleanButton.dataset.report || ""));
            });
        });

        document.getElementById("reportsTableBody")?.addEventListener("click", function (event) {
            const viewButton = event.target.closest(".generatedViewBtn");
            const downloadButton = event.target.closest(".generatedDownloadBtn");

            if (viewButton) {
                const report = findReport(viewButton.dataset.reportId);
                if (report) openReportModal(report);
            }

            if (downloadButton) {
                const report = findReport(downloadButton.dataset.reportId);
                if (report) downloadReportCsv(report);
            }
        });
    }

    async function loadReportSummary() {
        try {
            const response = await API.request("GET", "/hods/reports/summary");
            if (!response || response.success !== true) {
                throw new Error(response?.message || "Reports summary load nahi hui.");
            }

            reportSummary = response;
            updateSummaryCards();
            updateDepartmentOverview();
            updateModalSummary();
        }
        catch (error) {
            console.error("Report Summary Error:", error);
            showEmptyTable(error.message || "Reports load nahi ho paayi.", true);
        }
    }

    function updateSummaryCards() {
        const cards = document.querySelectorAll(".report-stat-card h3");
        const attendance = reportSummary?.attendance || {};
        const performance = reportSummary?.performance || {};

        setNodeText(cards[0], String(generatedReports.length));
        setNodeText(cards[1], `${formatNumber(attendance.attendance_percentage)}%`);
        setNodeText(cards[2], `${formatNumber(performance.average_percentage)}%`);
        setNodeText(cards[3], String(generatedReports.filter(item => item.status === "pending").length));
    }

    function updateDepartmentOverview() {
        const items = document.querySelectorAll(".progress-report");
        const attendance = clampPercentage(reportSummary?.attendance?.attendance_percentage);
        const performance = clampPercentage(reportSummary?.performance?.average_percentage);

        setProgressItem(items[0], attendance, `${formatNumber(attendance)}%`);
        setProgressItem(items[1], 0, "N/A");
        setProgressItem(items[2], performance, `${formatNumber(performance)}%`);
        setProgressItem(items[3], 0, "N/A");
        setProgressItem(items[4], 0, "N/A");
    }

    function setProgressItem(item, width, label) {
        if (!item) return;
        setNodeText(item.querySelector(".progress-report-header span:last-child"), label);
        const bar = item.querySelector(".progress-bar");
        if (bar) bar.style.width = `${width}%`;
    }

    function updateModalSummary() {
        const modal = document.getElementById("reportViewModal");
        if (!modal) return;

        const department = reportSummary?.department || "Department";
        const attendance = reportSummary?.attendance || {};
        const faculty = reportSummary?.faculty || {};
        const performance = reportSummary?.performance || {};
        const headerText = modal.querySelector(".modal-body .text-center p.text-muted");
        const infoValues = modal.querySelectorAll(".row.g-3 .col-md-6 p");
        const metricValues = modal.querySelectorAll(".row.g-3 .col-md-4 h4");

        setNodeText(headerText, `Department of ${department}`);
        setNodeText(infoValues[1], department);
        setNodeText(metricValues[0], `${formatNumber(attendance.attendance_percentage)}%`);
        setNodeText(metricValues[1], String(faculty.total_students || 0));
        setNodeText(metricValues[2], `${formatNumber(performance.average_percentage)}%`);
        setNodeText(metricValues[1]?.parentElement?.querySelector("small"), "Total Students");
    }

    async function generateSelectedReport(openAfterGenerate) {
        const type = document.getElementById("reportType")?.value || "all";
        if (type === "all") {
            window.alert("Please select a Report Type before generating a report.");
            return;
        }
        if (!validateDates()) return;

        const button = document.getElementById("generateReportBtn");
        setButtonLoading(button, true);

        try {
            const reportData = await loadReportData(type);
            const typeText = selectedReportTypeText();
            const report = {
                id: nextReportId++,
                name: typeText,
                type,
                typeLabel: typeText.replace(" Report", ""),
                generatedDate: new Date(),
                period: selectedPeriod(type),
                status: "ready",
                data: reportData
            };

            generatedReports.unshift(report);
            saveReportHistory();
            updateSummaryCards();
            renderGeneratedReports();
            if (openAfterGenerate) openReportModal(report);
            window.alert(`${typeText} generated successfully from backend data.`);
        }
        catch (error) {
            console.error("Generate Report Error:", error);
            window.alert(error.message || "Report generate nahi ho paayi.");
        }
        finally {
            setButtonLoading(button, false);
        }
    }

    async function previewQuickReport(type) {
        if (!["attendance", "performance", "leave"].includes(type)) {
            window.alert("This report is not available because the current backend has no separate data endpoint for it.");
            return;
        }
        try {
            const data = await loadReportData(type);
            openReportModal({
                id: "preview",
                name: reportLabel(type),
                type,
                typeLabel: reportLabel(type).replace(" Report", ""),
                generatedDate: new Date().toISOString(),
                period: selectedPeriod(type),
                data
            });
        } catch (error) {
            window.alert(error.message || "Report preview load nahi ho paayi.");
        }
    }

    async function loadReportData(type) {
        const fromDate = document.getElementById("fromDate")?.value || "";
        const toDate = document.getElementById("toDate")?.value || "";

        if (type === "attendance") {
            const params = {};
            if (fromDate) params.from_date = fromDate;
            if (toDate) params.to_date = toDate;
            return requireData(await API.request("GET", "/faculty-attendance/hod", null, params));
        }
        if (type === "performance") {
            return requireData(await API.request("GET", "/hods/performance"));
        }
        if (type === "leave") {
            const response = requireData(await API.request("GET", "/leave-requests/hod"));
            response.data = filterLeavesByDate(response.data, fromDate, toDate);
            return response;
        }
        if (type === "academic" || type === "workload") throw new Error("This report type is not supported by the current backend.");
        throw new Error("Unsupported report type.");
    }

    function requireData(response) {
        if (!response || response.success !== true) {
            throw new Error(response?.message || "Backend se report data nahi mili.");
        }
        return response;
    }

    function filterLeavesByDate(records, fromDate, toDate) {
        return (Array.isArray(records) ? records : []).filter(function (record) {
            const start = dateInputValue(record.start_date);
            const end = dateInputValue(record.end_date || record.start_date);
            if (fromDate && end && end < fromDate) return false;
            if (toDate && start && start > toDate) return false;
            return true;
        });
    }

    function renderGeneratedReports() {
        const body = document.getElementById("reportsTableBody");
        const empty = document.getElementById("noReportResult");
        if (!body) return;

        updateLatestActionButtons();

        const selectedType = document.getElementById("reportType")?.value || "all";
        const search = normalize(document.getElementById("searchBox")?.value);
        const filtered = generatedReports.filter(function (report) {
            const typeMatch = selectedType === "all" || report.type === selectedType;
            const text = `${report.name} ${report.typeLabel} ${report.period}`.toLowerCase();
            return typeMatch && (!search || text.includes(search));
        });

        if (filtered.length === 0) {
            body.innerHTML = "";
            if (empty) empty.style.display = "block";
            return;
        }

        if (empty) empty.style.display = "none";
        body.innerHTML = filtered.map(function (report, index) {
            return `
                <tr class="report-row" data-type="${escapeHtml(report.type)}">
                    <td>${index + 1}</td>
                    <td><div class="report-name"><div class="report-name-icon"><i class="fa-solid fa-file-lines"></i></div><div><strong>${escapeHtml(report.name)}</strong></div></div></td>
                    <td>${escapeHtml(report.typeLabel)}</td>
                    <td>${formatDate(report.generatedDate)}</td>
                    <td>${escapeHtml(report.period)}</td>
                    <td><span class="report-status status-ready">Ready</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary generatedViewBtn" data-report-id="${report.id}" title="View"><i class="fa-solid fa-eye"></i></button>
                        <button class="btn btn-sm btn-outline-success generatedDownloadBtn" data-report-id="${report.id}" title="Download CSV"><i class="fa-solid fa-download"></i></button>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function updateLatestActionButtons() {
        const hasReport = generatedReports.length > 0;
        const viewButton = document.getElementById("viewLatestReportBtn");
        const downloadButton = document.getElementById("downloadLatestReportBtn");
        // Keep these buttons always visible and clickable. Before a report is
        // generated, their click handler clearly tells the HOD what to do.
        if (viewButton) viewButton.disabled = false;
        if (downloadButton) downloadButton.disabled = false;
    }

    function showEmptyTable(message, isError) {
        const body = document.getElementById("reportsTableBody");
        const empty = document.getElementById("noReportResult");
        if (body) body.innerHTML = `<tr><td colspan="7" class="text-center py-4 ${isError ? "text-danger" : "text-muted"}">${escapeHtml(message)}</td></tr>`;
        if (empty) empty.style.display = "none";
    }

    function openReportModal(report) {
        const modal = document.getElementById("reportViewModal");
        if (!modal) return;
        document.getElementById("modalReportTitle").textContent = report.name;
        const modalBody = modal.querySelector(".modal-body");
        if (modalBody) modalBody.innerHTML = buildReportModalContent(report);
        if (modal && window.bootstrap?.Modal) bootstrap.Modal.getOrCreateInstance(modal).show();
    }

    function downloadReportCsv(report) {
        const rows = reportRowsForDownload(report);
        const csv = rows.map(row => row.map(csvCell).join(",")).join("\n");
        const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${report.type}-report-${dateInputValue(new Date())}.csv`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }

    function reportRowsForDownload(report) {
        const records = Array.isArray(report.data?.data) ? report.data.data : [];
        const metadata = [[report.name], ["Period", report.period], ["Generated", formatDate(report.generatedDate)], []];
        if (report.type === "attendance") return metadata.concat([["Faculty Code", "Faculty Name", "Date", "Status", "Department"], ...records.map(item => [item.faculty_code, item.faculty_name, item.date, item.status, item.department])]);
        if (report.type === "performance") return metadata.concat([["Teacher Code", "Teacher Name", "Subject", "Term", "Score", "Max Score", "Percentage", "Grade", "Band"], ...records.map(item => [item.teacher_code, item.teacher_name, item.subject, item.term, item.score, item.max_score, item.percentage, item.grade, item.band])]);
        if (report.type === "leave") return metadata.concat([["Teacher", "Leave Type", "Start Date", "End Date", "Status", "Reason"], ...records.map(item => [item.teacher_name || item.teacher?.full_name, item.leave_type, item.start_date, item.end_date, item.status, item.reason])]);
        return metadata.concat([["Metric", "Value"], ...Object.entries(report.data || {}).filter(([, value]) => typeof value !== "object").map(([key, value]) => [key, value])]);
    }

    function buildReportModalContent(report) {
        const records = Array.isArray(report.data?.data) ? report.data.data : [];
        const summary = report.data?.summary || {};
        const department = report.data?.department || reportSummary?.department || "Department";
        let metrics = [];
        let columns = [];
        let rows = [];
        if (report.type === "attendance") {
            metrics = [["Total Records", summary.total || records.length], ["Present", summary.present || 0], ["Absent", summary.absent || 0], ["Leave", summary.leave || 0]];
            columns = ["Faculty", "Date", "Status"]; rows = records.map(item => [item.faculty_name || "-", item.date || "-", item.status || "-"]);
        } else if (report.type === "performance") {
            metrics = [["Total Records", summary.total || records.length], ["Excellent", summary.excellent || 0], ["Good", summary.good || 0], ["Average/Poor", (summary.average || 0) + (summary.poor || 0)]];
            columns = ["Teacher", "Subject", "Score", "Performance"]; rows = records.map(item => [item.teacher_name || "-", item.subject || "-", `${item.score ?? "-"}/${item.max_score ?? "-"}`, `${item.percentage ?? "-"}% (${item.band || "-"})`]);
        } else {
            metrics = [["Total Requests", summary.total || records.length], ["Pending", summary.pending || 0], ["Approved", summary.approved || 0], ["Rejected", summary.rejected || 0]];
            columns = ["Teacher", "Leave Type", "Dates", "Status"]; rows = records.map(item => [item.teacher_name || item.teacher?.full_name || "-", item.leave_type || "-", `${item.start_date || "-"} to ${item.end_date || "-"}`, item.status || "-"]);
        }
        const metricHtml = metrics.map(([label, value]) => `<div class="col-6 col-md-3"><div class="border rounded-3 p-3 text-center"><h4 class="text-primary fw-bold mb-1">${escapeHtml(value)}</h4><small>${escapeHtml(label)}</small></div></div>`).join("");
        const rowHtml = rows.length ? rows.map(row => `<tr>${row.map(value => `<td>${escapeHtml(value)}</td>`).join("")}</tr>`).join("") : `<tr><td colspan="${columns.length}" class="text-center text-muted py-3">No records found for this report.</td></tr>`;
        return `<div class="text-center mb-4"><div class="report-stat-icon purple mx-auto mb-3"><i class="fa-solid fa-file-lines"></i></div><h4 class="fw-bold">${escapeHtml(report.name)}</h4><p class="text-muted mb-0">Department of ${escapeHtml(department)} · ${escapeHtml(report.period)}</p></div><div class="row g-3 mb-4">${metricHtml}</div><div class="table-responsive"><table class="table table-bordered table-sm align-middle"><thead><tr>${columns.map(column => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead><tbody>${rowHtml}</tbody></table></div>`;
    }

    function reportLabel(type) { return ({ attendance: "Attendance Report", performance: "Faculty Performance Report", leave: "Leave Report" })[type] || "Report"; }

    function loadReportHistory() {
        try {
            const records = JSON.parse(localStorage.getItem(REPORT_HISTORY_KEY) || "[]");
            return Array.isArray(records) ? records.filter(record => ["attendance", "performance", "leave"].includes(record.type)) : [];
        } catch (_) { return []; }
    }

    function saveReportHistory() {
        try { localStorage.setItem(REPORT_HISTORY_KEY, JSON.stringify(generatedReports.slice(0, 25))); }
        catch (_) { console.warn("Report history could not be stored in this browser."); }
    }

    async function loadNotificationPreview() {
        try {
            const response = await API.request("GET", "/notifications");
            if (!response || response.success !== true) return;
            const notifications = Array.isArray(response.data) ? response.data : [];
            const unread = Number(response.summary?.unread ?? notifications.filter(item => !item.is_read).length) || 0;
            const badge = document.getElementById("notificationCount");
            if (badge) {
                badge.textContent = String(unread);
                badge.style.display = unread > 0 ? "flex" : "none";
            }

            const menu = document.querySelector(".notification-menu");
            if (!menu) return;
            const items = notifications.slice(0, 4).map(item => `<li><a class="dropdown-item" href="notification.html">${escapeHtml(item.title || "Notification")}</a></li>`).join("");
            menu.innerHTML = `<li class="dropdown-header">Notifications</li>${items || '<li><div class="dropdown-item text-muted text-center">No notifications</div></li>'}<li><hr class="dropdown-divider"></li><li><a class="dropdown-item text-center" href="notification.html">View All Notifications</a></li>`;
        }
        catch (error) {
            console.warn("Notification preview load nahi hui:", error);
        }
    }

    function validateDates() {
        const from = document.getElementById("fromDate")?.value || "";
        const to = document.getElementById("toDate")?.value || "";
        if (from && to && from > to) {
            window.alert("From Date cannot be after To Date.");
            return false;
        }
        return true;
    }

    function selectedReportTypeText() {
        const select = document.getElementById("reportType");
        return select?.options[select.selectedIndex]?.text?.trim() || "Report";
    }

    function selectedPeriod(type) {
        const from = document.getElementById("fromDate")?.value || "";
        const to = document.getElementById("toDate")?.value || "";
        if (["attendance", "leave"].includes(type) && (from || to)) return `${from || "Beginning"} to ${to || "Today"}`;
        return document.getElementById("academicYear")?.value || "All Records";
    }

    function reportTypeFromName(name) {
        const value = normalize(name);
        if (value.includes("attendance")) return "attendance";
        if (value.includes("performance")) return "performance";
        if (value.includes("academic")) return "academic";
        if (value.includes("leave")) return "leave";
        if (value.includes("workload")) return "workload";
        return "all";
    }

    function findReport(id) {
        return generatedReports.find(report => String(report.id) === String(id));
    }

    function setButtonLoading(button, loading) {
        if (!button) return;
        if (loading) {
            button.dataset.originalHtml = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
        }
        else {
            button.disabled = false;
            if (button.dataset.originalHtml) button.innerHTML = button.dataset.originalHtml;
        }
    }

    function setInputValue(id, value) {
        const input = document.getElementById(id);
        if (input) input.value = value;
    }

    function setNodeText(node, value) {
        if (node) node.textContent = String(value ?? "");
    }

    function formatDate(value) {
        const date = value instanceof Date ? value : new Date(value);
        if (Number.isNaN(date.getTime())) return "-";
        return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
    }

    function dateInputValue(value) {
        if (value instanceof Date) {
            const year = value.getFullYear();
            const month = String(value.getMonth() + 1).padStart(2, "0");
            const day = String(value.getDate()).padStart(2, "0");
            return `${year}-${month}-${day}`;
        }
        const match = String(value || "").match(/^(\d{4}-\d{2}-\d{2})/);
        return match ? match[1] : "";
    }

    function csvCell(value) {
        return `"${String(value ?? "").replaceAll('"', '""')}"`;
    }

    function normalize(value) {
        return String(value || "").trim().toLowerCase();
    }

    function clampPercentage(value) {
        const number = Number(value || 0);
        if (!Number.isFinite(number)) return 0;
        return Math.max(0, Math.min(100, number));
    }

    function formatNumber(value) {
        const number = Number(value || 0);
        if (!Number.isFinite(number)) return "0";
        return Number.isInteger(number) ? String(number) : number.toFixed(1);
    }

    function escapeHtml(value) {
        return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
    }
})();