// ============================================================
// REPORTS.JS
// Faculty Management & Productivity System
// ============================================================

const REPORT_API = {
    teachers: "http://127.0.0.1:5000/api/teachers",
    hods: "http://127.0.0.1:5000/api/hods",
    students: "http://127.0.0.1:5000/api/students",
    recruiters: "http://127.0.0.1:5000/api/recruiters",
    performance: "http://127.0.0.1:5000/api/performance"
};

let currentReport = {
    title: "",
    subtitle: "",
    fileName: "Report",
    columns: [],
    rows: []
};



// ============================================================
// FETCH RECORDS
// ============================================================

async function fetchReportRecords(url) {

    const response =
        await fetch(url);

    let result;


    try {

        result =
            await response.json();

    } catch (error) {

        throw new Error(
            "Invalid response received from backend."
        );

    }


    if (!response.ok) {

        throw new Error(
            result.message ||
            result.error ||
            "Failed to load report data."
        );

    }


    if (
        Array.isArray(result)
    ) {

        return result;

    }


    if (
        result &&
        Array.isArray(result.data)
    ) {

        return result.data;

    }


    if (
        result &&
        result.data &&
        Array.isArray(result.data.records)
    ) {

        return result.data.records;

    }


    if (
        result &&
        Array.isArray(result.records)
    ) {

        return result.records;

    }


    return [];

}


// ============================================================
// SAFE TEXT
// ============================================================

