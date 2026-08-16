"use strict";

/* ============================================================
   HOD TEACHER LIST
   ------------------------------------------------------------
   IMPORTANT:
   This file is ONLY for HOD panel.
   Admin teacher-list.js is not touched.
============================================================ */


/* ============================================================
   GLOBAL DATA
============================================================ */

let hodTeachers = [];
let hodDepartmentName = "";
let hodAverageAttendance = null;


/* ============================================================
   INITIAL LOAD
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        if (
            typeof API === "undefined" ||
            typeof API.request !== "function"
        ) {

            console.error(
                "FMPS API client is not loaded."
            );

            showTeacherTableMessage(
                "Unable to connect with backend."
            );

            return;
        }


        prepareTeacherPage();

        bindTeacherFilters();

        bindTeacherTableActions();

        bindExportButtons();


        await loadHodTeachers();

        await loadAverageAttendance();
    }
);


/* ============================================================
   PAGE PREPARATION
============================================================ */

function prepareTeacherPage() {

    showTeacherTableMessage(
        "Loading teachers..."
    );


    /*
     * Remove hardcoded statistics immediately.
     */
    const counters =
        getTeacherStatisticElements();


    if (counters.total) {
        counters.total.textContent = "0";
    }


    if (counters.active) {
        counters.active.textContent = "0";
    }


    /*
     * Face registration backend is not final yet.
     * Do not show fake number.
     */
    if (counters.face) {
        counters.face.textContent = "--";
    }


    /*
     * Attendance will be loaded from real analytics API.
     */
    if (counters.attendance) {
        counters.attendance.textContent = "--";
    }
}


/* ============================================================
   LOAD HOD DEPARTMENT TEACHERS
============================================================ */

async function loadHodTeachers() {

    try {

        const response =
            await API.request(
                "GET",
                "/hods/teachers"
            );


        console.log(
            "HOD Teachers:",
            response
        );


        if (
            !response ||
            response.success !== true
        ) {

            throw new Error(
                response?.message ||
                "Unable to load teachers."
            );
        }


        hodTeachers =
            Array.isArray(
                response.data
            )
                ? response.data
                : [];


        hodDepartmentName =
            response.department || "";


        updateDepartmentFilter();

        updateTeacherStatistics();

        applyTeacherFilters();
    }

    catch (error) {

        console.error(
            "Load HOD Teachers Error:",
            error
        );


        hodTeachers = [];


        updateTeacherStatistics();


        showTeacherTableMessage(
            error.message ||
            "Unable to load teachers.",
            true
        );
    }
}


/* ============================================================
   LOAD REAL AVERAGE ATTENDANCE
============================================================ */

async function loadAverageAttendance() {

    try {

        const response =
            await API.request(
                "GET",
                "/hods/analytics"
            );


        if (
            !response ||
            response.success !== true
        ) {

            return;
        }


        const percentage =
            response.attendance
                ?.percentage;


        if (
            percentage !== null &&
            percentage !== undefined &&
            !Number.isNaN(
                Number(percentage)
            )
        ) {

            hodAverageAttendance =
                Number(percentage);


            const counters =
                getTeacherStatisticElements();


            if (counters.attendance) {

                counters.attendance.textContent =
                    hodAverageAttendance
                        .toFixed(1)
                        .replace(".0", "") +
                    "%";
            }
        }
    }

    catch (error) {

        console.error(
            "Teacher Attendance Summary Error:",
            error
        );
    }
}


/* ============================================================
   STATISTIC ELEMENTS
============================================================ */

function getTeacherStatisticElements() {

    const values =
        document.querySelectorAll(
            ".dashboard-cards .card-box h3"
        );


    return {

        total:
            values[0] || null,

        active:
            values[1] || null,

        face:
            values[2] || null,

        attendance:
            values[3] || null

    };
}


/* ============================================================
   UPDATE STATISTICS
============================================================ */

function updateTeacherStatistics() {

    const counters =
        getTeacherStatisticElements();


    const total =
        hodTeachers.length;


    const active =
        hodTeachers.filter(
            function (teacher) {

                return (
                    String(
                        teacher.status || ""
                    )
                        .trim()
                        .toLowerCase()
                    === "active"
                );
            }
        ).length;


    if (counters.total) {
        counters.total.textContent =
            String(total);
    }


    if (counters.active) {
        counters.active.textContent =
            String(active);
    }


    /*
     * No fake face-registration number.
     */
    if (counters.face) {
        counters.face.textContent = "--";
    }
}


