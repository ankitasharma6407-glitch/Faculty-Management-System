"use strict";

let hodStudents = [];
let filteredHodStudents = [];

document.addEventListener("DOMContentLoaded", async function () {
    if (typeof API === "undefined" || typeof API.request !== "function") {
        showStudentMessage("Unable to connect with backend.", true);
        return;
    }

    bindStudentFilters();
    bindStudentActions();
    bindStudentExports();
    await loadHodStudents();
});

async function loadHodStudents() {
    showStudentMessage("Loading students...");

    try {
        const response = await API.request("GET", "/hods/students");

        if (!response || response.success !== true) {
            throw new Error(response?.message || "Unable to load students.");
        }

        hodStudents = Array.isArray(response.data) ? response.data : [];
        populateStudentFilters();
        applyStudentFilters();
    }
    catch (error) {
        console.error("HOD Students Error:", error);
        hodStudents = [];
        filteredHodStudents = [];
        updateStudentStatistics();
        renderStudents();
        alert(error.message || "Unable to load students.");
    }
}

function populateStudentFilters() {
    populateSelect(
        "courseFilter",
        "All Courses",
        hodStudents.map(student => student.course).filter(Boolean)
    );

    populateSelect(
        "semesterFilter",
        "All Semesters",
        hodStudents.map(student => student.semester).filter(Boolean)
    );
}

function populateSelect(elementId, firstLabel, values) {
    const select = document.getElementById(elementId);
    if (!select) return;

    const currentValue = select.value;
    const uniqueValues = [...new Set(values.map(value => String(value).trim()))]
        .filter(Boolean)
        .sort((first, second) => first.localeCompare(second, undefined, {numeric: true}));

    select.innerHTML = `<option value="">${escapeHtml(firstLabel)}</option>`;

    uniqueValues.forEach(function (value) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
    });

    if (uniqueValues.includes(currentValue)) select.value = currentValue;
}

function bindStudentFilters() {
    const studentSearch = document.getElementById("studentSearch");
    const globalSearch = document.getElementById("globalSearch");

    studentSearch?.addEventListener("input", applyStudentFilters);

    globalSearch?.addEventListener("input", function () {
        if (studentSearch) studentSearch.value = globalSearch.value;
        applyStudentFilters();
    });

    ["courseFilter", "semesterFilter", "statusFilter"].forEach(function (id) {
        document.getElementById(id)?.addEventListener("change", applyStudentFilters);
    });
}

function applyStudentFilters() {
    const search = String(document.getElementById("studentSearch")?.value || "")
        .trim().toLowerCase();
    const course = String(document.getElementById("courseFilter")?.value || "")
        .trim().toLowerCase();
    const semester = String(document.getElementById("semesterFilter")?.value || "")
        .trim().toLowerCase();
    const status = String(document.getElementById("statusFilter")?.value || "")
        .trim().toLowerCase();

    filteredHodStudents = hodStudents.filter(function (student) {
        const searchable = [
            student.full_name,
            student.student_code,
            student.roll_number,
            student.email,
            student.phone,
            student.course,
            student.semester,
            student.section
        ].filter(Boolean).join(" ").toLowerCase();

        return (
            (!search || searchable.includes(search)) &&
            (!course || String(student.course || "").toLowerCase() === course) &&
            (!semester || String(student.semester || "").toLowerCase() === semester) &&
            (!status || String(student.status || "").toLowerCase() === status)
        );
    });

    updateStudentStatistics();
    renderStudents();
}

function updateStudentStatistics() {
    const active = filteredHodStudents.filter(
        student => String(student.status || "").toLowerCase() === "active"
    ).length;
    const inactive = filteredHodStudents.filter(
        student => String(student.status || "").toLowerCase() === "inactive"
    ).length;
    const courses = new Set(
        filteredHodStudents.map(student => student.course).filter(Boolean)
    ).size;

    setText("totalStudents", filteredHodStudents.length);
    setText("activeStudents", active);
    setText("inactiveStudents", inactive);
    setText("totalCourses", courses);
    setText("studentCountBadge", `Showing ${filteredHodStudents.length} Students`);
    setText("studentCountSummary", `Showing ${filteredHodStudents.length} students`);
}

