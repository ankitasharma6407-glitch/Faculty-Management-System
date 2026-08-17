"use strict";

/* ============================================================
   HOD DEPARTMENT ANALYTICS
   GET /api/hods/analytics
============================================================ */

let hodAnalyticsData = null;
let hodAnalyticsTeachers = [];
let hodAnalyticsCharts = {};

const analyticsColors = {
    purple: "#6d4aff",
    blue: "#2563eb",
    green: "#16a34a",
    red: "#dc2626",
    amber: "#d97706",
    gray: "#94a3b8"
};

document.addEventListener("DOMContentLoaded", async function () {
    if (typeof API === "undefined" || typeof API.request !== "function") {
        showAnalyticsMessage("Unable to connect with backend.", true);
        renderAnalyticsEmptyState();
        return;
    }

    bindAnalyticsActions();
    await loadHodAnalytics();
});

async function loadHodAnalytics() {
    setAnalyticsButtonsDisabled(true);
    showAnalyticsMessage("Loading department analytics...");

    try {
        const response = await API.request("GET", "/hods/analytics");

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to load HOD analytics.");
        }

        hodAnalyticsData = response;
        hodAnalyticsTeachers = Array.isArray(response.performance?.teachers)
            ? response.performance.teachers
            : [];

        renderAnalytics(response);
        hideAnalyticsMessage();
    }
    catch (error) {
        console.error("HOD Analytics Error:", error);
        hodAnalyticsData = null;
        hodAnalyticsTeachers = [];
        renderAnalyticsEmptyState();
        showAnalyticsMessage(error.message || "Unable to load department analytics.", true);
    }
    finally {
        setAnalyticsButtonsDisabled(false);
    }
}

function renderAnalytics(data) {
    const summary = data.summary || {};
    const attendance = data.attendance || {};
    const performance = data.performance || {};
    const leaveRequests = data.leave_requests || {};

    setAnalyticsText("departmentLabel", `Live analytics for ${data.department || "your department"}.`);
    setAnalyticsText("totalTeachers", toSafeNumber(summary.total_teachers));
    setAnalyticsText("totalStudents", toSafeNumber(summary.total_students));
    setAnalyticsText("attendancePercentage", formatPercentage(summary.attendance_percentage));
    setAnalyticsText("averagePerformance", formatPercentage(summary.average_performance));
    setAnalyticsText("pendingLeaves", toSafeNumber(summary.pending_leave_requests));

    const trend = Array.isArray(attendance.trend) ? attendance.trend : [];
    const attendanceTotal = toSafeNumber(attendance.total);
    const performanceTotal = toSafeNumber(performance.total_records);
    const leaveTotal = toSafeNumber(leaveRequests.total);

    setAnalyticsText("attendanceTrendLabel", `${trend.length} date${trend.length === 1 ? "" : "s"}`);
    setAnalyticsText("attendanceRecordLabel", `${attendanceTotal} record${attendanceTotal === 1 ? "" : "s"}`);
    setAnalyticsText("performanceRecordLabel", `${performanceTotal} record${performanceTotal === 1 ? "" : "s"}`);
    setAnalyticsText("leaveRecordLabel", `${leaveTotal} request${leaveTotal === 1 ? "" : "s"}`);
    setAnalyticsText("teacherPerformanceLabel", `${hodAnalyticsTeachers.length} teacher${hodAnalyticsTeachers.length === 1 ? "" : "s"}`);

    renderSmartInsights(data);
    renderAttendanceTrendChart(trend);
    renderAttendanceOverviewChart(attendance);
    renderPerformanceDistributionChart(performance.distribution || {});
    renderLeaveStatusChart(leaveRequests);
    renderTeacherPerformanceChart(hodAnalyticsTeachers);
    renderTeacherPerformanceTable(hodAnalyticsTeachers);
}

function renderAnalyticsEmptyState() {
    setAnalyticsText("departmentLabel", "Department analytics are unavailable.");
    ["totalTeachers", "totalStudents", "pendingLeaves"].forEach(id => setAnalyticsText(id, "0"));
    ["attendancePercentage", "averagePerformance"].forEach(id => setAnalyticsText(id, "0%"));
    setAnalyticsText("attendanceTrendLabel", "0 dates");
    setAnalyticsText("attendanceRecordLabel", "0 records");
    setAnalyticsText("performanceRecordLabel", "0 records");
    setAnalyticsText("leaveRecordLabel", "0 requests");
    setAnalyticsText("teacherPerformanceLabel", "0 teachers");

    renderSmartInsights(null);
    renderAttendanceTrendChart([]);
    renderAttendanceOverviewChart({});
    renderPerformanceDistributionChart({});
    renderLeaveStatusChart({});
    renderTeacherPerformanceChart([]);
    renderTeacherPerformanceTable([]);
}

