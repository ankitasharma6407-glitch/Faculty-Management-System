// ==========================================
// Add Teacher - API Integration
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    const teacherForm = document.getElementById("teacherForm");

    if (!teacherForm) {
        return;
    }

    teacherForm.addEventListener("submit", async function (e) {

        e.preventDefault();

        // ==========================================
        // Password Validation
        // ==========================================

        const password =
            document.getElementById("password").value;

        const confirmPassword =
            document.getElementById("confirmPassword").value;

        if (password !== confirmPassword) {

            alert("Passwords do not match.");

            return;
        }


        // ==========================================
        // Create FormData
        // ==========================================

        const formData = new FormData();

        formData.append(
            "teacherId",
            document.getElementById("teacherId").value.trim()
        );

        formData.append(
            "teacherName",
            document.getElementById("teacherName").value.trim()
        );

        formData.append(
            "teacherEmail",
            document.getElementById("teacherEmail").value.trim()
        );

        formData.append(
            "teacherPhone",
            document.getElementById("teacherPhone").value.trim()
        );

        formData.append(
            "teacherGender",
            document.getElementById("teacherGender").value
        );

        formData.append(
            "teacherDob",
            document.getElementById("teacherDob").value
        );

        formData.append(
            "bloodGroup",
            document.getElementById("bloodGroup").value
        );

        formData.append(
            "teacherDepartment",
            document.getElementById("teacherDepartment").value
        );

        formData.append(
            "teacherDesignation",
            document.getElementById("teacherDesignation").value
        );

        formData.append(
            "teacherQualification",
            document.getElementById("teacherQualification").value.trim()
        );

        formData.append(
            "teacherExperience",
            document.getElementById("teacherExperience").value
        );

        formData.append(
            "joiningDate",
            document.getElementById("joiningDate").value
        );

        formData.append(
            "teacherSalary",
            document.getElementById("teacherSalary").value
        );

        formData.append(
            "teacherAddress",
            document.getElementById("teacherAddress").value.trim()
        );

        formData.append(
            "username",
            document.getElementById("username").value.trim()
        );

        formData.append(
            "password",
            password
        );

        formData.append(
            "teacherStatus",
            document.getElementById("teacherStatus").value
        );


        // ==========================================
        // Profile Photo
        // ==========================================

        const photoInput =
            document.getElementById("teacherPhoto");

        if (photoInput && photoInput.files.length > 0) {

            formData.append(
                "teacherPhoto",
                photoInput.files[0]
            );

        }


        // ==========================================
        // Send Data to Flask Backend
        // ==========================================

        try {

            const response = await fetch(
                "http://127.0.0.1:5000/api/admin/teachers",
                {
                    method: "POST",
                    body: formData
                }
            );


            const data = await response.json();

            console.log(
                "Teacher API Response:",
                data
            );


            // ==========================================
            // Success
            // ==========================================

            if (response.ok && data.success) {

                alert(
                    "Teacher added successfully!"
                );

                teacherForm.reset();

                window.location.href =
                    "teacher-list.html";

            } else {

                alert(
                    data.message ||
                    "Failed to add teacher."
                );

            }

        } catch (error) {

            console.error(
                "Add Teacher Error:",
                error
            );

            alert(
                "Unable to connect to the backend. " +
                "Please make sure Flask server is running."
            );

        }

    });

});