function renderStudents() {
    const body = document.getElementById("studentTableBody");
    if (!body) return;

    if (filteredHodStudents.length === 0) {
        showStudentMessage("No students found.");
        return;
    }

    body.innerHTML = filteredHodStudents.map(function (student, index) {
        return `
            <tr>
                <td>${index + 1}</td>
                <td>
                    <div class="student-name-box">
                        ${getStudentPhoto(student)}
                        <div>
                            <div class="student-name">${escapeHtml(student.full_name || "-")}</div>
                            <div class="student-email">${escapeHtml(student.email || "-")}</div>
                        </div>
                    </div>
                </td>
                <td>${escapeHtml(student.student_code || "-")}</td>
                <td>${escapeHtml(student.roll_number || "-")}</td>
                <td>${escapeHtml(student.course || "-")}</td>
                <td>${escapeHtml(student.semester || "-")}</td>
                <td>${escapeHtml(student.section || "-")}</td>
                <td>${getStatusBadge(student.status)}</td>
                <td>
                    <button
                        type="button"
                        class="action-btn view-btn viewStudentBtn"
                        data-student-id="${Number(student.id)}"
                        title="View Student">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function showStudentMessage(message, isError = false) {
    const body = document.getElementById("studentTableBody");
    if (!body) return;

    body.innerHTML = `
        <tr>
            <td colspan="9" class="text-center py-4 ${isError ? "text-danger" : "text-muted"}">
                ${escapeHtml(message)}
            </td>
        </tr>
    `;
}

function getStudentPhoto(student) {
    if (!student.photo_url) {
        return `
            <div class="student-photo d-flex align-items-center justify-content-center bg-light text-primary">
                <i class="fa-solid fa-user-graduate"></i>
            </div>
        `;
    }

    const url = getBackendAssetUrl(student.photo_url);
    return `<img src="${escapeHtml(url)}" class="student-photo" alt="Student photo">`;
}

function getBackendAssetUrl(path) {
    const value = String(path || "");
    if (/^https?:\/\//i.test(value)) return value;

    const backendRoot = String(API.baseUrl || "http://127.0.0.1:5000/api")
        .replace(/\/api\/?$/, "");
    return backendRoot + (value.startsWith("/") ? value : `/${value}`);
}

function getStatusBadge(status) {
    const value = String(status || "unknown").trim();
    const lower = value.toLowerCase();
    const badgeClass = lower === "active"
        ? "bg-success"
        : lower === "inactive"
            ? "bg-secondary"
            : "bg-warning text-dark";

    return `<span class="badge ${badgeClass}">${escapeHtml(value)}</span>`;
}

function bindStudentActions() {
    document.getElementById("studentTable")?.addEventListener("click", function (event) {
        const button = event.target.closest(".viewStudentBtn");
        if (!button) return;

        const studentId = Number(button.dataset.studentId);
        if (studentId) {
            window.location.href = `student-details.html?id=${studentId}`;
        }
    });
}

function bindStudentExports() {
    document.getElementById("exportBtn")?.addEventListener("click", exportStudentsCsv);
    document.getElementById("printBtn")?.addEventListener("click", function () {
        window.print();
    });
}

function exportStudentsCsv() {
    if (filteredHodStudents.length === 0) {
        alert("No student data available to export.");
        return;
    }

    const rows = [
        ["Student ID", "Roll Number", "Name", "Email", "Phone", "Course", "Semester", "Section", "Status"],
        ...filteredHodStudents.map(student => [
            student.student_code || "",
            student.roll_number || "",
            student.full_name || "",
            student.email || "",
            student.phone || "",
            student.course || "",
            student.semester || "",
            student.section || "",
            student.status || ""
        ])
    ];

    const csv = rows.map(row => row.map(escapeCsv).join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF" + csv], {type: "text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "hod-department-students.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

function escapeCsv(value) {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
}

function setText(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = String(value);
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}