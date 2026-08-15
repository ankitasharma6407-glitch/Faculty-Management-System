// ==========================================
// Teacher List - API Integration
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    loadTeachers();


    // ==========================================
    // Load Teachers
    // ==========================================

    async function loadTeachers() {

        const tableBody =
            document.getElementById("teacherTable");

        if (!tableBody) {
            return;
        }

        // Loading message
        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center">
                    Loading teachers...
                </td>
            </tr>
        `;


        try {

            const response =
                await API.teachers.list();


            console.log(
                "Teachers API Response:",
                response
            );


            if (
                !response ||
                !response.success
            ) {

                throw new Error(
                    response?.message ||
                    "Failed to load teachers."
                );

            }


            const teachers =
                response.data || [];


            // ======================================
            // No Teachers
            // ======================================

            if (teachers.length === 0) {

                tableBody.innerHTML = `
                    <tr>
                        <td colspan="9"
                            class="text-center text-muted">

                            No teachers found.

                        </td>
                    </tr>
                `;

                return;
            }


            // ======================================
            // Create Rows
            // ======================================

            tableBody.innerHTML = "";


            teachers.forEach(function (teacher) {

                const row =
                    document.createElement("tr");


                // Photo
                let photoHTML = `
                    <div class="rounded-circle
                                bg-secondary
                                text-white
                                d-flex
                                align-items-center
                                justify-content-center"
                         style="width:45px;height:45px;">

                        <i class="fa-solid fa-user"></i>

                    </div>
                `;


                // If teacher has photo
                if (teacher.photo_url) {

                    let photoUrl =
                        teacher.photo_url
                            .replaceAll("\\", "/");


                    // Make relative upload path work
                    if (
                        !photoUrl.startsWith("http")
                    ) {

                        photoUrl =
                            "http://127.0.0.1:5000/" +
                            photoUrl;

                    }


                    photoHTML = `
                        <img
                            src="${photoUrl}"
                            class="rounded-circle"
                            width="45"
                            height="45"
                            style="object-fit:cover;"
                            onerror="this.style.display='none';">
                    `;

                }


                // Status
                let status =
                    teacher.status || "active";


                let statusBadge = "";


                if (
                    status.toLowerCase() ===
                    "active"
                ) {

                    statusBadge = `
                        <span class="badge bg-success">
                            Active
                        </span>
                    `;

                } else if (
                    status.toLowerCase() ===
                    "inactive"
                ) {

                    statusBadge = `
                        <span class="badge bg-secondary">
                            Inactive
                        </span>
                    `;

                } else {

                    statusBadge = `
                        <span class="badge bg-warning text-dark">
                            ${status}
                        </span>
                    `;

                }


                // ==================================
                // Row HTML
                // ==================================

                row.innerHTML = `

                    <td>
                        ${photoHTML}
                    </td>

                    <td>
                        ${teacher.teacher_code || "-"}
                    </td>

                    <td>
                        ${teacher.full_name || "-"}
                    </td>

                    <td>
                        ${teacher.department || "-"}
                    </td>

                    <td>
                        ${teacher.designation || "-"}
                    </td>

                    <td>
                        ${teacher.email || "-"}
                    </td>

                    <td>
                        ${teacher.phone || "-"}
                    </td>

                    <td>
                        ${statusBadge}
                    </td>

                    <td>

                        <a
                            href="view-teacher.html?id=${teacher.id}"
                            class="btn btn-info btn-sm">

                            <i class="fa-solid fa-eye"></i>

                        </a>


                        <a
                            href="edit-teacher.html?id=${teacher.id}"
                            class="btn btn-warning btn-sm">

                            <i class="fa-solid fa-pen"></i>

                        </a>


                        <button
                            class="btn btn-danger btn-sm deleteBtn"
                            data-id="${teacher.id}">

                            <i class="fa-solid fa-trash"></i>

                        </button>

                    </td>

                `;


                tableBody.appendChild(row);

            });


            // Add delete functionality
            addDeleteEvents();


        } catch (error) {

            console.error(
                "Load Teachers Error:",
                error
            );


            tableBody.innerHTML = `
                <tr>
                    <td colspan="9"
                        class="text-center text-danger">

                        Failed to load teachers.

                        <br>

                        <small>
                            ${error.message}
                        </small>

                    </td>
                </tr>
            `;

        }

    }


    // ==========================================
    // Delete Teacher
    // ==========================================

    function addDeleteEvents() {

        const deleteButtons =
            document.querySelectorAll(
                ".deleteBtn"
            );


        deleteButtons.forEach(function (button) {

            button.addEventListener(
                "click",
                async function () {

                    const teacherId =
                        this.dataset.id;


                    const confirmed =
                        confirm(
                            "Are you sure you want to delete this teacher?"
                        );


                    if (!confirmed) {
                        return;
                    }


                    try {

                        const response =
                            await API.teachers.remove(
                                teacherId
                            );


                        console.log(
                            "Delete Response:",
                            response
                        );


                        alert(
                            "Teacher deleted successfully."
                        );


                        // Reload list
                        loadTeachers();


                    } catch (error) {

                        console.error(
                            "Delete Teacher Error:",
                            error
                        );


                        alert(
                            error.message ||
                            "Failed to delete teacher."
                        );

                    }

                }
            );

        });

    }


    // ==========================================
    // Search
    // ==========================================

    const searchTeacher =
        document.getElementById(
            "searchTeacher"
        );


    if (searchTeacher) {

        searchTeacher.addEventListener(
            "input",
            function () {

                const value =
                    this.value
                        .toLowerCase()
                        .trim();


                const rows =
                    document.querySelectorAll(
                        "#teacherTable tr"
                    );


                rows.forEach(function (row) {

                    const text =
                        row.innerText
                            .toLowerCase();


                    row.style.display =
                        text.includes(value)
                            ? ""
                            : "none";

                });

            }
        );

    }


    // ==========================================
    // Department Filter
    // ==========================================

    const departmentFilter =
        document.getElementById(
            "departmentFilter"
        );


    if (departmentFilter) {

        departmentFilter.addEventListener(
            "change",
            function () {

                filterTeachers();

            }
        );

    }


    // ==========================================
    // Designation Filter
    // ==========================================

    const designationFilter =
        document.getElementById(
            "designationFilter"
        );


    if (designationFilter) {

        designationFilter.addEventListener(
            "change",
            function () {

                filterTeachers();

            }
        );

    }


    // ==========================================
    // Combined Filters
    // ==========================================

    function filterTeachers() {

        const searchValue =
            document.getElementById(
                "searchTeacher"
            )?.value
                .toLowerCase()
                .trim() || "";


        const departmentValue =
            document.getElementById(
                "departmentFilter"
            )?.value
                .toLowerCase()
                .trim() || "";


        const designationValue =
            document.getElementById(
                "designationFilter"
            )?.value
                .toLowerCase()
                .trim() || "";


        const rows =
            document.querySelectorAll(
                "#teacherTable tr"
            );


        rows.forEach(function (row) {

            const text =
                row.innerText
                    .toLowerCase();


            const matchesSearch =
                text.includes(searchValue);


            const matchesDepartment =
                !departmentValue ||
                text.includes(
                    departmentValue
                );


            const matchesDesignation =
                !designationValue ||
                text.includes(
                    designationValue
                );


            row.style.display =
                matchesSearch &&
                matchesDepartment &&
                matchesDesignation
                    ? ""
                    : "none";

        });

    }

});