function renderSmartInsights(data) {
    const grid = document.getElementById("smartInsightsGrid");
    if (!grid) return;

    if (!data) {
        grid.innerHTML = createInsightCard(
            "Data Unavailable",
            "Smart insights could not be generated because analytics data is unavailable.",
            "info",
            "fa-circle-info"
        );
        return;
    }

    const summary = data.summary || {};
    const attendance = data.attendance || {};
    const performance = data.performance || {};
    const leaveRequests = data.leave_requests || {};
    const attendancePercentage = toSafeNumber(summary.attendance_percentage);
    const averagePerformance = toSafeNumber(summary.average_performance);
    const attendanceTotal = toSafeNumber(attendance.total);
    const performanceTotal = toSafeNumber(performance.total_records);
    const totalTeachers = toSafeNumber(summary.total_teachers);
    const performanceTeachers = Array.isArray(performance.teachers)
        ? performance.teachers.length
        : 0;
    const pendingLeaves = toSafeNumber(leaveRequests.pending);

    const insights = [];

    if (attendanceTotal === 0) {
        insights.push({
            title: "Attendance Data Needed",
            message: "No teacher attendance records are available yet. Mark attendance to generate an attendance trend.",
            type: "info",
            icon: "fa-calendar-plus"
        });
    }
    else if (attendancePercentage >= 90) {
        insights.push({
            title: "Strong Attendance",
            message: `Teacher attendance is ${formatPercentage(attendancePercentage)}, which indicates strong department consistency.`,
            type: "positive",
            icon: "fa-user-check"
        });
    }
    else if (attendancePercentage >= 75) {
        insights.push({
            title: "Stable Attendance",
            message: `Teacher attendance is ${formatPercentage(attendancePercentage)}. Continue monitoring absent and leave records.`,
            type: "warning",
            icon: "fa-chart-line"
        });
    }
    else {
        insights.push({
            title: "Attendance Needs Attention",
            message: `Teacher attendance is ${formatPercentage(attendancePercentage)}. Review recent absence and leave patterns.`,
            type: "critical",
            icon: "fa-triangle-exclamation"
        });
    }

    if (performanceTotal === 0) {
        insights.push({
            title: "Performance Data Needed",
            message: "No teacher performance records are available yet, so an average cannot be evaluated.",
            type: "info",
            icon: "fa-chart-column"
        });
    }
    else if (averagePerformance >= 85) {
        insights.push({
            title: "Excellent Performance",
            message: `Department performance is ${formatPercentage(averagePerformance)} across ${performanceTotal} evaluated record${performanceTotal === 1 ? "" : "s"}.`,
            type: "positive",
            icon: "fa-trophy"
        });
    }
    else if (averagePerformance >= 70) {
        insights.push({
            title: "Good Performance",
            message: `Department performance is ${formatPercentage(averagePerformance)}. Teacher-wise comparison can identify further improvement areas.`,
            type: "warning",
            icon: "fa-ranking-star"
        });
    }
    else {
        insights.push({
            title: "Performance Review Suggested",
            message: `Department performance is ${formatPercentage(averagePerformance)}. Review teachers in the Average and Poor bands.`,
            type: "critical",
            icon: "fa-arrow-trend-down"
        });
    }

    if (pendingLeaves === 0) {
        insights.push({
            title: "Leave Queue Clear",
            message: "There are no pending faculty leave requests requiring HOD action.",
            type: "positive",
            icon: "fa-circle-check"
        });
    }
    else {
        insights.push({
            title: "Leave Review Pending",
            message: `${pendingLeaves} leave request${pendingLeaves === 1 ? " is" : "s are"} waiting for HOD review.`,
            type: "warning",
            icon: "fa-clock"
        });
    }

    if (totalTeachers === 0) {
        insights.push({
            title: "No Department Teachers",
            message: "No teachers are currently assigned to this HOD department.",
            type: "info",
            icon: "fa-users-slash"
        });
    }
    else if (performanceTeachers === totalTeachers) {
        insights.push({
            title: "Complete Performance Coverage",
            message: `Performance records are available for all ${totalTeachers} department teacher${totalTeachers === 1 ? "" : "s"}.`,
            type: "positive",
            icon: "fa-list-check"
        });
    }
    else {
        insights.push({
            title: "Partial Performance Coverage",
            message: `${performanceTeachers} of ${totalTeachers} department teachers currently have performance records.`,
            type: "info",
            icon: "fa-chart-simple"
        });
    }

    grid.innerHTML = insights.map(function (insight) {
        return createInsightCard(insight.title, insight.message, insight.type, insight.icon);
    }).join("");
}

