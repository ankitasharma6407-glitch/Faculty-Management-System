"use strict";

/* =========================================================
   HOD PERFORMANCE DASHBOARD — REAL BACKEND DATA
========================================================= */

let allPerformanceRecords = [];
let filteredPerformanceRecords = [];
let teacherPerformanceChart = null;
let performanceDistributionChart = null;
let departmentTeachers = [];
let departmentTimetable = [];


/* =========================================================
   INITIAL LOAD
========================================================= */

document.addEventListener("DOMContentLoaded", async function () {

    if (
        typeof API === "undefined" ||
        typeof API.request !== "function"
    ) {
        showPerformanceMessage(
            "Unable to connect with backend.",
            true
        );

        return;
    }

    preparePerformancePage();
    bindPerformanceEvents();

    await Promise.all([
        loadPerformanceRecords(),
        loadEvaluationOptions()
    ]);
});


/* =========================================================
   PREPARE PAGE
========================================================= */

function preparePerformancePage() {

    setText("totalTeachers", "0");
    setText("excellentTeachers", "0");
    setText("averagePerformance", "0%");
    setText("needsImprovement", "0");

    updateModalLabels();

    showPerformanceMessage(
        "Loading performance records..."
    );
}


function updateModalLabels() {

    setMetricLabel(
        "modalAttendance",
        "Term / Semester"
    );

    setMetricLabel(
        "modalClasses",
        "Score"
    );

    setMetricLabel(
        "modalSyllabus",
        "Maximum Score"
    );

    setMetricLabel(
        "modalFeedback",
        "Grade"
    );

    setMetricLabel(
        "modalScore",
        "Percentage"
    );

    setMetricLabel(
        "modalPerformance",
        "Performance"
    );


    /*
     * Add Remarks row if it is not already present.
     */
    if (!document.getElementById("modalRemarks")) {

        const modalTable =
            document.querySelector(
                "#performanceModal .modal-body table"
            );

        if (modalTable) {

            const row =
                document.createElement("tr");

            row.innerHTML = `
                <th>Remarks</th>
                <td id="modalRemarks">--</td>
            `;

            modalTable.appendChild(row);
        }
    }
}


function setMetricLabel(elementId, label) {

    const valueElement =
        document.getElementById(elementId);

    const box =
        valueElement?.closest(
            ".performance-detail-box"
        );

    const labelElement =
        box?.querySelector("p");

    if (labelElement) {
        labelElement.textContent = label;
    }
}


/* =========================================================
   LOAD REAL PERFORMANCE DATA
========================================================= */

async function loadPerformanceRecords() {

    try {

        const urlParams =
            new URLSearchParams(
                window.location.search
            );

        const teacherId =
            urlParams.get("teacher_id");

        const queryParams = {};

        if (teacherId) {
            queryParams.teacher_id = teacherId;
        }


        const response =
            await API.request(
                "GET",
                "/hods/performance",
                null,
                queryParams
            );


        if (
            !response ||
            response.success !== true
        ) {
            throw new Error(
                response?.message ||
                "Unable to load performance records."
            );
        }


        allPerformanceRecords =
            Array.isArray(response.data)
                ? response.data
                : [];


        populateSubjectFilter();
        populateTermFilter();
        populateEvaluationTerms();

        applyPerformanceFilters();


        /*
         * When opened from Teacher List,
         * show selected teacher in page heading.
         */
        if (
            teacherId &&
            allPerformanceRecords.length > 0
        ) {
            updateSelectedTeacherHeading(
                allPerformanceRecords[0]
            );
        }
    }

    catch (error) {

        console.error(
            "Performance Load Error:",
            error
        );

        allPerformanceRecords = [];
        filteredPerformanceRecords = [];

        updatePerformanceStatistics();
        renderPerformanceTable();
        renderPerformanceCharts();
        updateTopPerformers();

        alert(
            error.message ||
            "Unable to load performance records."
        );
    }
}


function updateSelectedTeacherHeading(record) {

    const pageHeading =
        document.querySelector(
            ".page-header h2"
        );

    if (
        pageHeading &&
        record.teacher_name &&
        !pageHeading.dataset.filtered
    ) {
        pageHeading.dataset.filtered = "true";

        pageHeading.append(
            ` — ${record.teacher_name}`
        );
    }
}