function safeText(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "-";

    }

    return String(value);

}


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(value) {

    return safeText(value)

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


// ============================================================
// DEPARTMENT
// ============================================================

function getDepartmentName(record) {

    if (!record) {

        return "Not Assigned";

    }


    if (
        typeof record.department === "string" &&
        record.department.trim()
    ) {

        return record.department.trim();

    }


    if (
        record.department &&
        typeof record.department === "object" &&
        record.department.name
    ) {

        return String(
            record.department.name
        ).trim();

    }


    if (
        record.department_name
    ) {

        return String(
            record.department_name
        ).trim();

    }


    return "Not Assigned";

}


// ============================================================
// DATE FORMAT
// ============================================================

function formatDate(value) {

    if (
        !value ||
        value === "-"
    ) {

        return "-";

    }


    const text =
        String(value);


    const match =
        text.match(
            /^(\d{4})-(\d{2})-(\d{2})/
        );


    if (!match) {

        return text;

    }


    return (
        match[3]
        + "-"
        + match[2]
        + "-"
        + match[1]
    );

}


// ============================================================
// GET MODAL
// ============================================================

function getReportModal() {

    const element =
        document.getElementById(
            "reportModal"
        );


    if (!element) {

        alert(
            "Report modal not found."
        );

        return null;

    }


    if (
        typeof bootstrap === "undefined"
    ) {

        alert(
            "Bootstrap is not loaded."
        );

        return null;

    }


    return bootstrap.Modal
        .getOrCreateInstance(
            element
        );

}


// ============================================================
// SHOW LOADING
// ============================================================

function showReportLoading(
    title,
    subtitle
) {

    const modal =
        getReportModal();


    if (!modal) {

        return false;

    }


    const titleElement =
        document.getElementById(
            "reportTitle"
        );


    const subtitleElement =
        document.getElementById(
            "reportSubtitle"
        );


    const head =
        document.getElementById(
            "reportTableHead"
        );


    const body =
        document.getElementById(
            "reportTableBody"
        );


    const count =
        document.getElementById(
            "reportCount"
        );


    if (
        !titleElement ||
        !subtitleElement ||
        !head ||
        !body ||
        !count
    ) {

        alert(
            "Report modal elements are missing."
        );

        return false;

    }


    titleElement.innerHTML =

        '<i class="fa-solid fa-spinner fa-spin me-2"></i>'

        + escapeHtml(
            title
        );


    subtitleElement.textContent =
        subtitle;


    count.textContent =
        "Loading...";


    head.innerHTML =

        "<tr>"

        + "<th>Loading Report</th>"

        + "</tr>";


    body.innerHTML =

        '<tr>'

        + '<td class="text-center py-5">'

        + '<i class="fa-solid fa-spinner fa-spin fa-2x mb-3"></i>'

        + '<br>'

        + 'Generating report...'

        + '</td>'

        + '</tr>';


    modal.show();


    return true;

}


// ============================================================
// ERROR
// ============================================================

function showReportError(
    title,
    error
) {

    document.getElementById(
        "reportTitle"
    ).textContent =
        title;


    document.getElementById(
        "reportSubtitle"
    ).textContent =
        "Unable to generate report";


    document.getElementById(
        "reportCount"
    ).textContent =
        "Total Records: 0";


    document.getElementById(
        "reportTableHead"
    ).innerHTML =

        "<tr>"

        + "<th>Error</th>"

        + "</tr>";


    document.getElementById(
        "reportTableBody"
    ).innerHTML =

        '<tr>'

        + '<td class="text-center text-danger py-5">'

        + '<i class="fa-solid fa-circle-exclamation fa-2x mb-3"></i>'

        + '<br>'

        + escapeHtml(
            error.message ||
            error
        )

        + '</td>'

        + '</tr>';

}


// ============================================================
// STATUS BADGE
// ============================================================

function statusBadge(value) {

    const text =
        safeText(value);


    const status =
        text.toLowerCase();


    if (
        status === "active"
    ) {

        return (
            '<span class="badge bg-success">'
            + 'Active'
            + '</span>'
        );

    }


    if (
        status === "inactive"
    ) {

        return (
            '<span class="badge bg-danger">'
            + 'Inactive'
            + '</span>'
        );

    }


    if (
        status === "leave" ||
        status === "on leave"
    ) {

        return (
            '<span class="badge bg-warning text-dark">'
            + escapeHtml(text)
            + '</span>'
        );

    }


    return (
        '<span class="badge bg-secondary">'
        + escapeHtml(text)
        + '</span>'
    );

}


// ============================================================
// ROLE BADGE
// ============================================================

function roleBadge(value) {

    const role =
        safeText(value)
            .toLowerCase();


    if (
        role === "teacher"
    ) {

        return (
            '<span class="badge bg-info text-dark">'
            + 'Teacher'
            + '</span>'
        );

    }


    if (
        role === "hod"
    ) {

        return (
            '<span class="badge bg-primary">'
            + 'HOD'
            + '</span>'
        );

    }


    return escapeHtml(
        value
    );

}


// ============================================================
// PERFORMANCE BADGE
// ============================================================

function performanceBadge(value) {

    const band =
        safeText(value)
            .toLowerCase();


    if (
        band === "excellent"
    ) {

        return (
            '<span class="badge bg-success">'
            + 'Excellent'
            + '</span>'
        );

    }


    if (
        band === "good"
    ) {

        return (
            '<span class="badge bg-primary">'
            + 'Good'
            + '</span>'
        );

    }


    if (
        band === "average"
    ) {

        return (
            '<span class="badge bg-warning text-dark">'
            + 'Average'
            + '</span>'
        );

    }


    if (
        band === "poor"
    ) {

        return (
            '<span class="badge bg-danger">'
            + 'Poor'
            + '</span>'
        );

    }


    return escapeHtml(
        value
    );

}


// ============================================================
// CELL
// ============================================================

function renderCell(
    column,
    value
) {

    if (
        column.key === "status"
    ) {

        return statusBadge(
            value
        );

    }


    if (
        column.key === "role"
    ) {

        return roleBadge(
            value
        );

    }


    if (
        column.key === "performance"
    ) {

        return performanceBadge(
            value
        );

    }


    return escapeHtml(
        value
    );

}


// ============================================================
// RENDER REPORT
// ============================================================

function renderCurrentReport() {

    const title =
        document.getElementById(
            "reportTitle"
        );


    const subtitle =
        document.getElementById(
            "reportSubtitle"
        );


    const count =
        document.getElementById(
            "reportCount"
        );


    const head =
        document.getElementById(
            "reportTableHead"
        );


    const body =
        document.getElementById(
            "reportTableBody"
        );


    title.textContent =
        currentReport.title;


    subtitle.textContent =
        currentReport.subtitle;


    count.textContent =

        "Total Records: "

        + currentReport.rows.length;


    let headerHtml =
        "<tr><th>#</th>";


    currentReport.columns
        .forEach(
            function (column) {

                headerHtml +=

                    "<th>"

                    + escapeHtml(
                        column.label
                    )

                    + "</th>";

            }
        );


    headerHtml +=
        "</tr>";


    head.innerHTML =
        headerHtml;


    if (
        currentReport.rows.length === 0
    ) {

        body.innerHTML =

            '<tr>'

            + '<td colspan="'

            + (
                currentReport.columns.length
                + 1
            )

            + '" class="text-center text-muted py-5">'

            + 'No records found.'

            + '</td>'

            + '</tr>';


        return;

    }


    let bodyHtml =
        "";


    currentReport.rows
        .forEach(
            function (
                row,
                index
            ) {

                bodyHtml +=

                    "<tr><td>"

                    + (
                        index + 1
                    )

                    + "</td>";


                currentReport.columns
                    .forEach(
                        function (column) {

                            bodyHtml +=

                                "<td>"

                                + renderCell(
                                    column,
                                    row[
                                        column.key
                                    ]
                                )

                                + "</td>";

                        }
                    );


                bodyHtml +=
                    "</tr>";

            }
        );


    body.innerHTML =
        bodyHtml;

}


// ============================================================
// FACULTY REPORT
// ============================================================

async function generateFacultyReport() {

    if (
        !showReportLoading(
            "Faculty Report",
            "Teachers and HODs"
        )
    ) {

        return;

    }


    try {

        const data =
            await Promise.all([

                fetchReportRecords(
                    REPORT_API.teachers
                ),

                fetchReportRecords(
                    REPORT_API.hods
                )

            ]);


        const teachers =
            data[0];


        const hods =
            data[1];


        const rows =
            [];


        teachers.forEach(
            function (teacher) {

                rows.push({

                    code:
                        teacher.teacher_code ||
                        "-",


                    name:
                        teacher.full_name ||
                        "-",


                    role:
                        "Teacher",


                    department:
                        getDepartmentName(
                            teacher
                        ),


                    designation:
                        teacher.designation ||
                        "Teacher",


                    experience:

                        teacher.experience_years !== null &&

                        teacher.experience_years !== undefined

                            ? (
                                teacher.experience_years
                                + " Years"
                            )

                            : "-",


                    joining_date:
                        formatDate(
                            teacher.joining_date
                        ),


                    status:
                        teacher.status ||
                        "-"

                });

            }
        );


        hods.forEach(
            function (hod) {

                rows.push({

                    code:
                        hod.hod_code ||
                        "-",


                    name:
                        hod.full_name ||
                        "-",


                    role:
                        "HOD",


                    department:
                        getDepartmentName(
                            hod
                        ),


                    designation:
                        hod.designation ||
                        "HOD",


                    experience:

                        hod.experience_years !== null &&

                        hod.experience_years !== undefined

                            ? (
                                hod.experience_years
                                + " Years"
                            )

                            : "-",


                    joining_date:
                        formatDate(
                            hod.joining_date
                        ),


                    status:
                        hod.status ||
                        "-"

                });

            }
        );


        currentReport = {

            title:
                "Faculty Report",


            subtitle:
                "Teachers and HODs",


            fileName:
                "Faculty_Report",


            columns: [

                {
                    key: "code",
                    label: "Faculty ID"
                },

                {
                    key: "name",
                    label: "Name"
                },

                {
                    key: "role",
                    label: "Role"
                },

                {
                    key: "department",
                    label: "Department"
                },

                {
                    key: "designation",
                    label: "Designation"
                },

                {
                    key: "experience",
                    label: "Experience"
                },

                {
                    key: "joining_date",
                    label: "Joining Date"
                },

                {
                    key: "status",
                    label: "Status"
                }

            ],


            rows:
                rows

        };


        renderCurrentReport();

    }

    catch (error) {

        console.error(
            "Faculty report error:",
            error
        );


        showReportError(
            "Faculty Report",
            error
        );

    }

}


// ============================================================
// PERFORMANCE
// ============================================================

function calculatePerformance(
    score,
    maxScore
) {

    const s =
        Number(score);


    const m =
        Number(maxScore);


    const percentage =

        Number.isFinite(s) &&

        Number.isFinite(m) &&

        m > 0

            ? (
                s /
                m *
                100
            )

            : 0;


    let performance =
        "Poor";


    if (
        percentage >= 80
    ) {

        performance =
            "Excellent";

    }

    else if (
        percentage >= 60
    ) {

        performance =
            "Good";

    }

    else if (
        percentage >= 40
    ) {

        performance =
            "Average";

    }


    return {

        percentage:
            percentage,

        performance:
            performance

    };

}


async function generatePerformanceReport() {

    if (
        !showReportLoading(
            "Performance Report",
            "Faculty Performance Records"
        )
    ) {

        return;

    }


    try {

        const data =
            await Promise.all([

                fetchReportRecords(
                    REPORT_API.performance
                ),

                fetchReportRecords(
                    REPORT_API.teachers
                ),

                fetchReportRecords(
                    REPORT_API.hods
                )

            ]);


        const records =
            data[0];


        const teachers =
            data[1];


        const hods =
            data[2];


        const facultyMap =
            new Map();


        teachers.forEach(
            function (teacher) {

                if (
                    teacher.user_id !== null &&
                    teacher.user_id !== undefined
                ) {

                    facultyMap.set(

                        String(
                            teacher.user_id
                        ),

                        {

                            name:
                                teacher.full_name ||
                                "-",


                            role:
                                "Teacher",


                            department:
                                getDepartmentName(
                                    teacher
                                )

                        }

                    );

                }

            }
        );


        hods.forEach(
            function (hod) {

                if (
                    hod.user_id !== null &&
                    hod.user_id !== undefined
                ) {

                    facultyMap.set(

                        String(
                            hod.user_id
                        ),

                        {

                            name:
                                hod.full_name ||
                                "-",


                            role:
                                "HOD",


                            department:
                                getDepartmentName(
                                    hod
                                )

                        }

                    );

                }

            }
        );


        const rows =
            records.map(
                function (record) {

                    const faculty =
                        facultyMap.get(

                            String(
                                record.user_id
                            )

                        ) || {};


                    const info =
                        calculatePerformance(
                            record.score,
                            record.max_score
                        );


                    let percentage =
                        info.percentage;


                    if (
                        record.percentage !== null &&
                        record.percentage !== undefined &&
                        !Number.isNaN(
                            Number(
                                record.percentage
                            )
                        )
                    ) {

                        percentage =
                            Number(
                                record.percentage
                            );

                    }


                    return {

                        name:
                            faculty.name ||

                            (
                                "User #"

                                + safeText(
                                    record.user_id
                                )
                            ),


                        role:
                            faculty.role ||
                            "Faculty",


                        department:
                            faculty.department ||
                            "Not Assigned",


                        subject:
                            record.subject ||
                            "-",


                        term:
                            record.term ||
                            "-",


                        score:

                            safeText(
                                record.score
                            )

                            + " / "

                            + safeText(
                                record.max_score
                            ),


                        percentage:

                            percentage.toFixed(
                                1
                            )

                            + "%",


                        grade:
                            record.grade ||
                            "-",


                        performance:
                            record.band ||
                            info.performance,


                        remarks:
                            record.remarks ||
                            "-"

                    };

                }
            );


        currentReport = {

            title:
                "Performance Report",


            subtitle:
                "Faculty Performance Records",


            fileName:
                "Performance_Report",


            columns: [

                {
                    key: "name",
                    label: "Faculty"
                },

                {
                    key: "role",
                    label: "Role"
                },

                {
                    key: "department",
                    label: "Department"
                },

                {
                    key: "subject",
                    label: "Subject"
                },

                {
                    key: "term",
                    label: "Term"
                },

                {
                    key: "score",
                    label: "Score"
                },

                {
                    key: "percentage",
                    label: "Percentage"
                },

                {
                    key: "grade",
                    label: "Grade"
                },

                {
                    key: "performance",
                    label: "Performance"
                },

                {
                    key: "remarks",
                    label: "Remarks"
                }

            ],


            rows:
                rows

        };


        renderCurrentReport();

    }

    catch (error) {

        console.error(
            "Performance report error:",
            error
        );


        showReportError(
            "Performance Report",
            error
        );

    }

}


// ============================================================
// RECRUITMENT REPORT
// ============================================================

async function generateRecruitmentReport() {

    if (
        !showReportLoading(
            "Recruitment Report",
            "Recruiters and Registered Companies"
        )
    ) {

        return;

    }


    try {

        const recruiters =
            await fetchReportRecords(
                REPORT_API.recruiters
            );


        const rows =
            recruiters.map(
                function (recruiter) {

                    return {

                        code:
                            recruiter.recruiter_code ||
                            "-",


                        company:
                            recruiter.company_name ||
                            "-",


                        name:
                            recruiter.full_name ||
                            "-",


                        designation:
                            recruiter.designation ||
                            "-",


                        email:
                            recruiter.email ||
                            "-",


                        phone:
                            recruiter.phone ||
                            "-",


                        industry:
                            recruiter.industry_type ||
                            "-",


                        hiring_role:
                            recruiter.hiring_role ||
                            "-",


                        package:
                            recruiter.package_offered ||
                            "-",


                        hiring_date:
                            formatDate(
                                recruiter.hiring_date
                            ),


                        status:
                            recruiter.status ||
                            "-"

                    };

                }
            );


        currentReport = {

            title:
                "Recruitment Report",


            subtitle:
                "Recruiters and Registered Companies",


            fileName:
                "Recruitment_Report",


            columns: [

                {
                    key: "code",
                    label: "Recruiter ID"
                },

                {
                    key: "company",
                    label: "Company"
                },

                {
                    key: "name",
                    label: "Contact Person"
                },

                {
                    key: "designation",
                    label: "Designation"
                },

                {
                    key: "email",
                    label: "Email"
                },

                {
                    key: "phone",
                    label: "Phone"
                },

                {
                    key: "industry",
                    label: "Industry"
                },

                {
                    key: "hiring_role",
                    label: "Hiring Role"
                },

                {
                    key: "package",
                    label: "Package"
                },

                {
                    key: "hiring_date",
                    label: "Hiring Date"
                },

                {
                    key: "status",
                    label: "Status"
                }

            ],


            rows:
                rows

        };


        renderCurrentReport();

    }

    catch (error) {

        console.error(
            "Recruitment report error:",
            error
        );


        showReportError(
            "Recruitment Report",
            error
        );

    }

}


// ============================================================
// DEPARTMENT REPORT
// ============================================================

async function generateDepartmentReport() {

    if (
        !showReportLoading(
            "Department Report",
            "Department-wise Faculty and Student Summary"
        )
    ) {

        return;

    }


    try {

        const data =
            await Promise.all([

                fetchReportRecords(
                    REPORT_API.teachers
                ),

                fetchReportRecords(
                    REPORT_API.hods
                ),

                fetchReportRecords(
                    REPORT_API.students
                )

            ]);


        const teachers =
            data[0];


        const hods =
            data[1];


        const students =
            data[2];


        const departmentMap =
            new Map();


        function ensureDepartment(name) {

            const department =

                name &&
                String(name).trim()

                    ? String(name).trim()

                    : "Not Assigned";


            if (
                !departmentMap.has(
                    department
                )
            ) {

                departmentMap.set(

                    department,

                    {

                        department:
                            department,

                        hodNames:
                            [],

                        teachers:
                            0,

                        hods:
                            0,

                        students:
                            0

                    }

                );

            }


            return departmentMap.get(
                department
            );

        }


        teachers.forEach(
            function (teacher) {

                ensureDepartment(

                    getDepartmentName(
                        teacher
                    )

                ).teachers++;

            }
        );


        hods.forEach(
            function (hod) {

                const item =
                    ensureDepartment(

                        getDepartmentName(
                            hod
                        )

                    );


                item.hods++;


                if (
                    hod.full_name
                ) {

                    item.hodNames.push(
                        hod.full_name
                    );

                }

            }
        );


        students.forEach(
            function (student) {

                ensureDepartment(

                    getDepartmentName(
                        student
                    )

                ).students++;

            }
        );


        const rows =
            Array.from(
                departmentMap.values()
            )

                .sort(
                    function (
                        a,
                        b
                    ) {

                        return a.department
                            .localeCompare(
                                b.department
                            );

                    }
                )

                .map(
                    function (item) {

                        return {

                            department:
                                item.department,


                            hod:

                                item.hodNames.length > 0

                                    ? item.hodNames.join(
                                        ", "
                                    )

                                    : "Not Assigned",


                            teachers:
                                item.teachers,


                            hods:
                                item.hods,


                            total_faculty:

                                item.teachers

                                + item.hods,


                            students:
                                item.students

                        };

                    }
                );


        currentReport = {

            title:
                "Department Report",


            subtitle:
                "Department-wise Faculty and Student Distribution",


            fileName:
                "Department_Report",


            columns: [

                {
                    key: "department",
                    label: "Department"
                },

                {
                    key: "hod",
                    label: "HOD"
                },

                {
                    key: "teachers",
                    label: "Teachers"
                },

                {
                    key: "hods",
                    label: "HOD Count"
                },

                {
                    key: "total_faculty",
                    label: "Total Faculty"
                },

                {
                    key: "students",
                    label: "Students"
                }

            ],


            rows:
                rows

        };


        renderCurrentReport();

    }

    catch (error) {

        console.error(
            "Department report error:",
            error
        );


        showReportError(
            "Department Report",
            error
        );

    }

}


// ============================================================
// STUDENT REPORT
// ============================================================

async function generateStudentReport() {

    if (
        !showReportLoading(
            "Student Report",
            "Registered Student Records"
        )
    ) {

        return;

    }


    try {

        const students =
            await fetchReportRecords(
                REPORT_API.students
            );


        const rows =
            students.map(
                function (student) {

                    return {

                        student_id:
                            student.student_code ||
                            "-",


                        roll_number:
                            student.roll_number ||
                            "-",


                        name:
                            student.full_name ||
                            "-",


                        course:
                            student.course ||
                            "-",


                        department:
                            getDepartmentName(
                                student
                            ),


                        semester:
                            student.semester ||
                            "-",


                        section:
                            student.section ||
                            "-",


                        email:
                            student.email ||
                            "-",


                        phone:
                            student.phone ||
                            "-",


                        status:
                            student.status ||
                            "-"

                    };

                }
            );


        currentReport = {

            title:
                "Student Report",


            subtitle:
                "Registered Student Records",


            fileName:
                "Student_Report",


            columns: [

                {
                    key: "student_id",
                    label: "Student ID"
                },

                {
                    key: "roll_number",
                    label: "Roll Number"
                },

                {
                    key: "name",
                    label: "Name"
                },

                {
                    key: "course",
                    label: "Course"
                },

                {
                    key: "department",
                    label: "Department"
                },

                {
                    key: "semester",
                    label: "Semester"
                },

                {
                    key: "section",
                    label: "Section"
                },

                {
                    key: "email",
                    label: "Email"
                },

                {
                    key: "phone",
                    label: "Phone"
                },

                {
                    key: "status",
                    label: "Status"
                }

            ],


            rows:
                rows

        };


        renderCurrentReport();

    }

    catch (error) {

        console.error(
            "Student report error:",
            error
        );


        showReportError(
            "Student Report",
            error
        );

    }

}


// ============================================================
// EXCEL DATA
// ============================================================

function createExportMatrix() {

    const matrix =
        [];


    const header =
        ["#"];


    currentReport.columns
        .forEach(
            function (column) {

                header.push(
                    column.label
                );

            }
        );


    matrix.push(
        header
    );


    currentReport.rows
        .forEach(
            function (
                row,
                index
            ) {

                const values =
                    [
                        index + 1
                    ];


                currentReport.columns
                    .forEach(
                        function (column) {

                            values.push(

                                safeText(
                                    row[
                                        column.key
                                    ]
                                )

                            );

                        }
                    );


                matrix.push(
                    values
                );

            }
        );


    return matrix;

}


// ============================================================
// EXCEL EXPORT
// ============================================================

function exportCurrentReportExcel() {

    if (
        currentReport.rows.length === 0
    ) {

        alert(
            "Please generate a report first."
        );

        return;

    }


    const matrix =
        createExportMatrix();


    if (
        typeof XLSX !== "undefined"
    ) {

        const worksheet =
            XLSX.utils.aoa_to_sheet(
                matrix
            );


        const workbook =
            XLSX.utils.book_new();


        XLSX.utils.book_append_sheet(

            workbook,

            worksheet,

            "Report"

        );


        XLSX.writeFile(

            workbook,

            currentReport.fileName
            + ".xlsx"

        );


        return;

    }


    // CSV FALLBACK

    const csv =
        matrix

            .map(
                function (row) {

                    return row

                        .map(
                            function (value) {

                                return (

                                    '"'

                                    + String(value)
                                        .replaceAll(
                                            '"',
                                            '""'
                                        )

                                    + '"'

                                );

                            }
                        )

                        .join(",");

                }
            )

            .join("\r\n");


    const blob =
        new Blob(
            [
                "\ufeff"
                + csv
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


    link.href =
        url;


    link.download =
        currentReport.fileName
        + ".csv";


    document.body.appendChild(
        link
    );


    link.click();


    link.remove();


    URL.revokeObjectURL(
        url
    );

}


// ============================================================
// PRINTABLE TABLE
// ============================================================

function createPrintableTable() {

    let html =
        "<table><thead><tr><th>#</th>";


    currentReport.columns
        .forEach(
            function (column) {

                html +=

                    "<th>"

                    + escapeHtml(
                        column.label
                    )

                    + "</th>";

            }
        );


    html +=
        "</tr></thead><tbody>";


    currentReport.rows
        .forEach(
            function (
                row,
                index
            ) {

                html +=

                    "<tr><td>"

                    + (
                        index + 1
                    )

                    + "</td>";


                currentReport.columns
                    .forEach(
                        function (column) {

                            html +=

                                "<td>"

                                + escapeHtml(
                                    row[
                                        column.key
                                    ]
                                )

                                + "</td>";

                        }
                    );


                html +=
                    "</tr>";

            }
        );


    html +=
        "</tbody></table>";


    return html;

}


// ============================================================
// PRINT WINDOW
// ============================================================

function openReportPrintWindow() {

    if (
        currentReport.rows.length === 0
    ) {

        alert(
            "Please generate a report first."
        );

        return null;

    }


    const printWindow =
        window.open(
            "",
            "_blank"
        );


    if (!printWindow) {

        alert(
            "Please allow pop-ups in your browser."
        );

        return null;

    }


    const generated =
        new Date()
            .toLocaleString(
                "en-IN"
            );


    const table =
        createPrintableTable();


    const styles =

        "body{font-family:Arial,sans-serif;margin:25px;color:#222;}"

        + ".header{text-align:center;margin-bottom:20px;}"

        + ".header h2,.header h3{margin:5px 0;}"

        + ".info{display:flex;justify-content:space-between;margin-bottom:12px;font-size:12px;}"

        + "table{width:100%;border-collapse:collapse;}"

        + "th,td{border:1px solid #777;padding:7px;font-size:10px;text-align:left;word-break:break-word;}"

        + "th{background:#eee;}"

        + ".footer{text-align:center;margin-top:25px;font-size:10px;color:#666;}"

        + "@page{size:A4 landscape;margin:10mm;}";


    printWindow.document.open();


    printWindow.document.write(
        "<!DOCTYPE html>"
    );


    printWindow.document.write(
        "<html>"
    );


    printWindow.document.write(
        "<head>"
    );


    printWindow.document.write(
        "<meta charset='UTF-8'>"
    );


    printWindow.document.write(

        "<title>"

        + escapeHtml(
            currentReport.title
        )

        + "</title>"

    );


    printWindow.document.write(

        "<style>"

        + styles

        + "</style>"

    );


    printWindow.document.write(
        "</head><body>"
    );


    printWindow.document.write(

        "<div class='header'>"

        + "<h2>PATNA WOMEN'S COLLEGE</h2>"

        + "<div>(AUTONOMOUS)</div>"

        + "<div>Faculty Management &amp; Productivity System</div>"

        + "<h3>"

        + escapeHtml(
            currentReport.title
        )

        + "</h3>"

        + "<div>"

        + escapeHtml(
            currentReport.subtitle
        )

        + "</div>"

        + "</div>"

    );


    printWindow.document.write(

        "<div class='info'>"

        + "<span>Generated: "

        + escapeHtml(
            generated
        )

        + "</span>"

        + "<span>Total Records: "

        + currentReport.rows.length

        + "</span>"

        + "</div>"

    );


    printWindow.document.write(
        table
    );


    printWindow.document.write(

        "<div class='footer'>"

        + "Faculty Management &amp; Productivity System"

        + " | "

        + "Patna Women's College (Autonomous)"

        + "</div>"

    );


    printWindow.document.write(
        "</body></html>"
    );


    printWindow.document.close();


    return printWindow;

}


// ============================================================
// PRINT
// ============================================================

function printCurrentReport() {

    const win =
        openReportPrintWindow();


    if (!win) {

        return;

    }


    setTimeout(
        function () {

            win.focus();

            win.print();

        },
        400
    );

}


// ============================================================
// PDF
// ============================================================

// ============================================================
// DIRECT PDF DOWNLOAD
// ============================================================

function saveCurrentReportPDF() {


    if (
        currentReport.rows.length === 0
    ) {

        alert(
            "Please generate a report first."
        );

        return;

    }


    if (
        typeof window.jspdf === "undefined"
    ) {

        alert(
            "PDF library is not loaded."
        );

        return;

    }


    const jsPDF =
        window.jspdf.jsPDF;


    const doc =
        new jsPDF({

            orientation:
                "landscape",

            unit:
                "mm",

            format:
                "a4"

        });


    // ========================================================
    // COLLEGE HEADER
    // ========================================================

    doc.setFontSize(
        16
    );


    doc.text(

        "PATNA WOMEN'S COLLEGE",

        148,

        12,

        {
            align:
                "center"
        }

    );


    doc.setFontSize(
        9
    );


    doc.text(

        "(AUTONOMOUS)",

        148,

        18,

        {
            align:
                "center"
        }

    );


    doc.text(

        "Faculty Management & Productivity System",

        148,

        23,

        {
            align:
                "center"
        }

    );


    // ========================================================
    // REPORT TITLE
    // ========================================================

    doc.setFontSize(
        13
    );


    doc.text(

        currentReport.title,

        148,

        31,

        {
            align:
                "center"
        }

    );


    doc.setFontSize(
        8
    );


    doc.text(

        currentReport.subtitle,

        148,

        36,

        {
            align:
                "center"
        }

    );


    // ========================================================
    // GENERATED DATE
    // ========================================================

    const generatedDate =
        new Date()
            .toLocaleString(
                "en-IN"
            );


    doc.setFontSize(
        7
    );


    doc.text(

        "Generated: "
        + generatedDate,

        10,

        42

    );


    doc.text(

        "Total Records: "
        + currentReport.rows.length,

        287,

        42,

        {
            align:
                "right"
        }

    );


    // ========================================================
    // TABLE HEADER
    // ========================================================

    const tableHeaders =
        [
            "#"
        ];


    currentReport.columns
        .forEach(
            function (column) {

                tableHeaders.push(
                    column.label
                );

            }
        );


    // ========================================================
    // TABLE DATA
    // ========================================================

    const tableRows =
        [];


    currentReport.rows
        .forEach(
            function (
                row,
                index
            ) {


                const values =
                    [
                        index + 1
                    ];


                currentReport.columns
                    .forEach(
                        function (column) {


                            values.push(

                                safeText(
                                    row[
                                        column.key
                                    ]
                                )

                            );


                        }
                    );


                tableRows.push(
                    values
                );


            }
        );


    // ========================================================
    // CREATE TABLE
    // ========================================================

    doc.autoTable({

        head:
            [
                tableHeaders
            ],

        body:
            tableRows,

        startY:
            46,

        margin: {

            left:
                7,

            right:
                7,

            bottom:
                12

        },

        styles: {

            fontSize:
                6.5,

            cellPadding:
                1.7,

            overflow:
                "linebreak",

            valign:
                "middle"

        },

        headStyles: {

            fontStyle:
                "bold"

        },

        didDrawPage:
            function (data) {


                const pageNumber =
                    doc.internal
                        .getNumberOfPages();


                doc.setFontSize(
                    7
                );


                doc.text(

                    "Page "
                    + pageNumber,

                    148,

                    203,

                    {
                        align:
                            "center"
                    }

                );


            }

    });


    // ========================================================
    // DOWNLOAD PDF
    // ========================================================

    doc.save(

        currentReport.fileName
        + ".pdf"

    );

}


// ============================================================
// START
// ============================================================



console.log(
    "reports.js loaded successfully"
);