function createInsightCard(title, message, type, icon) {
    return `
        <div class="smart-insight">
            <div class="smart-insight-icon ${escapeAnalyticsHtml(type)}">
                <i class="fa-solid ${escapeAnalyticsHtml(icon)}"></i>
            </div>
            <div>
                <h6>${escapeAnalyticsHtml(title)}</h6>
                <p>${escapeAnalyticsHtml(message)}</p>
            </div>
        </div>
    `;
}

function renderAttendanceTrendChart(trend) {
    createAnalyticsChart("attendanceTrend", "attendanceTrendChart", {
        type: "line",
        data: {
            labels: trend.map(item => formatAnalyticsDate(item.date)),
            datasets: [
                createLineDataset("Present", trend.map(item => toSafeNumber(item.present)), analyticsColors.green),
                createLineDataset("Absent", trend.map(item => toSafeNumber(item.absent)), analyticsColors.red),
                createLineDataset("Leave", trend.map(item => toSafeNumber(item.leave)), analyticsColors.amber)
            ]
        },
        options: getCartesianChartOptions("Attendance Records")
    });
}

function renderAttendanceOverviewChart(attendance) {
    createAnalyticsChart("attendanceOverview", "attendanceOverviewChart", {
        type: "doughnut",
        data: {
            labels: ["Present", "Absent", "Leave"],
            datasets: [{
                data: [
                    toSafeNumber(attendance.present),
                    toSafeNumber(attendance.absent),
                    toSafeNumber(attendance.leave)
                ],
                backgroundColor: [analyticsColors.green, analyticsColors.red, analyticsColors.amber],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: getDoughnutChartOptions()
    });
}

function renderPerformanceDistributionChart(distribution) {
    createAnalyticsChart("performanceDistribution", "performanceDistributionChart", {
        type: "doughnut",
        data: {
            labels: ["Excellent", "Good", "Average", "Poor"],
            datasets: [{
                data: [
                    toSafeNumber(distribution.excellent),
                    toSafeNumber(distribution.good),
                    toSafeNumber(distribution.average),
                    toSafeNumber(distribution.poor)
                ],
                backgroundColor: [
                    analyticsColors.green,
                    analyticsColors.blue,
                    analyticsColors.amber,
                    analyticsColors.red
                ],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: getDoughnutChartOptions()
    });
}

function renderLeaveStatusChart(leaveRequests) {
    createAnalyticsChart("leaveStatus", "leaveStatusChart", {
        type: "doughnut",
        data: {
            labels: ["Pending", "Approved", "Rejected"],
            datasets: [{
                data: [
                    toSafeNumber(leaveRequests.pending),
                    toSafeNumber(leaveRequests.approved),
                    toSafeNumber(leaveRequests.rejected)
                ],
                backgroundColor: [analyticsColors.amber, analyticsColors.green, analyticsColors.red],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: getDoughnutChartOptions()
    });
}

function renderTeacherPerformanceChart(teachers) {
    createAnalyticsChart("teacherPerformance", "teacherPerformanceChart", {
        type: "bar",
        data: {
            labels: teachers.map(teacher => teacher.teacher_name || teacher.teacher_code || "Teacher"),
            datasets: [{
                label: "Average Performance (%)",
                data: teachers.map(teacher => toSafeNumber(teacher.average_percentage)),
                backgroundColor: analyticsColors.purple,
                borderRadius: 7,
                maxBarThickness: 52
            }]
        },
        options: {
            ...getCartesianChartOptions("Percentage"),
            scales: {
                x: {
                    grid: {display: false},
                    ticks: {color: getAnalyticsTextColor(), maxRotation: 35, minRotation: 0}
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {color: getAnalyticsTextColor(), callback: value => `${value}%`},
                    grid: {color: getAnalyticsGridColor()}
                }
            }
        }
    });
}

function createLineDataset(label, data, color) {
    return {
        label,
        data,
        borderColor: color,
        backgroundColor: color,
        tension: 0.35,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: false
    };
}

function createAnalyticsChart(key, canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;

    if (hodAnalyticsCharts[key]) {
        hodAnalyticsCharts[key].destroy();
    }

    hodAnalyticsCharts[key] = new Chart(canvas, config);
}

function getCartesianChartOptions(yTitle) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {mode: "index", intersect: false},
        plugins: {
            legend: {position: "bottom", labels: {color: getAnalyticsTextColor(), usePointStyle: true}},
            tooltip: {enabled: true}
        },
        scales: {
            x: {
                grid: {display: false},
                ticks: {color: getAnalyticsTextColor(), maxRotation: 35, minRotation: 0}
            },
            y: {
                beginAtZero: true,
                title: {display: true, text: yTitle, color: getAnalyticsTextColor()},
                ticks: {color: getAnalyticsTextColor(), precision: 0},
                grid: {color: getAnalyticsGridColor()}
            }
        }
    };
}

function getDoughnutChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "64%",
        plugins: {
            legend: {
                position: "bottom",
                labels: {color: getAnalyticsTextColor(), usePointStyle: true, padding: 18}
            }
        }
    };
}

function renderTeacherPerformanceTable(teachers) {
    const body = document.getElementById("teacherPerformanceTableBody");
    if (!body) return;

    if (teachers.length === 0) {
        body.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No teacher performance records found.</td></tr>';
        return;
    }

    body.innerHTML = teachers.map(function (teacher, index) {
        const band = normalizePerformanceBand(teacher.band);

        return `
            <tr>
                <td>${index + 1}</td>
                <td>${escapeAnalyticsHtml(teacher.teacher_code || "-")}</td>
                <td class="teacher-name">${escapeAnalyticsHtml(teacher.teacher_name || "-")}</td>
                <td>${toSafeNumber(teacher.record_count)}</td>
                <td>${formatPercentage(teacher.average_percentage)}</td>
                <td><span class="performance-band ${band.toLowerCase()}">${escapeAnalyticsHtml(band)}</span></td>
            </tr>
        `;
    }).join("");
}

function bindAnalyticsActions() {
    document.getElementById("refreshAnalyticsBtn")?.addEventListener("click", loadHodAnalytics);
    document.getElementById("exportAnalyticsExcelBtn")?.addEventListener("click", exportAnalyticsExcel);
    document.getElementById("exportAnalyticsPdfBtn")?.addEventListener("click", exportAnalyticsPdf);
    document.getElementById("printAnalyticsBtn")?.addEventListener("click", () => window.print());

    const teacherSearch = document.getElementById("teacherSearch");
    const topSearch = document.getElementById("topSearch");

    teacherSearch?.addEventListener("input", function () {
        if (topSearch) topSearch.value = teacherSearch.value;
        filterAnalyticsTeachers(teacherSearch.value);
    });

    topSearch?.addEventListener("input", function () {
        if (teacherSearch) teacherSearch.value = topSearch.value;
        filterAnalyticsTeachers(topSearch.value);
    });
}

function filterAnalyticsTeachers(searchValue) {
    const query = String(searchValue || "").trim().toLowerCase();
    const filtered = hodAnalyticsTeachers.filter(function (teacher) {
        return [teacher.teacher_name, teacher.teacher_code]
            .some(value => String(value || "").toLowerCase().includes(query));
    });

    renderTeacherPerformanceTable(filtered);
}

function exportAnalyticsExcel() {
    if (!hodAnalyticsData) {
        alert("Analytics data is not available to export.");
        return;
    }

    if (typeof XLSX === "undefined") {
        alert("Excel export library is unavailable.");
        return;
    }

    const workbook = XLSX.utils.book_new();
    const summary = hodAnalyticsData.summary || {};
    const attendance = hodAnalyticsData.attendance || {};
    const performance = hodAnalyticsData.performance || {};
    const leaveRequests = hodAnalyticsData.leave_requests || {};

    const summaryRows = [
        {Metric: "Department", Value: hodAnalyticsData.department || ""},
        {Metric: "Total Teachers", Value: toSafeNumber(summary.total_teachers)},
        {Metric: "Total Students", Value: toSafeNumber(summary.total_students)},
        {Metric: "Teacher Attendance (%)", Value: toSafeNumber(summary.attendance_percentage)},
        {Metric: "Average Performance (%)", Value: toSafeNumber(summary.average_performance)},
        {Metric: "Pending Leave Requests", Value: toSafeNumber(summary.pending_leave_requests)}
    ];

    const attendanceRows = (Array.isArray(attendance.trend) ? attendance.trend : []).map(item => ({
        Date: item.date || "",
        Present: toSafeNumber(item.present),
        Absent: toSafeNumber(item.absent),
        Leave: toSafeNumber(item.leave),
        Total: toSafeNumber(item.total)
    }));

    const teacherRows = hodAnalyticsTeachers.map(teacher => ({
        "Faculty ID": teacher.teacher_code || "",
        Teacher: teacher.teacher_name || "",
        "Performance Records": toSafeNumber(teacher.record_count),
        "Average (%)": toSafeNumber(teacher.average_percentage),
        Band: normalizePerformanceBand(teacher.band)
    }));

    const leaveRows = [
        {Status: "Pending", Count: toSafeNumber(leaveRequests.pending)},
        {Status: "Approved", Count: toSafeNumber(leaveRequests.approved)},
        {Status: "Rejected", Count: toSafeNumber(leaveRequests.rejected)},
        {Status: "Total", Count: toSafeNumber(leaveRequests.total)}
    ];

    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(summaryRows), "Summary");
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(attendanceRows), "Attendance Trend");
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(teacherRows), "Teacher Performance");
    XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(leaveRows), "Leave Requests");
    XLSX.writeFile(workbook, "HOD_Department_Analytics.xlsx");
}

function exportAnalyticsPdf() {
    if (!hodAnalyticsData) {
        alert("Analytics data is not available to export.");
        return;
    }

    if (!window.jspdf?.jsPDF) {
        alert("PDF export library is unavailable.");
        return;
    }

    const {jsPDF} = window.jspdf;
    const pdf = new jsPDF({orientation: "landscape"});
    const summary = hodAnalyticsData.summary || {};

    pdf.setFontSize(17);
    pdf.text("HOD Department Analytics", 14, 16);
    pdf.setFontSize(10);
    pdf.text(`Department: ${hodAnalyticsData.department || "-"}`, 14, 23);

    pdf.autoTable({
        startY: 29,
        head: [["Teachers", "Students", "Attendance", "Average Performance", "Pending Leaves"]],
        body: [[
            toSafeNumber(summary.total_teachers),
            toSafeNumber(summary.total_students),
            formatPercentage(summary.attendance_percentage),
            formatPercentage(summary.average_performance),
            toSafeNumber(summary.pending_leave_requests)
        ]],
        headStyles: {fillColor: [109, 74, 255]}
    });

    pdf.autoTable({
        startY: pdf.lastAutoTable.finalY + 10,
        head: [["#", "Faculty ID", "Teacher", "Records", "Average", "Band"]],
        body: hodAnalyticsTeachers.length
            ? hodAnalyticsTeachers.map((teacher, index) => [
                index + 1,
                teacher.teacher_code || "-",
                teacher.teacher_name || "-",
                toSafeNumber(teacher.record_count),
                formatPercentage(teacher.average_percentage),
                normalizePerformanceBand(teacher.band)
            ])
            : [["-", "-", "No teacher performance records", "-", "-", "-"]],
        headStyles: {fillColor: [109, 74, 255]}
    });

    pdf.save("HOD_Department_Analytics.pdf");
}

function setAnalyticsButtonsDisabled(disabled) {
    ["refreshAnalyticsBtn", "exportAnalyticsExcelBtn", "exportAnalyticsPdfBtn"]
        .forEach(function (id) {
            const button = document.getElementById(id);
            if (button) button.disabled = Boolean(disabled);
        });
}

function showAnalyticsMessage(message, isError = false) {
    const element = document.getElementById("analyticsMessage");
    if (!element) return;
    element.textContent = message;
    element.className = `alert analytics-message ${isError ? "alert-danger" : "alert-info"}`;
    element.style.display = "block";
}

function hideAnalyticsMessage() {
    const element = document.getElementById("analyticsMessage");
    if (element) element.style.display = "none";
}

function toSafeNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function formatPercentage(value) {
    const number = toSafeNumber(value);
    return `${Number.isInteger(number) ? number : number.toFixed(1)}%`;
}

function formatAnalyticsDate(value) {
    if (!value) return "-";
    const date = /^\d{4}-\d{2}-\d{2}$/.test(value)
        ? new Date(`${value}T00:00:00`)
        : new Date(value);

    if (Number.isNaN(date.getTime())) return String(value);

    return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short"
    });
}

function normalizePerformanceBand(value) {
    const band = String(value || "Poor").trim().toLowerCase();
    const allowed = ["excellent", "good", "average", "poor"];
    const safeBand = allowed.includes(band) ? band : "poor";
    return safeBand.charAt(0).toUpperCase() + safeBand.slice(1);
}

function getAnalyticsTextColor() {
    return document.body.classList.contains("dark") ? "#e5e7eb" : "#475569";
}

function getAnalyticsGridColor() {
    return document.body.classList.contains("dark")
        ? "rgba(148, 163, 184, .18)"
        : "rgba(148, 163, 184, .25)";
}

function setAnalyticsText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = String(value ?? "");
}

function escapeAnalyticsHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}