/* =========================================================
   ADD EVALUATION OPTIONS
========================================================= */

async function loadEvaluationOptions() {

    try {

        const teachersResponse =
            await API.request(
                "GET",
                "/hods/teachers"
            );


        if (
            !teachersResponse ||
            teachersResponse.success !== true
        ) {
            throw new Error(
                teachersResponse?.message ||
                "Unable to load department teachers."
            );
        }


        departmentTeachers =
            Array.isArray(teachersResponse.data)
                ? teachersResponse.data
                : [];


        populateEvaluationTeachers();


        try {

            const timetableResponse =
                await API.request(
                    "GET",
                    "/hod/timetable"
                );


            departmentTimetable =
                timetableResponse?.success === true &&
                Array.isArray(timetableResponse.data)
                    ? timetableResponse.data
                    : [];
        }

        catch (timetableError) {

            console.warn(
                "Evaluation Subjects Load Error:",
                timetableError
            );

            departmentTimetable = [];
        }


        populateEvaluationSubjects();
        populateEvaluationTerms();
    }

    catch (error) {

        console.error(
            "Evaluation Options Load Error:",
            error
        );

        departmentTeachers = [];
        departmentTimetable = [];

        populateEvaluationTeachers();
        populateEvaluationSubjects();

        showEvaluationMessage(
            error.message ||
            "Unable to load evaluation form data.",
            true
        );
    }
}


function populateEvaluationTeachers() {

    const teacherSelect =
        document.getElementById(
            "evaluationTeacher"
        );

    if (!teacherSelect) {
        return;
    }


    const currentValue =
        teacherSelect.value;


    teacherSelect.innerHTML = `
        <option value="">
            Select teacher
        </option>
    `;


    departmentTeachers
        .slice()
        .sort(function (first, second) {
            return String(first.full_name || "")
                .localeCompare(
                    String(second.full_name || "")
                );
        })
        .forEach(function (teacher) {

            const option =
                document.createElement("option");

            option.value = teacher.id;
            option.textContent = [
                teacher.full_name,
                teacher.teacher_code
                    ? `(${teacher.teacher_code})`
                    : ""
            ]
                .filter(Boolean)
                .join(" ");

            teacherSelect.appendChild(option);
        });


    const teacherFromUrl =
        new URLSearchParams(
            window.location.search
        ).get("teacher_id");


    const preferredValue =
        currentValue || teacherFromUrl || "";


    if (
        preferredValue &&
        [...teacherSelect.options]
            .some(function (option) {
                return option.value ===
                    String(preferredValue);
            })
    ) {
        teacherSelect.value =
            String(preferredValue);
    }
}


function populateEvaluationSubjects() {

    const subjectSelect =
        document.getElementById(
            "evaluationSubject"
        );

    const teacherId = Number(
        document.getElementById(
            "evaluationTeacher"
        )?.value || 0
    );

    if (!subjectSelect) {
        return;
    }


    const currentValue =
        subjectSelect.value;


    const subjectMap = new Map();


    departmentTimetable
        .filter(function (entry) {
            return !teacherId ||
                Number(entry.teacher_id) === teacherId;
        })
        .forEach(function (entry) {

            if (!entry.subject_id) {
                return;
            }

            subjectMap.set(
                Number(entry.subject_id),
                {
                    id: Number(entry.subject_id),
                    name: entry.subject ||
                        "Unnamed Subject",
                    code: entry.subject_code || ""
                }
            );
        });


    subjectSelect.innerHTML = `
        <option value="">
            General evaluation (no subject)
        </option>
    `;


    [...subjectMap.values()]
        .sort(function (first, second) {
            return first.name.localeCompare(
                second.name
            );
        })
        .forEach(function (subject) {

            const option =
                document.createElement("option");

            option.value = subject.id;
            option.textContent = subject.code
                ? `${subject.name} (${subject.code})`
                : subject.name;

            subjectSelect.appendChild(option);
        });


    if (
        currentValue &&
        [...subjectSelect.options]
            .some(function (option) {
                return option.value === currentValue;
            })
    ) {
        subjectSelect.value = currentValue;
    }
}


