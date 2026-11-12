
const API_BASE_URL = "http://127.0.0.1:8000";

const token = localStorage.getItem("token");

if (!token) {
    window.location.href = "login.html";
}


// ==============================
// API HELPER
// ==============================

async function apiRequest(endpoint, method = "GET", body = null) {

    const options = {
        method: method,
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        }
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        options
    );

    const data = await response.json();

    if (response.status === 401) {

        localStorage.removeItem("token");
        localStorage.removeItem("user");

        alert("Session expired! Please login again.");

        window.location.href = "login.html";

        throw new Error("Unauthorized");
    }

    if (!response.ok) {
        throw new Error(data.detail || "Something went wrong!");
    }

    return data;
}


// ==============================
// APPLICATION ELEMENTS
// ==============================

const modal = document.getElementById("applicationModal");

const openForm = document.getElementById("openForm");
const sidebarAdd = document.getElementById("sidebarAdd");
const closeForm = document.getElementById("closeForm");
const cancelForm = document.getElementById("cancelForm");

const applicationForm = document.getElementById("applicationForm");
const applicationList = document.getElementById("applicationList");

let applications = [];


// ==============================
// LOAD APPLICATIONS
// ==============================

async function loadApplications() {

    try {

        applicationList.innerHTML = `
            <tr>
                <td colspan="5">Loading applications...</td>
            </tr>
        `;

        const data = await apiRequest("/applications");

        applications = data.applications.map(app => ({
            id: app.id,
            company: app.company,
            position: app.position,
            status: app.status,
            appliedDate: app.applied_date
        }));

        displayApplications();

    } catch (error) {

        if (error.message === "Unauthorized") return;

        console.error(error);

        applicationList.innerHTML = `
            <tr>
                <td colspan="5">Unable to load applications.</td>
            </tr>
        `;

        alert(error.message);
    }
}


// ==============================
// LOAD DASHBOARD STATISTICS
// ==============================

async function loadStatistics() {

    try {

        const data = await apiRequest("/applications/dashboard");

        document.getElementById("totalCount").textContent =
            data.total_applications;

        const stats = {};

        data.statistics.forEach(item => {
            stats[item.status] = item.count;
        });

        document.getElementById("appliedCount").textContent =
            stats["Applied"] || 0;

        document.getElementById("interviewCount").textContent =
            stats["Interview"] || 0;

        document.getElementById("offerCount").textContent =
            stats["Selected"] || 0;

    } catch (error) {

        if (error.message === "Unauthorized") return;

        console.error("Statistics error:", error);
    }
}


// ==============================
// OPEN AND CLOSE FORM
// ==============================

function showForm() {
    modal.style.display = "flex";
}

function hideForm() {
    modal.style.display = "none";
}

openForm.addEventListener("click", showForm);

sidebarAdd.addEventListener("click", function(event) {
    event.preventDefault();
    showForm();
});

closeForm.addEventListener("click", hideForm);
cancelForm.addEventListener("click", hideForm);


// ==============================
// ADD APPLICATION - POST API
// ==============================

applicationForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const company = document.getElementById("company").value.trim();
    const position = document.getElementById("position").value.trim();
    const status = document.getElementById("status").value;
    const appliedDate = document.getElementById("appliedDate").value;

    if (!company || !position || !appliedDate) {
        alert("Please fill all fields!");
        return;
    }

    const button = applicationForm.querySelector(
        'button[type="submit"]'
    );

    if (button) {
        button.disabled = true;
    }

    try {

        const applicationData = {
            company: company,
            position: position,
            status: status,
            applied_date: appliedDate
        };

        await apiRequest(
            "/applications",
            "POST",
            applicationData
        );

        alert("Application added successfully!");

        applicationForm.reset();
        hideForm();

        await loadApplications();
        await loadStatistics();

    } catch (error) {

        if (error.message !== "Unauthorized") {
            alert(error.message);
        }

    } finally {

        if (button) {
            button.disabled = false;
        }

    }

});


// ==============================
// DISPLAY APPLICATIONS
// ==============================

