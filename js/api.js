// ==========================================
// FMPS API CLIENT
// Faculty Management & Productivity System
// ==========================================

(function (global) {

    const BASE_URL = "http://127.0.0.1:5000/api";

    const TOKEN_KEY = "fmps_access_token";
    const USER_KEY = "fmps_user";


    // ==========================================
    // Local Storage
    // ==========================================

    const store = {

        get token() {
            return localStorage.getItem(TOKEN_KEY);
        },

        set token(value) {

            if (value) {
                localStorage.setItem(TOKEN_KEY, value);
            } else {
                localStorage.removeItem(TOKEN_KEY);
            }

        },


        get user() {

            try {

                return JSON.parse(
                    localStorage.getItem(USER_KEY)
                );

            } catch (error) {

                return null;

            }

        },


        set user(value) {

            if (value) {

                localStorage.setItem(
                    USER_KEY,
                    JSON.stringify(value)
                );

            } else {

                localStorage.removeItem(USER_KEY);

            }

        }

    };


    // ==========================================
    // Query Parameters
    // ==========================================

    function queryString(params) {

        if (!params) {
            return "";
        }

        const entries = Object.entries(params)
            .filter(function ([key, value]) {

                return value !== undefined &&
                       value !== null &&
                       value !== "";

            });

        if (entries.length === 0) {
            return "";
        }

        return "?" + new URLSearchParams(entries).toString();

    }


    // ==========================================
    // Main API Request
    // ==========================================

    async function request(method, path, body, params) {

        const headers = {
            "Accept": "application/json"
        };


        // ======================================
        // JSON Body
        // ======================================

        if (
            body &&
            !(body instanceof FormData)
        ) {

            headers["Content-Type"] =
                "application/json";

        }


        // ======================================
        // JWT Token
        // ======================================

        if (store.token) {

            headers["Authorization"] =
                "Bearer " + store.token;

        }


        const response = await fetch(

            BASE_URL +
            path +
            queryString(params),

            {

                method: method,

                headers: headers,

                body:
                    body instanceof FormData
                        ? body
                        : body
                            ? JSON.stringify(body)
                            : undefined

            }

        );


        const data =
            await response
                .json()
                .catch(function () {
                    return {};
                });


        // ======================================
        // Error Handling
        // ======================================

        if (!response.ok) {

            if (response.status === 401) {

                store.token = null;
                store.user = null;

            }


            const error =
                new Error(
                    data.message ||
                    "Request failed"
                );

            error.status =
                response.status;

            error.errors =
                data.errors;

            throw error;

        }


        return data;

    }


    // ==========================================
    // HTTP Methods
    // ==========================================

    function get(path, params) {

        return request(
            "GET",
            path,
            null,
            params
        );

    }


    function post(path, body) {

        return request(
            "POST",
            path,
            body
        );

    }


    function put(path, body) {

        return request(
            "PUT",
            path,
            body
        );

    }


    function patch(path, body) {

        return request(
            "PATCH",
            path,
            body
        );

    }


    function del(path) {

        return request(
            "DELETE",
            path
        );

    }


    // ==========================================
    // API
    // ==========================================

    const API = {

        baseUrl: BASE_URL,

        store: store,

        request: request,


        // ======================================
        // Admin
        // ======================================

        admin: {

            dashboard() {

                return get(
                    "/admin/dashboard"
                );

            }

        },


        // ======================================
        // Authentication
        // ======================================

        auth: {

            async login(credentials) {

                const response =
                    await post(
                        "/auth/login",
                        credentials
                    );


                store.token =
                    response.data.access_token;


                store.user =
                    response.data.user;


                return response.data;

            },


            me() {

                return get(
                    "/auth/me"
                );

            },


            updateProfile(data) {

                return put(
                    "/auth/me",
                    data
                );

            },


            changePassword(data) {

                return post(
                    "/auth/change-password",
                    data
                );

            },


            forgotPassword(email) {

                return post(
                    "/auth/forgot-password",
                    {
                        email: email
                    }
                );

            },


            resetPassword(data) {

                return post(
                    "/auth/reset-password",
                    data
                );

            },


            logout() {

                store.token = null;
                store.user = null;

            }

        },


        // ======================================
        // Health Check
        // ======================================

        health() {

            return get(
                "/health"
            );

        },


        // ======================================
        // Users
        // ======================================

        users: {

            list(params) {

                return get(
                    "/admin/users",
                    params
                );

            },


            updateStatus(id, data) {

                return patch(
                    "/admin/users/" +
                    id +
                    "/status",
                    data
                );

            },


            resetPassword(id, data) {

                return post(
                    "/admin/users/" +
                    id +
                    "/reset-password",
                    data
                );

            },


            remove(id) {

                return del(
                    "/admin/users/" +
                    id
                );

            }

        },


        // ======================================
        // Departments
        // ======================================

        departments: {

            list(params) {

                return get(
                    "/departments",
                    params
                );

            },


            get(id) {

                return get(
                    "/departments/" + id
                );

            },


            create(data) {

                return post(
                    "/departments",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/departments/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/departments/" +
                    id
                );

            }

        },


        // ======================================
        // Teachers
        // ======================================

        teachers: {

            list(params) {

                return get(
                    "/teachers",
                    params
                );

            },


            get(id) {

                return get(
                    "/teachers/" + id
                );

            },


            create(data) {

                return post(
                    "/teachers",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/teachers/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/teachers/" +
                    id
                );

            }

        },


        // ======================================
        // HODs
        // ======================================

        hods: {

            list(params) {

                return get(
                    "/hods",
                    params
                );

            },


            get(id) {

                return get(
                    "/hods/" + id
                );

            },


            create(data) {

                return post(
                    "/hods",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/hods/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/hods/" +
                    id
                );

            }

        },


        // ======================================
        // Students
        // ======================================

        students: {

            list(params) {

                return get(
                    "/students",
                    params
                );

            },


            get(id) {

                return get(
                    "/students/" + id
                );

            },


            create(data) {

                return post(
                    "/students",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/students/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/students/" +
                    id
                );

            }

        },


        // ======================================
        // Recruiters
        // ======================================

        recruiters: {

            list(params) {

                return get(
                    "/recruiters",
                    params
                );

            },


            get(id) {

                return get(
                    "/recruiters/" + id
                );

            },


            create(data) {

                return post(
                    "/recruiters",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/recruiters/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/recruiters/" +
                    id
                );

            }

        },


        // ======================================
        // Attendance
        // ======================================

        attendance: {

            list(params) {

                return get(
                    "/attendance",
                    params
                );

            },


            create(data) {

                return post(
                    "/attendance",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/attendance/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/attendance/" +
                    id
                );

            }

        },


        // ======================================
        // Calendar
        // ======================================

        calendar: {

            list(params) {

                return get(
                    "/calendar",
                    params
                );

            },


            create(data) {

                return post(
                    "/calendar",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/calendar/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/calendar/" +
                    id
                );

            }

        },


        // ======================================
        // Performance
        // ======================================

        performance: {

            list(params) {

                return get(
                    "/performance",
                    params
                );

            },


            mine(params) {

                return get(
                    "/performance/me",
                    params
                );

            },


            create(data) {

                return post(
                    "/performance",
                    data
                );

            },


            update(id, data) {

                return put(
                    "/performance/" +
                    id,
                    data
                );

            },


            remove(id) {

                return del(
                    "/performance/" +
                    id
                );

            },


            summary(userId) {

                return get(
                    "/performance/summary/" +
                    userId
                );

            }

        },


        // ======================================
        // Reports
        // ======================================

        reports: {

            dashboard() {

                return get(
                    "/reports/dashboard"
                );

            },


            attendanceTrend(days) {

                return get(
                    "/reports/attendance-trend",
                    {
                        days: days
                    }
                );

            },


            departmentStats() {

                return get(
                    "/reports/department-stats"
                );

            }

        },


        // ======================================
        // Face Recognition
        // ======================================

        face: {

            register(data) {

                return post(
                    "/face/register",
                    data
                );

            },


            login(data) {

                return post(
                    "/face/login",
                    data
                );

            },


            uploadPhoto(file) {

                const formData =
                    new FormData();


                formData.append(
                    "file",
                    file
                );


                return post(
                    "/face/upload-photo",
                    formData
                );

            }

        }

    };


    // ==========================================
    // Make API Globally Available
    // ==========================================

    global.API = API;


})(window);