function populateEvaluationTerms() {

    const termOptions =
        document.getElementById(
            "evaluationTermOptions"
        );

    if (!termOptions) {
        return;
    }


    const terms = new Set();


    allPerformanceRecords.forEach(
        function (record) {
            if (record.term) {
                terms.add(
                    String(record.term).trim()
                );
            }
        }
    );


    departmentTimetable.forEach(
        function (entry) {
            if (entry.semester) {
                terms.add(
                    String(entry.semester).trim()
                );
            }
        }
    );


    termOptions.innerHTML = "";


    [...terms]
        .filter(Boolean)
        .sort()
        .forEach(function (term) {

            const option =
                document.createElement("option");

            option.value = term;
            termOptions.appendChild(option);
        });
}


function updateEvaluationPreview() {

    const score = Number(
        document.getElementById(
            "evaluationScore"
        )?.value
    );

    const maxScore = Number(
        document.getElementById(
            "evaluationMaxScore"
        )?.value
    );


    const percentage =
        Number.isFinite(score) &&
        Number.isFinite(maxScore) &&
        maxScore > 0 &&
        score >= 0
            ? Math.min(
                (score / maxScore) * 100,
                999.9
            )
            : 0;


    let band = "Poor";

    if (percentage >= 80) {
        band = "Excellent";
    }
    else if (percentage >= 60) {
        band = "Good";
    }
    else if (percentage >= 40) {
        band = "Average";
    }


    setText(
        "evaluationPercentage",
        `${percentage.toFixed(1)}%`
    );

    setText(
        "evaluationBand",
        band
    );
}


async function submitEvaluation(event) {

    event.preventDefault();


    const form = event.currentTarget;

    clearEvaluationMessage();


    if (!form.checkValidity()) {
        form.classList.add("was-validated");
        form.reportValidity();
        return;
    }


    const teacherId = Number(
        document.getElementById(
            "evaluationTeacher"
        ).value
    );

    const subjectValue =
        document.getElementById(
            "evaluationSubject"
        ).value;

    const term =
        document.getElementById(
            "evaluationTerm"
        ).value.trim();

    const score = Number(
        document.getElementById(
            "evaluationScore"
        ).value
    );

    const maxScore = Number(
        document.getElementById(
            "evaluationMaxScore"
        ).value
    );


    if (score > maxScore) {
        showEvaluationMessage(
            "Score cannot be greater than maximum score.",
            true
        );
        return;
    }


    const payload = {
        teacher_id: teacherId,
        subject_id: subjectValue
            ? Number(subjectValue)
            : null,
        term: term,
        score: score,
        max_score: maxScore,
        grade:
            document.getElementById(
                "evaluationGrade"
            ).value.trim() || null,
        remarks:
            document.getElementById(
                "evaluationRemarks"
            ).value.trim() || null
    };


    setEvaluationSaving(true);


    try {

        const response =
            await API.request(
                "POST",
                "/hods/performance",
                payload
            );


        if (
            !response ||
            response.success !== true
        ) {
            throw new Error(
                response?.message ||
                "Unable to save teacher evaluation."
            );
        }


        resetEvaluationForm();


        const modalElement =
            document.getElementById(
                "addEvaluationModal"
            );

        if (
            modalElement &&
            typeof bootstrap !== "undefined"
        ) {
            bootstrap.Modal
                .getOrCreateInstance(modalElement)
                .hide();
        }


        await loadPerformanceRecords();


        alert(
            response.message ||
            "Teacher evaluation saved successfully."
        );
    }

    catch (error) {

        console.error(
            "Evaluation Save Error:",
            error
        );

        showEvaluationMessage(
            error.message ||
            "Unable to save teacher evaluation.",
            true
        );
    }

    finally {
        setEvaluationSaving(false);
    }
}