/* ============================================================
   DEPARTMENT FILTER
============================================================ */

function updateDepartmentFilter() {

    const departmentFilter =
        document.getElementById(
            "departmentFilter"
        );


    if (!departmentFilter) {
        return;
    }


    departmentFilter.innerHTML = `
        <option value="all">
            All Departments
        </option>
    `;


    if (hodDepartmentName) {

        const option =
            document.createElement(
                "option"
            );


        option.value =
            hodDepartmentName;


        option.textContent =
            hodDepartmentName;


        departmentFilter.appendChild(
            option
        );
    }
}


/* ============================================================
   FILTER EVENTS
============================================================ */

function bindTeacherFilters() {

    const teacherSearch =
        document.getElementById(
            "teacherSearch"
        );


    const globalSearch =
        document.getElementById(
            "globalSearch"
        );


    const departmentFilter =
        document.getElementById(
            "departmentFilter"
        );


    const statusFilter =
        document.getElementById(
            "statusFilter"
        );


    const resetFilterBtn =
        document.getElementById(
            "resetFilterBtn"
        );


    if (teacherSearch) {

        teacherSearch.addEventListener(
            "input",
            applyTeacherFilters
        );
    }


    /*
     * Top navbar search also searches teachers.
     */
    if (globalSearch) {

        globalSearch.addEventListener(
            "input",
            function () {

                if (teacherSearch) {

                    teacherSearch.value =
                        globalSearch.value;
                }


                applyTeacherFilters();
            }
        );
    }


    if (departmentFilter) {

        departmentFilter.addEventListener(
            "change",
            applyTeacherFilters
        );
    }


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            applyTeacherFilters
        );
    }


    if (resetFilterBtn) {

        resetFilterBtn.addEventListener(
            "click",
            function () {

                if (teacherSearch) {
                    teacherSearch.value = "";
                }


                if (globalSearch) {
                    globalSearch.value = "";
                }


                if (departmentFilter) {
                    departmentFilter.value =
                        "all";
                }


                if (statusFilter) {
                    statusFilter.value =
                        "all";
                }


                applyTeacherFilters();
            }
        );
    }
}


/* ============================================================
   APPLY FILTERS
============================================================ */

function applyTeacherFilters() {

    const teacherSearch =
        document.getElementById(
            "teacherSearch"
        );


    const departmentFilter =
        document.getElementById(
            "departmentFilter"
        );


    const statusFilter =
        document.getElementById(
            "statusFilter"
        );


    const searchValue =
        String(
            teacherSearch?.value || ""
        )
            .trim()
            .toLowerCase();


    const departmentValue =
        String(
            departmentFilter?.value ||
            "all"
        )
            .trim()
            .toLowerCase();


    const statusValue =
        String(
            statusFilter?.value ||
            "all"
        )
            .trim()
            .toLowerCase();


    const filteredTeachers =
        hodTeachers.filter(
            function (teacher) {

                const searchableText =
                    [
                        teacher.teacher_code,
                        teacher.full_name,
                        teacher.email,
                        teacher.phone,
                        teacher.department,
                        teacher.designation,
                        teacher.qualification
                    ]
                        .filter(Boolean)
                        .join(" ")
                        .toLowerCase();


                const teacherDepartment =
                    String(
                        teacher.department || ""
                    )
                        .trim()
                        .toLowerCase();


                const teacherStatus =
                    String(
                        teacher.status || ""
                    )
                        .trim()
                        .toLowerCase();


                const searchMatch =
                    !searchValue ||
                    searchableText.includes(
                        searchValue
                    );


                const departmentMatch =
                    departmentValue === "all" ||
                    teacherDepartment ===
                        departmentValue;


                const statusMatch =
                    statusValue === "all" ||
                    teacherStatus ===
                        statusValue;


                return (
                    searchMatch &&
                    departmentMatch &&
                    statusMatch
                );
            }
        );


    renderTeachers(
        filteredTeachers
    );
}


/* ============================================================
   RENDER TEACHERS
============================================================ */

