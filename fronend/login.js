
const API_BASE_URL = "http://127.0.0.1:8000";

// Elements
const loginTab = document.getElementById("loginTab");
const registerTab = document.getElementById("registerTab");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

const message = document.getElementById("message");

// Switch to Login
loginTab.addEventListener("click", function () {
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");

    loginTab.classList.add("active");
    registerTab.classList.remove("active");

    message.textContent = "";
});

// Switch to Register
registerTab.addEventListener("click", function () {
    registerForm.classList.remove("hidden");
    loginForm.classList.add("hidden");

    registerTab.classList.add("active");
    loginTab.classList.remove("active");

    message.textContent = "";
});

// Show Message
function showMessage(text, type) {
    message.textContent = text;
    message.className = type;
}

// Login Function
loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    const button = loginForm.querySelector("button");

    button.disabled = true;
    button.textContent = "Logging in...";

    try {

        const response = await fetch(`${API_BASE_URL}/login`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed!");
        }

        // Save Token and User
        localStorage.setItem("token", data.access_token);

        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );

        showMessage("Login successful! Redirecting...", "success");

        setTimeout(function () {
            window.location.href = "index.html";
        }, 700);

    } catch (error) {

        showMessage(error.message, "error");

    } finally {

        button.disabled = false;
        button.textContent = "Login";

    }

});


// Register Function
registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;

    const button = registerForm.querySelector("button");

    button.disabled = true;
    button.textContent = "Creating account...";

    try {

        const response = await fetch(`${API_BASE_URL}/register`, {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                name: name,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed!");
        }

        showMessage(
            "Account created successfully! Please login.",
            "success"
        );

        registerForm.reset();

        // Switch to Login
        setTimeout(function () {

            loginTab.click();

            document.getElementById("loginEmail").value = email;

        }, 1000);

    } catch (error) {

        showMessage(error.message, "error");

    } finally {

        button.disabled = false;
        button.textContent = "Create Account";

    }

});