function setEvaluationSaving(isSaving) {

    const saveButton =
        document.getElementById(
            "saveEvaluationBtn"
        );

    const spinner =
        document.getElementById(
            "saveEvaluationSpinner"
        );

    const icon =
        document.getElementById(
            "saveEvaluationIcon"
        );

    const text =
        document.getElementById(
            "saveEvaluationText"
        );


    if (saveButton) {
        saveButton.disabled = isSaving;
    }

    spinner?.classList.toggle(
        "d-none",
        !isSaving
    );

    icon?.classList.toggle(
        "d-none",
        isSaving
    );

    if (text) {
        text.textContent = isSaving
            ? "Saving..."
            : "Save Evaluation";
    }
}


function showEvaluationMessage(message, isError) {

    const messageBox =
        document.getElementById(
            "evaluationFormMessage"
        );

    if (!messageBox) {
        return;
    }


    messageBox.textContent = message;
    messageBox.className =
        `alert ${isError
            ? "alert-danger"
            : "alert-success"}`;
}


function clearEvaluationMessage() {

    const messageBox =
        document.getElementById(
            "evaluationFormMessage"
        );

    if (!messageBox) {
        return;
    }


    messageBox.textContent = "";
    messageBox.className = "alert d-none";
}


function resetEvaluationForm() {

    const form =
        document.getElementById(
            "evaluationForm"
        );

    form?.reset();
    form?.classList.remove("was-validated");


    const maxScore =
        document.getElementById(
            "evaluationMaxScore"
        );

    if (maxScore) {
        maxScore.value = "100";
    }


    clearEvaluationMessage();
    populateEvaluationTeachers();
    populateEvaluationSubjects();
    updateEvaluationPreview();
}


/* =========================================================
   DYNAMIC FILTER OPTIONS
========================================================= */

function populateSubjectFilter() {

    const subjectFilter =
        document.getElementById(
            "subjectFilter"
        );

    if (!subjectFilter) {
        return;
    }


    const subjects =
        [
            ...new Set(
                allPerformanceRecords
                    .map(function (record) {
                        return record.subject;
                    })
                    .filter(Boolean)
            )
        ].sort();


    subjectFilter.innerHTML = `
        <option value="">
            All Subjects
        </option>
    `;


    subjects.forEach(function (subject) {

        const option =
            document.createElement("option");

        option.value = subject;
        option.textContent = subject;

        subjectFilter.appendChild(option);
    });
}


function populateTermFilter() {

    const termFilter =
        document.getElementById(
            "termFilter"
        );

    if (!termFilter) {
        return;
    }


    const terms =
        [
            ...new Set(
                allPerformanceRecords
                    .map(function (record) {
                        return record.term;
                    })
                    .filter(Boolean)
            )
        ].sort();


    termFilter.innerHTML = `
        <option value="">
            All Terms
        </option>
    `;


    terms.forEach(function (term) {

        const option =
            document.createElement("option");

        option.value = term;
        option.textContent = term;

        termFilter.appendChild(option);
    });
}


/* =========================================================
   FILTER EVENTS
========================================================= */

function bindPerformanceEvents() {

    const teacherSearch =
        document.getElementById(
            "teacherSearch"
        );

    const applyButton =
        document.getElementById(
            "applyFilterBtn"
        );

    const resetButton =
        document.getElementById(
            "resetFilterBtn"
        );

    const tableBody =
        document.getElementById(
            "performanceTableBody"
        );

    const evaluationForm =
        document.getElementById(
            "evaluationForm"
        );

    const evaluationTeacher =
        document.getElementById(
            "evaluationTeacher"
        );

    const evaluationScore =
        document.getElementById(
            "evaluationScore"
        );

    const evaluationMaxScore =
        document.getElementById(
            "evaluationMaxScore"
        );

    const evaluationModal =
        document.getElementById(
            "addEvaluationModal"
        );


    teacherSearch?.addEventListener(
        "input",
        applyPerformanceFilters
    );


    applyButton?.addEventListener(
        "click",
        applyPerformanceFilters
    );


    resetButton?.addEventListener(
        "click",
        resetPerformanceFilters
    );


    evaluationForm?.addEventListener(
        "submit",
        submitEvaluation
    );


    evaluationTeacher?.addEventListener(
        "change",
        populateEvaluationSubjects
    );


    evaluationScore?.addEventListener(
        "input",
        updateEvaluationPreview
    );


    evaluationMaxScore?.addEventListener(
        "input",
        updateEvaluationPreview
    );


    evaluationModal?.addEventListener(
        "show.bs.modal",
        function () {
            clearEvaluationMessage();
            populateEvaluationTeachers();
            populateEvaluationSubjects();
            populateEvaluationTerms();
            updateEvaluationPreview();
        }
    );


    tableBody?.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    ".view-performance"
                );

            if (!button) {
                return;
            }

            const recordId =
                Number(button.dataset.recordId);

            viewPerformanceRecord(recordId);
        }
    );


    document
        .getElementById("excelBtn")
        ?.addEventListener(
            "click",
            exportPerformanceExcel
        );


    document
        .getElementById("pdfBtn")
        ?.addEventListener(
            "click",
            exportPerformancePdf
        );


    document
        .getElementById("printBtn")
        ?.addEventListener(
            "click",
            printPerformanceTable
        );
}