function renderTeachers(
    teachers
) {

    const tbody =
        getTeacherTableBody();


    if (!tbody) {
        return;
    }


    if (teachers.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td
                    colspan="10"
                    class="text-center text-muted py-4">

                    No teachers found.

                </td>
            </tr>
        `;

        return;
    }


    tbody.innerHTML =
        teachers
            .map(
                function (teacher) {

                    const photo =
                        getTeacherPhotoHtml(
                            teacher
                        );


                    const status =
                        getTeacherStatusHtml(
                            teacher.status
                        );


                    /*
                     * Subject is NOT returned by
                     * /hods/teachers currently.
                     *
                     * Do not invent one.
                     */
                    const subject = "--";


                    /*
                     * Per-teacher attendance is not
                     * part of this endpoint.
                     */
                    const attendance = "--";


                    /*
                     * Face registration backend is
                     * not final yet.
                     */
                    const face = `
                        <span class="badge bg-secondary">
                            Not Available
                        </span>
                    `;


                    return `
                        <tr
                            data-teacher-id="${Number(
                                teacher.id
                            )}"
                            data-department="${escapeHtml(
                                teacher.department ||
                                ""
                            )}"
                            data-status="${escapeHtml(
                                teacher.status ||
                                ""
                            )}">

                            <td>
                                ${photo}
                            </td>


                            <td>
                                ${escapeHtml(
                                    teacher.teacher_code ||
                                    "-"
                                )}
                            </td>


                            <td>
                                ${escapeHtml(
                                    teacher.full_name ||
                                    "-"
                                )}
                            </td>


                            <td>
                                ${escapeHtml(
                                    teacher.email ||
                                    "-"
                                )}
                            </td>


                            <td>
                                ${subject}
                            </td>


                            <td>
                                ${escapeHtml(
                                    teacher.department ||
                                    hodDepartmentName ||
                                    "-"
                                )}
                            </td>


                            <td>

                                <span class="badge bg-secondary">
                                    ${attendance}
                                </span>

                            </td>


                            <td>
                                ${face}
                            </td>


                            <td>
                                ${status}
                            </td>


                            <td>

                                <div class="d-flex gap-1">

                                    <button
                                        type="button"
                                        class="btn btn-info btn-sm text-white viewTeacherBtn"
                                        data-teacher-id="${Number(
                                            teacher.id
                                        )}"
                                        title="View Teacher">

                                        <i class="fa-solid fa-eye"></i>

                                    </button>


                                   


                                    <a
                                        href="performance.html"
                                        class="btn btn-primary btn-sm"
                                        title="Performance">

                                        <i class="fa-solid fa-chart-line"></i>

                                    </a>


                                

                                </div>

                            </td>

                        </tr>
                    `;
                }
            )
            .join("");
}


/* ============================================================
   TEACHER PHOTO
============================================================ */

function getTeacherPhotoHtml(
    teacher
) {

    if (!teacher.photo_url) {

        return `
            <div
                class="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center"
                style="
                    width:45px;
                    height:45px;
                ">

                <i class="fa-solid fa-user"></i>

            </div>
        `;
    }


    const photoUrl =
        buildBackendFileUrl(
            teacher.photo_url
        );


    return `
        <img
            src="${escapeHtml(photoUrl)}"
            width="45"
            height="45"
            class="rounded-circle"
            style="object-fit:cover;"
            alt="${escapeHtml(
                teacher.full_name ||
                "Teacher"
            )}"
            onerror="
                this.style.display='none';
                this.nextElementSibling.style.display='flex';
            ">

        <div
            class="rounded-circle bg-secondary text-white align-items-center justify-content-center"
            style="
                width:45px;
                height:45px;
                display:none;
            ">

            <i class="fa-solid fa-user"></i>

        </div>
    `;
}


/* ============================================================
   BACKEND FILE URL
============================================================ */

function buildBackendFileUrl(
    value
) {

    let path =
        String(
            value || ""
        )
            .trim()
            .replaceAll(
                "\\",
                "/"
            );


    if (
        path.startsWith(
            "http://"
        ) ||
        path.startsWith(
            "https://"
        )
    ) {

        return path;
    }


    if (!path.startsWith("/")) {

        path =
            "/" + path;
    }


    return (
        "http://127.0.0.1:5000" +
        path
    );
}


/* ============================================================
   STATUS BADGE
============================================================ */

function getTeacherStatusHtml(
    status
) {

    const value =
        String(
            status || ""
        )
            .trim()
            .toLowerCase();


    if (value === "active") {

        return `
            <span class="badge bg-success">
                Active
            </span>
        `;
    }


    if (value === "inactive") {

        return `
            <span class="badge bg-secondary">
                Inactive
            </span>
        `;
    }


    if (!value) {

        return `
            <span class="badge bg-secondary">
                -
            </span>
        `;
    }


    return `
        <span class="badge bg-warning text-dark">
            ${escapeHtml(status)}
        </span>
    `;
}


/* ============================================================
   TABLE ACTIONS
============================================================ */

function bindTeacherTableActions() {

    const teacherTable =
        document.getElementById(
            "teacherTable"
        );


    if (!teacherTable) {
        return;
    }


    teacherTable.addEventListener(
        "click",
        async function (event) {

            const viewButton =
                event.target.closest(
                    ".viewTeacherBtn"
                );


            if (!viewButton) {
                return;
            }


            const teacherId =
                Number(
                    viewButton.dataset
                        .teacherId
                );


            if (!teacherId) {
                return;
            }


            await viewTeacher(
                teacherId
            );
        }
    );
}


/* ============================================================
   VIEW REAL TEACHER DETAILS
============================================================ */

async function viewTeacher(
    teacherId
) {

    try {

        const response =
            await API.request(
                "GET",
                `/hods/teachers/${teacherId}`
            );


        if (
            !response ||
            response.success !== true ||
            !response.data
        ) {

            throw new Error(
                response?.message ||
                "Unable to load teacher details."
            );
        }


        const teacher =
            response.data;


        setText(
            "viewTeacherId",
            teacher.teacher_code ||
            "-"
        );


        setText(
            "viewTeacherName",
            teacher.full_name ||
            "-"
        );


        setText(
            "viewTeacherEmail",
            teacher.email ||
            "-"
        );


        /*
         * Subject mapping is not available
         * from current teacher endpoint.
         */
        setText(
            "viewTeacherSubject",
            "--"
        );


        setText(
            "viewTeacherDepartment",
            teacher.department ||
            "-"
        );


        /*
         * Per-teacher attendance is not
         * returned from this endpoint.
         */
        setText(
            "viewTeacherAttendance",
            "--"
        );


        const modalElement =
            document.getElementById(
                "viewTeacherModal"
            );


        if (
            modalElement &&
            typeof bootstrap !== "undefined"
        ) {

            const modal =
                bootstrap.Modal
                    .getOrCreateInstance(
                        modalElement
                    );


            modal.show();
        }
    }

    catch (error) {

        console.error(
            "View Teacher Error:",
            error
        );


        alert(
            error.message ||
            "Unable to load teacher details."
        );
    }
}




/* ============================================================
   EXPORT BUTTONS
============================================================ */

function bindExportButtons() {

    const excelButton =
        document.getElementById(
            "exportExcelBtn"
        );


    const pdfButton =
        document.getElementById(
            "exportPdfBtn"
        );


    if (excelButton) {

        excelButton.addEventListener(
            "click",
            exportTeacherCsv
        );
    }


    if (pdfButton) {

        pdfButton.addEventListener(
            "click",
            exportTeacherPdf
        );
    }
}


/* ============================================================
   EXPORT TEACHER LIST AS REAL PDF
============================================================ */

function exportTeacherPdf() {

    if (
        !window.jspdf ||
        !window.jspdf.jsPDF
    ) {

        alert(
            "PDF library could not be loaded."
        );

        return;
    }


    if (
        !Array.isArray(hodTeachers) ||
        hodTeachers.length === 0
    ) {

        alert(
            "No teacher data available to export."
        );

        return;
    }


    const {
        jsPDF
    } = window.jspdf;


    const pdf =
        new jsPDF(
            "landscape",
            "mm",
            "a4"
        );


    /*
     * Title
     */
    pdf.setFontSize(18);

    pdf.text(
        "Faculty Management & Productivity System",
        14,
        16
    );


    pdf.setFontSize(14);

    pdf.text(
        "HOD - Teacher List",
        14,
        25
    );


    /*
     * Department
     */
    pdf.setFontSize(10);

    pdf.text(
        "Department: " +
        (
            hodDepartmentName ||
            "-"
        ),
        14,
        33
    );


    pdf.text(
        "Total Teachers: " +
        hodTeachers.length,
        14,
        39
    );


    /*
     * PDF table rows
     */
    const rows =
        hodTeachers.map(
            function (teacher) {

                return [

                    teacher.teacher_code ||
                    "-",

                    teacher.full_name ||
                    "-",

                    teacher.email ||
                    "-",

                    teacher.phone ||
                    "-",

                    teacher.department ||
                    hodDepartmentName ||
                    "-",

                    teacher.designation ||
                    "-",

                    teacher.status ||
                    "-"
                ];
            }
        );


    /*
     * Create table
     */
    pdf.autoTable({

        startY: 46,

        head: [[

            "Teacher ID",
            "Name",
            "Email",
            "Phone",
            "Department",
            "Designation",
            "Status"

        ]],

        body: rows,

        styles: {

            fontSize: 9,

            cellPadding: 3,

            overflow: "linebreak"
        },

        headStyles: {

            fontStyle: "bold"
        },

        margin: {

            left: 14,
            right: 14
        }

    });


    /*
     * Footer
     */
    const pageCount =
        pdf.internal
            .getNumberOfPages();


    for (
        let page = 1;
        page <= pageCount;
        page++
    ) {

        pdf.setPage(page);

        pdf.setFontSize(8);


        pdf.text(

            "Faculty Management & Productivity System",

            14,

            pdf.internal
                .pageSize
                .getHeight() - 8
        );


        pdf.text(

            "Page " +
            page +
            " of " +
            pageCount,

            pdf.internal
                .pageSize
                .getWidth() - 35,

            pdf.internal
                .pageSize
                .getHeight() - 8
        );
    }


    /*
     * Actual PDF download
     */
    pdf.save(
        "hod-teacher-list.pdf"
    );
}

/* ============================================================
   EXPORT REAL DISPLAYED TEACHERS
============================================================ */

function exportTeacherCsv() {

    const teacherTable =
        document.getElementById(
            "teacherTable"
        );


    if (!teacherTable) {
        return;
    }


    const rows =
        teacherTable.querySelectorAll(
            "tr"
        );


    const csvRows = [];


    rows.forEach(
        function (row) {

            if (
                row.style.display ===
                "none"
            ) {

                return;
            }


            const columns =
                row.querySelectorAll(
                    "th, td"
                );


            if (
                columns.length === 1
            ) {

                return;
            }


            const values = [];


            columns.forEach(
                function (
                    column,
                    index
                ) {

                    /*
                     * Skip:
                     * 0 = Photo
                     * 9 = Actions
                     */
                    if (
                        index === 0 ||
                        index === 9
                    ) {

                        return;
                    }


                    values.push(
                        csvEscape(
                            column.innerText
                                .trim()
                        )
                    );
                }
            );


            csvRows.push(
                values.join(",")
            );
        }
    );


    if (
        csvRows.length <= 1
    ) {

        alert(
            "No teacher data available to export."
        );

        return;
    }


    const blob =
        new Blob(
            [
                csvRows.join(
                    "\n"
                )
            ],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const link =
        document.createElement(
            "a"
        );


    link.href = url;

    link.download =
        "hod-teacher-list.csv";


    document.body.appendChild(
        link
    );


    link.click();


    document.body.removeChild(
        link
    );


    URL.revokeObjectURL(
        url
    );
}


/* ============================================================
   TABLE BODY
============================================================ */

function getTeacherTableBody() {

    const teacherTable =
        document.getElementById(
            "teacherTable"
        );


    if (!teacherTable) {
        return null;
    }


    return teacherTable.querySelector(
        "tbody"
    );
}


/* ============================================================
   TABLE MESSAGE
============================================================ */

function showTeacherTableMessage(
    message,
    isError = false
) {

    const tbody =
        getTeacherTableBody();


    if (!tbody) {
        return;
    }


    tbody.innerHTML = `
        <tr>

            <td
                colspan="10"
                class="text-center py-4 ${
                    isError
                        ? "text-danger"
                        : "text-muted"
                }">

                ${escapeHtml(message)}

            </td>

        </tr>
    `;
}


/* ============================================================
   SET TEXT
============================================================ */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (element) {

        element.textContent =
            value;
    }
}


/* ============================================================
   CSV ESCAPE
============================================================ */

function csvEscape(
    value
) {

    return (
        '"' +
        String(
            value ?? ""
        )
            .replaceAll(
                '"',
                '""'
            ) +
        '"'
    );
}


/* ============================================================
   SAFE HTML
============================================================ */

function escapeHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}