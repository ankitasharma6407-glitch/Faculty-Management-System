// ==========================================
// FMPS API CLIENT
// Faculty Management & Productivity System
// ==========================================

(function (global) {

    const BASE_URL = "http://127.0.0.1:5000/api";

    const TOKEN_KEY = "fmps_access_token";
    const REFRESH_TOKEN_KEY = "fmps_refresh_token";
    const USER_KEY = "fmps_user";
    let refreshPromise = null;


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

        get refreshToken() {
            return localStorage.getItem(REFRESH_TOKEN_KEY);
        },

        set refreshToken(value) {
            if (value) {
                localStorage.setItem(REFRESH_TOKEN_KEY, value);
            } else {
                localStorage.removeItem(REFRESH_TOKEN_KEY);
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
    // JWT Expiry Helpers
    // ==========================================

    function decodeJwtPayload(token) {

        if (!token || typeof token !== "string") {
            return null;
        }

        try {
            const payload = token.split(".")[1];

            if (!payload) {
                return null;
            }

            const normalized = payload
                .replace(/-/g, "+")
                .replace(/_/g, "/");

            const padded = normalized.padEnd(
                Math.ceil(normalized.length / 4) * 4,
                "="
            );

            return JSON.parse(atob(padded));
        }
        catch (error) {
            return null;
        }
    }


    function tokenExpiresSoon(token, secondsBeforeExpiry) {

        const payload = decodeJwtPayload(token);

        if (!payload || !payload.exp) {
            return false;
        }

        const expiryTime = Number(payload.exp) * 1000;
        const safetyWindow = Number(secondsBeforeExpiry || 120) * 1000;

        return expiryTime - Date.now() <= safetyWindow;
    }


    function isTerminalRefreshError(error) {

        return Boolean(
            error &&
            (error.status === 401 || error.status === 422)
        );
    }


    // ==========================================
    // Main API Request
    // ==========================================

    async function request(method, path, body, params, skipRefresh) {

        /*
         * Refresh shortly before expiry so an actively used page does not
         * have to fail with 401 first. A temporary network/server problem
         * must not erase a still-valid local session.
         */
        if (
            !skipRefresh &&
            path !== "/auth/refresh" &&
            store.token &&
            store.refreshToken &&
            tokenExpiresSoon(store.token, 120)
        ) {
            try {
                await refreshAccessToken();
            }
            catch (refreshError) {
                console.warn(
                    "Proactive session refresh failed:",
                    refreshError.message
                );

                if (isTerminalRefreshError(refreshError)) {
                    clearSession();
                    throw refreshError;
                }
            }
        }

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

            if (response.status === 401 && !skipRefresh && store.refreshToken) {
                try {
                    await refreshAccessToken();
                    return request(method, path, body, params, true);
                } catch (refreshError) {
                    console.warn("Session refresh failed:", refreshError.message);

                    if (isTerminalRefreshError(refreshError)) {
                        clearSession();
                    }

                    /*
                     * A refresh-network failure is not proof that the refresh
                     * token expired. Preserve the tokens and expose the real
                     * temporary error to the page instead of logging out.
                     */
                    throw refreshError;
                }
            }

            if (response.status === 401) {
                clearSession();
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

    async function refreshAccessToken() {
        if (refreshPromise) {
            return refreshPromise;
        }

        refreshPromise = refreshAccessTokenOnce();

        try {
            return await refreshPromise;
        } finally {
            refreshPromise = null;
        }
    }

    async function refreshAccessTokenOnce() {
        const refreshToken = store.refreshToken;

        if (!refreshToken) {
            throw new Error("Refresh token not found");
        }

        const response = await fetch(
            BASE_URL + "/auth/refresh",
            {
                method: "POST",
                headers: {
                    "Accept": "application/json",
                    "Authorization": "Bearer " + refreshToken
                }
            }
        );

        const data = await response.json().catch(function () {
            return {};
        });

        if (!response.ok || !data?.data?.access_token) {
            const error = new Error(
                data.message || "Refresh token expired"
            );

            error.status = response.status;
            error.isRefreshError = true;

            throw error;
        }

        store.token = data.data.access_token;
        return data.data.access_token;
    }

    function clearSession() {
        store.token = null;
        store.refreshToken = null;
        store.user = null;
    }

    function keepSessionAlive() {

        if (
            !store.token ||
            !store.refreshToken ||
            !tokenExpiresSoon(store.token, 120)
        ) {
            return;
        }

        refreshAccessToken().catch(function (error) {
            console.warn(
                "Background session refresh failed:",
                error.message
            );

            if (isTerminalRefreshError(error)) {
                clearSession();
            }
        });
    }


    // Check every minute, but contact the backend only near token expiry.
    setInterval(keepSessionAlive, 60 * 1000);


    // Also refresh after returning to an already-open tab.
    global.addEventListener("focus", keepSessionAlive);

    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
            keepSessionAlive();
        }
    });


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

                store.refreshToken =
                    response.data.refresh_token;


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
                clearSession();

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
                    "/auth/face/register",
                    data
                );

            },


            login(data) {

                return post(
                    "/auth/face/login",
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