function resetPerformanceFilters() {

    const teacherSearch =
        document.getElementById(
            "teacherSearch"
        );

    const subjectFilter =
        document.getElementById(
            "subjectFilter"
        );

    const performanceFilter =
        document.getElementById(
            "performanceFilter"
        );

    const termFilter =
        document.getElementById(
            "termFilter"
        );


    if (teacherSearch) {
        teacherSearch.value = "";
    }

    if (subjectFilter) {
        subjectFilter.value = "";
    }

    if (performanceFilter) {
        performanceFilter.value = "";
    }

    if (termFilter) {
        termFilter.value = "";
    }


    applyPerformanceFilters();
}


/* =========================================================
   APPLY FILTERS
========================================================= */

function applyPerformanceFilters() {

    const searchValue =
        String(
            document.getElementById(
                "teacherSearch"
            )?.value || ""
        )
            .trim()
            .toLowerCase();


    const subjectValue =
        String(
            document.getElementById(
                "subjectFilter"
            )?.value || ""
        )
            .trim()
            .toLowerCase();


    const performanceValue =
        String(
            document.getElementById(
                "performanceFilter"
            )?.value || ""
        )
            .trim()
            .toLowerCase();


    const termValue =
        String(
            document.getElementById(
                "termFilter"
            )?.value || ""
        )
            .trim()
            .toLowerCase();


    filteredPerformanceRecords =
        allPerformanceRecords.filter(
            function (record) {

                const searchableText =
                    [
                        record.teacher_code,
                        record.teacher_name,
                        record.subject,
                        record.term,
                        record.grade,
                        record.remarks
                    ]
                        .filter(Boolean)
                        .join(" ")
                        .toLowerCase();


                const searchMatch =
                    !searchValue ||
                    searchableText.includes(
                        searchValue
                    );


                const subjectMatch =
                    !subjectValue ||
                    String(
                        record.subject || ""
                    ).toLowerCase() ===
                    subjectValue;


                const performanceMatch =
                    !performanceValue ||
                    String(
                        record.band || ""
                    ).toLowerCase() ===
                    performanceValue;


                const termMatch =
                    !termValue ||
                    String(
                        record.term || ""
                    ).toLowerCase() ===
                    termValue;


                return (
                    searchMatch &&
                    subjectMatch &&
                    performanceMatch &&
                    termMatch
                );
            }
        );


    updatePerformanceStatistics();
    renderPerformanceTable();
    renderPerformanceCharts();
    updateTopPerformers();
}


/* =========================================================
   STATISTICS
========================================================= */

function updatePerformanceStatistics() {

    const uniqueTeacherIds =
        new Set(
            filteredPerformanceRecords
                .map(function (record) {
                    return record.teacher_id;
                })
                .filter(Boolean)
        );


    const excellentCount =
        filteredPerformanceRecords.filter(
            function (record) {
                return record.band === "Excellent";
            }
        ).length;


    const needsImprovementCount =
        filteredPerformanceRecords.filter(
            function (record) {
                return (
                    record.band === "Average" ||
                    record.band === "Poor"
                );
            }
        ).length;


    const totalPercentage =
        filteredPerformanceRecords.reduce(
            function (sum, record) {

                return (
                    sum +
                    Number(
                        record.percentage || 0
                    )
                );
            },
            0
        );


    const averagePercentage =
        filteredPerformanceRecords.length
            ? (
                totalPercentage /
                filteredPerformanceRecords.length
            ).toFixed(1)
            : "0.0";


    setText(
        "totalTeachers",
        String(uniqueTeacherIds.size)
    );

    setText(
        "excellentTeachers",
        String(excellentCount)
    );

    setText(
        "averagePerformance",
        `${averagePercentage}%`
    );

    setText(
        "needsImprovement",
        String(needsImprovementCount)
    );
}