function displayApplications() {

    applicationList.innerHTML = "";

    if (applications.length === 0) {

        applicationList.innerHTML = `
            <tr>
                <td colspan="5">No applications yet.</td>
            </tr>
        `;

    }

    applications.forEach(function(app) {

        const row = document.createElement("tr");

        const companyCell = document.createElement("td");
        companyCell.textContent = app.company;

        const positionCell = document.createElement("td");
        positionCell.textContent = app.position;

        const statusCell = document.createElement("td");
        statusCell.textContent = app.status;

        const dateCell = document.createElement("td");
        dateCell.textContent = app.appliedDate || "-";

        const actionCell = document.createElement("td");

        const deleteButton = document.createElement("button");

        deleteButton.textContent = "Delete";
        deleteButton.className = "delete-btn";

        deleteButton.addEventListener("click", function() {
            deleteApplication(app.id);
        });

        actionCell.appendChild(deleteButton);

        row.append(
            companyCell,
            positionCell,
            statusCell,
            dateCell,
            actionCell
        );

        applicationList.appendChild(row);

    });

}


// ==============================
// DELETE APPLICATION - DELETE API
// ==============================

async function deleteApplication(id) {

    const confirmDelete = confirm(
        "Are you sure you want to delete this application?"
    );

    if (!confirmDelete) return;

    try {

        await apiRequest(
            `/applications/${id}`,
            "DELETE"
        );

        alert("Application deleted successfully!");

        await loadApplications();
        await loadStatistics();

    } catch (error) {

        if (error.message !== "Unauthorized") {
            alert(error.message);
        }

    }

}


// ==============================
// LOGOUT
// ==============================

const logoutButton = document.getElementById("logoutButton");

logoutButton.addEventListener("click", function() {

    const confirmLogout = confirm("Are you sure you want to logout?");

    if (confirmLogout) {

        localStorage.removeItem("token");
        localStorage.removeItem("user");

        sessionStorage.clear();

        window.location.href = "login.html";

    }

});


// ==============================
// SETTINGS
// ==============================

const settingsModal = document.getElementById("settingsModal");

const settingsButton = document.getElementById("settingsButton");
const closeSettings = document.getElementById("closeSettings");
const cancelSettings = document.getElementById("cancelSettings");

const settingsForm = document.getElementById("settingsForm");

const userName = document.getElementById("userName");
const userEmail = document.getElementById("userEmail");
const theme = document.getElementById("theme");


// OPEN SETTINGS

settingsButton.addEventListener("click", function(event) {

    event.preventDefault();

    const savedSettings = JSON.parse(
        localStorage.getItem("careerTrackSettings")
    ) || {};

    const user = JSON.parse(
        localStorage.getItem("user")
    ) || {};

    userName.value = savedSettings.name || user.name || "";
    userEmail.value = savedSettings.email || user.email || "";
    theme.value = savedSettings.theme || "light";

    settingsModal.style.display = "flex";

});


// CLOSE SETTINGS

function hideSettings() {
    settingsModal.style.display = "none";
}

closeSettings.addEventListener("click", hideSettings);
cancelSettings.addEventListener("click", hideSettings);


// SAVE SETTINGS

settingsForm.addEventListener("submit", function(event) {

    event.preventDefault();

    const settings = {
        name: userName.value.trim(),
        email: userEmail.value.trim(),
        theme: theme.value
    };

    localStorage.setItem(
        "careerTrackSettings",
        JSON.stringify(settings)
    );

    applyTheme(settings.theme);

    alert("Settings saved successfully!");

    hideSettings();

});


// APPLY THEME

function applyTheme(selectedTheme) {

    if (selectedTheme === "dark") {
        document.body.classList.add("dark-theme");
    } else {
        document.body.classList.remove("dark-theme");
    }

}


// LOAD SAVED THEME

const savedSettings = JSON.parse(
    localStorage.getItem("careerTrackSettings")
) || {};

applyTheme(savedSettings.theme || "light");


// ==============================
// INITIALIZE DASHBOARD
// ==============================

async function initializeDashboard() {

    await loadApplications();
    await loadStatistics();

}

initializeDashboard();