/* =========================================================
   TABLE
========================================================= */

function renderPerformanceTable() {

    const tableBody =
        document.getElementById(
            "performanceTableBody"
        );

    if (!tableBody) {
        return;
    }


    if (
        filteredPerformanceRecords.length === 0
    ) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="10"
                    class="text-center text-muted py-4">

                    No performance records found.

                </td>
            </tr>
        `;

        return;
    }


    tableBody.innerHTML =
        filteredPerformanceRecords
            .map(function (record) {

                return `
                    <tr>
                        <td>
                            ${escapeHtml(
                                record.teacher_code || "-"
                            )}
                        </td>

                        <td class="text-start">
                            <i class="fa-solid fa-user-tie me-2 text-primary"></i>

                            ${escapeHtml(
                                record.teacher_name || "-"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                record.subject || "-"
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                record.term || "-"
                            )}
                        </td>

                        <td>
                            ${formatNumber(
                                record.score
                            )}
                        </td>

                        <td>
                            ${formatNumber(
                                record.max_score
                            )}
                        </td>

                        <td>
                            ${escapeHtml(
                                record.grade || "-"
                            )}
                        </td>

                        <td>
                            ${getPerformanceBadge(
                                record.band
                            )}
                        </td>

                        <td class="text-start">
                            ${escapeHtml(
                                record.remarks || "-"
                            )}
                        </td>

                        <td>
                            <button
                                type="button"
                                class="btn btn-info btn-sm text-white view-performance"
                                data-record-id="${Number(
                                    record.id
                                )}"
                                title="View Performance">

                                <i class="fa-solid fa-eye"></i>

                            </button>
                        </td>
                    </tr>
                `;
            })
            .join("");
}


function showPerformanceMessage(
    message,
    isError = false
) {

    const tableBody =
        document.getElementById(
            "performanceTableBody"
        );

    if (!tableBody) {
        return;
    }


    tableBody.innerHTML = `
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


function getPerformanceBadge(band) {

    const value =
        String(band || "Poor");


    let badgeClass = "bg-danger";


    if (value === "Excellent") {
        badgeClass = "bg-success";
    }

    else if (value === "Good") {
        badgeClass = "bg-primary";
    }

    else if (value === "Average") {
        badgeClass = "bg-warning text-dark";
    }


    return `
        <span class="badge ${badgeClass}">
            ${escapeHtml(value)}
        </span>
    `;
}


/* =========================================================
   VIEW MODAL
========================================================= */

function viewPerformanceRecord(recordId) {

    const record =
        allPerformanceRecords.find(
            function (item) {

                return (
                    Number(item.id) ===
                    Number(recordId)
                );
            }
        );


    if (!record) {

        alert(
            "Performance record not found."
        );

        return;
    }


    setText(
        "modalTeacherName",
        record.teacher_name || "-"
    );

    setText(
        "modalTeacherSubject",
        record.subject || "No subject"
    );

    setText(
        "modalAttendance",
        record.term || "-"
    );

    setText(
        "modalClasses",
        formatNumber(record.score)
    );

    setText(
        "modalSyllabus",
        formatNumber(record.max_score)
    );

    setText(
        "modalFeedback",
        record.grade || "-"
    );

    setText(
        "modalScore",
        `${formatNumber(record.percentage)}%`
    );

    setText(
        "modalPerformance",
        record.band || "-"
    );

    setText(
        "modalTeacherId",
        record.teacher_code || "-"
    );

    setText(
        "modalName",
        record.teacher_name || "-"
    );

    setText(
        "modalSubject",
        record.subject || "-"
    );

    setText(
        "modalRemarks",
        record.remarks || "-"
    );


    const modalElement =
        document.getElementById(
            "performanceModal"
        );


    if (
        modalElement &&
        typeof bootstrap !== "undefined"
    ) {

        bootstrap.Modal
            .getOrCreateInstance(
                modalElement
            )
            .show();
    }
}


/* =========================================================
   CHARTS
========================================================= */

function renderPerformanceCharts() {

    renderTeacherComparisonChart();
    renderDistributionChart();
}


function renderTeacherComparisonChart() {

    const canvas =
        document.getElementById(
            "teacherPerformanceChart"
        );

    if (!canvas || typeof Chart === "undefined") {
        return;
    }


    if (teacherPerformanceChart) {
        teacherPerformanceChart.destroy();
    }


    teacherPerformanceChart =
        new Chart(canvas, {

            type: "bar",

            data: {

                labels:
                    filteredPerformanceRecords
                        .map(function (record) {

                            return (
                                record.teacher_code ||
                                record.teacher_name ||
                                "-"
                            );
                        }),

                datasets: [{

                    label:
                        "Performance Percentage",

                    data:
                        filteredPerformanceRecords
                            .map(function (record) {

                                return Number(
                                    record.percentage || 0
                                );
                            }),

                    backgroundColor:
                        "#6c4cff",

                    borderRadius: 7

                }]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                scales: {

                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
}


function renderDistributionChart() {

    const canvas =
        document.getElementById(
            "performanceDistributionChart"
        );

    if (!canvas || typeof Chart === "undefined") {
        return;
    }


    if (performanceDistributionChart) {
        performanceDistributionChart.destroy();
    }


    const counts = {
        Excellent: 0,
        Good: 0,
        Average: 0,
        Poor: 0
    };


    filteredPerformanceRecords.forEach(
        function (record) {

            const band =
                record.band || "Poor";

            if (
                Object.prototype.hasOwnProperty
                    .call(counts, band)
            ) {
                counts[band]++;
            }
        }
    );


    performanceDistributionChart =
        new Chart(canvas, {

            type: "doughnut",

            data: {

                labels:
                    Object.keys(counts),

                datasets: [{

                    data:
                        Object.values(counts),

                    backgroundColor: [
                        "#198754",
                        "#0d6efd",
                        "#ffc107",
                        "#dc3545"
                    ]
                }]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false

            }
        });
}


/* =========================================================
   TOP PERFORMERS
========================================================= */

function updateTopPerformers() {

    const sections =
        Array.from(
            document.querySelectorAll(
                ".performance-page-card"
            )
        );


    const topSection =
        sections.find(
            function (section) {

                const heading =
                    section.querySelector("h4");

                return (
                    heading &&
                    heading.textContent
                        .toLowerCase()
                        .includes("top performers")
                );
            }
        );


    if (!topSection) {
        return;
    }


    const cards =
        topSection.querySelectorAll(
            ".performance-detail-box"
        );


    const sortedRecords =
        [...filteredPerformanceRecords]
            .sort(function (first, second) {

                return (
                    Number(
                        second.percentage || 0
                    ) -
                    Number(
                        first.percentage || 0
                    )
                );
            })
            .slice(0, 3);


    cards.forEach(
        function (card, index) {

            const nameElement =
                card.querySelector("h4");

            const detailElement =
                card.querySelector("p");

            const record =
                sortedRecords[index];


            if (!record) {

                if (nameElement) {
                    nameElement.textContent =
                        "No Data";
                }

                if (detailElement) {
                    detailElement.textContent =
                        "--";
                }

                return;
            }


            if (nameElement) {

                nameElement.textContent =
                    record.teacher_name || "-";
            }


            if (detailElement) {

                detailElement.textContent =
                    `${formatNumber(
                        record.percentage
                    )}% • ${
                        record.subject ||
                        record.term ||
                        "Performance"
                    }`;
            }
        }
    );
}


/* =========================================================
   EXCEL EXPORT
========================================================= */

function exportPerformanceExcel() {

    if (
        filteredPerformanceRecords.length === 0
    ) {

        alert(
            "No performance data available to export."
        );

        return;
    }


    if (typeof XLSX === "undefined") {

        alert(
            "Excel library is not available."
        );

        return;
    }


    const rows =
        filteredPerformanceRecords.map(
            function (record) {

                return {

                    "Teacher ID":
                        record.teacher_code || "",

                    "Teacher Name":
                        record.teacher_name || "",

                    "Subject":
                        record.subject || "",

                    "Term":
                        record.term || "",

                    "Score":
                        record.score ?? "",

                    "Maximum Score":
                        record.max_score ?? "",

                    "Percentage":
                        record.percentage ?? "",

                    "Grade":
                        record.grade || "",

                    "Performance":
                        record.band || "",

                    "Remarks":
                        record.remarks || ""
                };
            }
        );


    const worksheet =
        XLSX.utils.json_to_sheet(rows);

    const workbook =
        XLSX.utils.book_new();


    XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        "Performance"
    );


    XLSX.writeFile(
        workbook,
        "hod-performance-report.xlsx"
    );
}


/* =========================================================
   PDF EXPORT
========================================================= */

function exportPerformancePdf() {

    if (
        filteredPerformanceRecords.length === 0
    ) {

        alert(
            "No performance data available to export."
        );

        return;
    }


    if (
        !window.jspdf ||
        !window.jspdf.jsPDF
    ) {

        alert(
            "PDF library is not available."
        );

        return;
    }


    const documentPdf =
        new window.jspdf.jsPDF({
            orientation: "landscape"
        });


    documentPdf.setFontSize(16);

    documentPdf.text(
        "HOD Performance Report",
        14,
        15
    );


    const rows =
        filteredPerformanceRecords.map(
            function (record) {

                return [

                    record.teacher_code || "-",

                    record.teacher_name || "-",

                    record.subject || "-",

                    record.term || "-",

                    formatNumber(record.score),

                    formatNumber(record.max_score),

                    `${formatNumber(
                        record.percentage
                    )}%`,

                    record.grade || "-",

                    record.band || "-",

                    record.remarks || "-"

                ];
            }
        );


    documentPdf.autoTable({

        startY: 22,

        head: [[
            "Teacher ID",
            "Teacher",
            "Subject",
            "Term",
            "Score",
            "Max",
            "%",
            "Grade",
            "Performance",
            "Remarks"
        ]],

        body: rows,

        styles: {
            fontSize: 8
        }
    });


    documentPdf.save(
        "hod-performance-report.pdf"
    );
}


/* =========================================================
   PRINT
========================================================= */

function printPerformanceTable() {

    if (
        filteredPerformanceRecords.length === 0
    ) {

        alert(
            "No performance data available to print."
        );

        return;
    }


    const table =
        document.getElementById(
            "performanceTable"
        );


    if (!table) {
        return;
    }


    const tableCopy =
        table.cloneNode(true);


    tableCopy
        .querySelectorAll("tr")
        .forEach(function (row) {

            row.lastElementChild?.remove();
        });


    const printWindow =
        window.open(
            "",
            "_blank",
            "width=1200,height=700"
        );


    if (!printWindow) {

        alert(
            "Please allow pop-ups to print."
        );

        return;
    }


    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>HOD Performance Report</title>

            <style>
                body {
                    font-family: Arial, sans-serif;
                    padding: 25px;
                }

                h2 {
                    text-align: center;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                }

                th,
                td {
                    border: 1px solid #333;
                    padding: 8px;
                    text-align: left;
                }

                th {
                    background: #eeeeee;
                }
            </style>
        </head>

        <body>

            <h2>HOD Performance Report</h2>

            ${tableCopy.outerHTML}

        </body>
        </html>
    `);


    printWindow.document.close();

    printWindow.focus();

    printWindow.print();
}


/* =========================================================
   HELPERS
========================================================= */

function setText(elementId, value) {

    const element =
        document.getElementById(elementId);

    if (element) {
        element.textContent = value;
    }
}


function formatNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }


    const numberValue =
        Number(value);


    if (Number.isNaN(numberValue)) {
        return String(value);
    }


    return Number.isInteger(numberValue)
        ? String(numberValue)
        : numberValue.toFixed(1);
}


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

